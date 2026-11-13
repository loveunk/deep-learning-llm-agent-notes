"""Offline contract tests: deduplication, review preservation, failure handling."""

import argparse
import copy
import datetime as dt
import importlib.util
import io
import json
from contextlib import redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "collect_reading_candidates.py"
spec = importlib.util.spec_from_file_location("reading_candidates", SCRIPT)
reading = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reading)
NOW = dt.datetime(2026, 11, 13, 9, tzinfo=dt.timezone.utc)


def issue(number, title, body="", state="open", bot=True, comments=0):
    return {
        "number": number, "title": title, "body": body, "state": state,
        "user": {"login": "github-actions[bot]" if bot else "maintainer",
                 "type": "Bot" if bot else "User"},
        "comments": comments, "html_url": f"https://github.com/owner/repo/issues/{number}",
    }


class ReadingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / "reading"
        self.archive.mkdir()
        self.ledger = self.root / "status.json"
        self.ledger.write_text('{"version": 1, "entries": []}')
        self.sources = self.root / "sources.json"
        self.sources.write_text(json.dumps([{"name": "one", "feed_url": "https://feed.example/rss"}]))
        self.args = argparse.Namespace(
            sources=str(self.sources), since_days=7, timeout=1, workers=1,
            include_undated=False, min_score=1, max_per_source=2, max_items=12,
        )

    def test_tracking_removed_but_semantic_queries_and_routes_retained(self):
        self.assertEqual(reading.canonical_url("HTTPS://EXAMPLE.org/article?id=42&utm_source=rss&fbclid=x"),
                         "https://example.org/article?id=42")
        self.assertNotEqual(reading.canonical_url("https://example.org/article?id=42"),
                            reading.canonical_url("https://example.org/article?id=43"))
        self.assertEqual(reading.canonical_url("https://example.org/?q=a%2Bb&tag=x&tag=y#/doc"),
                         "https://example.org/?q=a%2Bb&tag=x&tag=y#/doc")
        self.assertEqual(reading.canonical_url("https://example.org/?ref=paper&source=code"),
                         "https://example.org/?ref=paper&source=code")
        with self.assertRaises(ValueError):
            reading.canonical_url("javascript:alert(1)")
        with self.assertRaises(ValueError):
            reading.canonical_url("https://user:secret@example.org/")

    def test_archive_ledger_and_open_closed_bot_history_are_deduplicated(self):
        month = self.archive / "2026"
        month.mkdir()
        (month / "06.md").write_text("- 链接：<https://example.org/selected?utm_medium=rss>\n")
        self.ledger.write_text(json.dumps({"version": 1, "entries": [
            {"url": f"https://example.org/{status}", "status": status}
            for status in reading.STATUSES]}))
        history = [
            issue(1, "Reading candidates 2026-06-01", "- Link: https://example.org/old?utm_source=rss", "closed"),
            issue(2, "Reading candidates 2026-W45", "- Link: https://example.org/pending-issue"),
            issue(3, "Reading candidates 2026-06-02", "- Link: https://example.org/human", bot=False),
            issue(4, "Unrelated issue", "- Link: https://example.org/unrelated"),
        ]
        snapshot = copy.deepcopy(history)
        links = reading.known_links(self.archive, self.ledger, history)
        self.assertTrue({"https://example.org/selected", "https://example.org/old",
                         "https://example.org/pending-issue"} <= links)
        self.assertTrue(all(f"https://example.org/{state}" in links for state in reading.STATUSES))
        self.assertNotIn("https://example.org/human", links)
        self.assertNotIn("https://example.org/unrelated", links)
        self.assertEqual(history, snapshot)

    def test_same_week_is_idempotent_even_after_closure_or_human_review(self):
        history = [issue(10, "Reading candidates 2026-W46", "My manual review must survive", "closed", False, 3)]
        snapshot = copy.deepcopy(history)
        result = reading.publication_decision([{"link": "https://example.org/new"}], history, NOW, True)
        self.assertFalse(result["should_create"])
        self.assertEqual(result["existing_issues"], [10])
        self.assertEqual(result["reason"], "existing_week")
        self.assertEqual(history, snapshot)
        self.assertTrue(reading.publication_decision([{}], history, NOW + dt.timedelta(days=7), True)["should_create"])

    def test_iso_week_year_and_no_candidate_or_history_never_publish(self):
        self.assertEqual(reading.week_key(dt.datetime(2021, 1, 1)), "2020-W53")
        self.assertFalse(reading.publication_decision([], [], NOW, True)["should_create"])
        self.assertFalse(reading.publication_decision([{}], [], NOW, False)["should_create"])

    def test_renamed_issue_still_blocks_republication_and_keeps_link_history(self):
        history = [issue(4, "Reviewed: keep for later", "# Reading candidates 2026-W46\n"
                         "<!-- reading-candidates:2026-W46 -->\n- Link: https://example.org/renamed", "closed")]
        self.assertFalse(reading.publication_decision([{}], history, NOW, True)["should_create"])
        self.assertIn("https://example.org/renamed", reading.known_links(self.archive, self.ledger, history))

    def test_history_accepts_pages_and_fails_closed_on_api_error(self):
        history = self.root / "history.json"
        history.write_text(json.dumps([[issue(1, "one")], [issue(2, "two")]]))
        self.assertEqual(len(reading.load_history(str(history))), 2)
        for malformed in ({"message": "API rate limit exceeded"}, [{"number": 1}], "invalid json"):
            history.write_text(json.dumps(malformed) if not isinstance(malformed, str) else malformed)
            with self.assertRaises(ValueError):
                reading.load_history(str(history))

    def test_invalid_status_and_missing_files_fail_closed(self):
        self.ledger.write_text('{"version": 1, "entries": [{"url": "https://example.org/", "status": "maybe"}]}')
        with self.assertRaises(ValueError):
            reading.known_links(self.archive, self.ledger, [])
        with redirect_stderr(io.StringIO()):
            result = reading.main(["--history", str(self.root / "missing.json"), "--require-history"])
        self.assertEqual(result, 1)

    def test_html_error_page_is_not_a_successful_empty_feed(self):
        with self.assertRaises(ValueError):
            reading.parse_entries(b"<html><body>Access denied</body></html>", {"name": "one"})
        self.assertEqual(reading.parse_entries(b"<rss><channel/></rss>", {"name": "one"}), [])

    def test_all_sources_fail_and_partial_failure_is_visible(self):
        with patch.object(reading, "fetch_feed", side_effect=OSError("network unavailable")):
            with self.assertRaisesRegex(RuntimeError, "All RSS sources failed"):
                reading.collect(self.args, set(), NOW)
        self.sources.write_text(json.dumps([{"name": "one"}, {"name": "two"}]))
        def fetch(source, timeout):
            if source["name"] == "one":
                return source, [], "- one: timeout"
            return source, [self.entry("https://example.org/new")], ""
        with patch.object(reading, "fetch_source_entries", side_effect=fetch):
            items, warnings = reading.collect(self.args, set(), NOW)
        self.assertEqual(len(items), 1)
        self.assertEqual(warnings, ["- one: timeout"])

    def entry(self, link, date=NOW):
        return {"source": "one", "title": "Agent evaluation", "link": link,
                "summary": "FEED EXCERPT MUST NOT BE PUBLISHED", "published": date, "weight": 1}

    def test_seen_removed_before_limits_and_query_distinctions_survive(self):
        entries = [self.entry("https://example.org/old?utm_source=rss"),
                   self.entry("https://example.org/item?id=1"),
                   self.entry("https://example.org/item?id=1&utm_source=feed"),
                   self.entry("https://example.org/item?id=2"),
                   self.entry("https://example.org/future", NOW + dt.timedelta(days=1)),
                   self.entry("https://example.org/expired", NOW - dt.timedelta(days=8))]
        with patch.object(reading, "fetch_source_entries", return_value=({"name": "one"}, entries, "")):
            items, warnings = reading.collect(self.args, {"https://example.org/old"}, NOW)
        self.assertEqual({x["canonical_url"] for x in items},
                         {"https://example.org/item?id=1", "https://example.org/item?id=2"})
        markdown = reading.render_markdown(items, warnings, self.args, NOW)
        self.assertNotIn("FEED EXCERPT", markdown)
        self.assertIn("pending", markdown)

    def test_cleanup_plan_preserves_review_and_never_contains_mutations(self):
        history = [issue(1, "Reading candidates 2026-06-01", "- Link: https://example.org/a"),
                   issue(2, "Reading candidates 2026-06-02", "- Link: https://example.org/a?utm_source=x\n- Link: https://example.org/b\nMaintainer: keep this", comments=2),
                   issue(3, "Reading candidates 2026-W46", "manual review", comments=4)]
        snapshot = copy.deepcopy(history)
        plan = reading.cleanup_plan(history)
        self.assertFalse(plan["automatic_mutations"])
        self.assertEqual(len(plan["issues"]), 2)
        second = plan["issues"][1]
        self.assertEqual(second["duplicates_with_earlier_issue"], {"https://example.org/a": 1})
        self.assertEqual(second["unique_links_to_preserve"], ["https://example.org/b"])
        self.assertEqual(second["comment_count"], 2)
        self.assertEqual(second["action"], "manual_review_only")
        self.assertEqual(history, snapshot)

    def test_cleanup_only_does_not_fetch_feeds(self):
        history = self.root / "history.json"
        output = self.root / "plan.json"
        history.write_text(json.dumps([issue(1, "Reading candidates 2026-06-01")]))
        with patch.object(reading, "fetch_feed", side_effect=AssertionError("must not fetch")):
            result = reading.main(["--history", str(history), "--status-file", str(self.ledger),
                                   "--reading-dir", str(self.archive), "--cleanup-only", "--cleanup-plan", str(output)])
        self.assertEqual(result, 0)
        self.assertFalse(json.loads(output.read_text())["automatic_mutations"])


if __name__ == "__main__":
    unittest.main()

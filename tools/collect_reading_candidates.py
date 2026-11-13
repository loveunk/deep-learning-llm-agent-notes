#!/usr/bin/env python3
"""Collect candidate AI reading links from curated RSS/Atom feeds.

The script intentionally produces a draft list instead of editing repository
content. A maintainer should still decide which links deserve curated summaries.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import email.utils
import hashlib
import html
import json
import re
import sys
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


KEYWORDS: dict[str, list[str]] = {
    "llm": [
        "llm",
        "large language model",
        "large language models",
        "language model",
        "foundation model",
        "gpt",
        "claude",
        "gemini",
        "deepseek",
        "qwen",
        "llama",
        "大模型",
        "语言模型",
        "基础模型",
        "通用模型",
    ],
    "agent": [
        "agent",
        "agents",
        "agentic",
        "tool use",
        "tools",
        "workflow",
        "workflows",
        "multi-agent",
        "mcp",
        "memory",
        "guardrail",
        "guardrails",
        "智能体",
        "代理",
        "工具调用",
        "函数调用",
        "多智能体",
        "记忆",
        "工作流",
        "护栏",
    ],
    "coding-agent": [
        "coding agent",
        "codex",
        "claude code",
        "software engineering",
        "developer",
        "code",
        "repository",
        "编程智能体",
        "代码智能体",
        "代码生成",
        "软件工程",
        "开发者",
        "仓库",
    ],
    "rag": [
        "rag",
        "retrieval",
        "retrieval-augmented",
        "embedding",
        "embeddings",
        "rerank",
        "context engineering",
        "检索增强",
        "检索",
        "向量",
        "嵌入",
        "重排",
        "上下文工程",
    ],
    "eval": [
        "eval",
        "evals",
        "evaluation",
        "benchmark",
        "observability",
        "tracing",
        "评测",
        "评估",
        "基准",
        "可观测",
        "观测",
        "追踪",
    ],
    "infra": [
        "inference",
        "serving",
        "deployment",
        "latency",
        "cost",
        "cache",
        "sandbox",
        "推理",
        "部署",
        "服务化",
        "延迟",
        "成本",
        "缓存",
        "沙箱",
        "工程化",
    ],
    "multimodal": [
        "multimodal",
        "vision",
        "video",
        "image",
        "document",
        "ocr",
        "多模态",
        "视觉",
        "视频",
        "图像",
        "文档",
        "语音",
    ],
    "safety": [
        "safety",
        "security",
        "control",
        "alignment",
        "risk",
        "安全",
        "对齐",
        "风险",
        "控制",
        "红队",
    ],
    "training": [
        "training",
        "fine-tuning",
        "finetuning",
        "post-training",
        "distillation",
        "rlhf",
        "lora",
        "训练",
        "微调",
        "后训练",
        "蒸馏",
    ],
}


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> dt.datetime | None:
    if not value:
        return None

    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except (TypeError, ValueError):
        pass

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except ValueError:
        pass

    for date_format in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(value, date_format)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return parsed.astimezone(dt.timezone.utc)
        except ValueError:
            continue

    return None


def parse_date_from_link(link: str) -> dt.datetime | None:
    match = re.search(r"/(20\d{2})/(\d{1,2})/(\d{1,2})(?:/|-)", link)
    if not match:
        return None

    try:
        year, month, day = (int(part) for part in match.groups())
        return dt.datetime(year, month, day, tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def children(node: ET.Element, name: str) -> list[ET.Element]:
    expected = name.lower()
    return [child for child in list(node) if local_name(child.tag) == expected]


def descendants(node: ET.Element, name: str) -> list[ET.Element]:
    expected = name.lower()
    return [child for child in node.iter() if child is not node and local_name(child.tag) == expected]


def element_text(node: ET.Element, names: list[str]) -> str:
    expected = {name.lower() for name in names}
    for child in list(node):
        if local_name(child.tag) in expected and child.text:
            return child.text.strip()
    return ""


def element_link(node: ET.Element, atom: bool) -> str:
    if atom:
        for found in children(node, "link"):
            href = found.attrib.get("href", "").strip()
            rel = found.attrib.get("rel", "alternate")
            if href and rel == "alternate":
                return href
        return ""

    link = element_text(node, ["link"])
    if link:
        return link
    guid = element_text(node, ["guid"])
    return guid if guid.startswith("http") else ""


def parse_entries(xml_bytes: bytes, source: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    root_name = local_name(root.tag)
    if root_name not in {"rss", "rdf", "feed"}:
        raise ValueError(f"Not an RSS/Atom feed: {root_name}")
    is_atom = root_name == "feed"
    entries: list[ET.Element]

    if is_atom:
        entries = children(root, "entry")
    else:
        channel = children(root, "channel")
        entries = children(channel[0], "item") if channel else children(root, "item")
        if not entries:
            entries = descendants(root, "item")

    parsed: list[dict[str, Any]] = []
    for item in entries:
        if is_atom:
            title = element_text(item, ["title"])
            summary = element_text(
                item,
                [
                    "summary",
                    "content",
                ],
            )
            date_text = element_text(
                item,
                [
                    "published",
                    "updated",
                ],
            )
        else:
            title = element_text(item, ["title"])
            summary = element_text(item, ["description", "encoded", "summary", "content"])
            date_text = element_text(item, ["pubDate", "published", "updated", "date"])

        link = element_link(item, is_atom)
        if not title or not link:
            continue
        published = parse_date(date_text) or parse_date_from_link(link)

        parsed.append(
            {
                "source": source["name"],
                "title": strip_html(title),
                "link": link,
                "summary": strip_html(summary),
                "published": published,
                "topics": source.get("topics", []),
                "weight": int(source.get("weight", 1)),
                "language": source.get("language", ""),
                "category": source.get("category", ""),
            }
        )

    return parsed


def fetch_feed(source: dict[str, Any], timeout: int) -> bytes:
    request = urllib.request.Request(
        source["feed_url"],
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AIReadingCandidates/1.0)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def keyword_matches(haystack: str, keyword: str) -> bool:
    keyword = keyword.lower()
    if keyword.isascii():
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        return re.search(pattern, haystack) is not None
    return keyword in haystack


def score_item(item: dict[str, Any]) -> tuple[int, list[str]]:
    summary = item.get("summary", "")
    haystack = f"{item['title']} {summary[:800]}".lower()
    matched_topics: list[str] = []
    score = item.get("weight", 1)

    for topic, keywords in KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword_matches(haystack, keyword))
        if hits:
            matched_topics.append(topic)
            score += min(hits, 3)

    return score, matched_topics


def is_excluded(item: dict[str, Any], source: dict[str, Any]) -> bool:
    exclude_keywords = source.get("exclude_keywords", [])
    if not exclude_keywords:
        return False

    summary = item.get("summary", "")
    haystack = f"{item['title']} {summary[:800]}".lower()
    return any(keyword_matches(haystack, keyword) for keyword in exclude_keywords)


def fetch_source_entries(source: dict[str, Any], timeout: int) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    try:
        feed = fetch_feed(source, timeout)
        entries = parse_entries(feed, source)
        return source, entries, ""
    except Exception as exc:  # noqa: BLE001 - keep scheduled collection resilient.
        return source, [], f"- {source['name']}: {type(exc).__name__}: {exc}"


TRACKING_PARAMS = {"fbclid", "gclid", "dclid", "msclkid", "mc_cid", "mc_eid"}
ISSUE_TITLE = re.compile(r"Reading candidates (?:\d{4}-\d{2}-\d{2}|\d{4}-W\d{2})$")
STATUSES = {"pending", "selected", "rejected", "deferred"}


def canonical_url(url: str) -> str:
    """Remove known tracking parameters; retain semantic queries and hash routes.

    Do not merge arbitrary query values, arXiv versions, http/https, or trailing
    path slashes: those can identify genuinely different resources.
    """
    parts = urllib.parse.urlsplit(html.unescape(url.strip()))
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"Expected an HTTP(S) article URL: {url!r}")
    if parts.username or parts.password or any(char.isspace() for char in url):
        raise ValueError("Article URLs cannot contain credentials or whitespace")
    query = []
    for field in parts.query.split("&"):
        key = urllib.parse.unquote_plus(field.split("=", 1)[0]).lower()
        if field and not key.startswith("utm_") and key not in TRACKING_PARAMS:
            query.append(field)
    return urllib.parse.urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", "&".join(query), parts.fragment)
    )


def article_links(text: str) -> set[str]:
    """Read article link fields, not incidental links in an author's review."""
    links = set()
    for match in re.finditer(r"(?m)^- (?:Link:|链接：)\s*<?(https?://[^\s>]+)", text):
        links.add(canonical_url(match.group(1)))
    return links


def load_history(path: str) -> list[dict[str, Any]]:
    """Accept a REST issue list or gh api --paginate --slurp output; fail closed."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Issue history must be a JSON list, not an API error object")
    issues = []
    for page in payload:
        entries = page if isinstance(page, list) else [page]
        for issue in entries:
            if not isinstance(issue, dict) or not {"number", "title", "user", "state", "body"} <= issue.keys():
                raise ValueError("Malformed issue history; refusing incomplete deduplication")
            if not isinstance(issue["user"], dict) or issue["state"] not in {"open", "closed"}:
                raise ValueError("Malformed issue author/state in history")
            issues.append(issue)
    return issues


def is_candidate_issue(issue: dict[str, Any]) -> bool:
    return (
        not issue.get("pull_request")
        and issue.get("user", {}).get("login") == "github-actions[bot]"
        and issue.get("user", {}).get("type") == "Bot"
        and bool(ISSUE_TITLE.fullmatch(issue.get("title", "")) or
                 re.match(r"^# Reading candidates (?:\d{4}-\d{2}-\d{2}|\d{4}-W\d{2})(?:\n|$)", issue.get("body") or "") or
                 re.search(r"<!-- reading-candidates:\d{4}-W\d{2} -->", issue.get("body") or ""))
    )


def known_links(reading_dir: Path, status_file: Path, history: list[dict[str, Any]]) -> set[str]:
    if not reading_dir.is_dir():
        raise ValueError(f"Missing reading archive: {reading_dir}")
    links = set()
    for path in reading_dir.glob("[0-9][0-9][0-9][0-9]/[0-9][0-9].md"):
        links.update(article_links(path.read_text(encoding="utf-8")))
    ledger = json.loads(status_file.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict) or ledger.get("version") != 1 or not isinstance(ledger.get("entries"), list):
        raise ValueError("Candidate status file must contain version=1 and entries=[]")
    for entry in ledger["entries"]:
        if not isinstance(entry, dict) or entry.get("status") not in STATUSES or not entry.get("url"):
            raise ValueError(f"Invalid candidate status entry: {entry!r}")
        links.add(canonical_url(entry["url"]))
    for issue in history:
        if is_candidate_issue(issue):
            links.update(article_links(issue.get("body") or ""))
    return links


def week_key(now: dt.datetime) -> str:
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def existing_week_issues(history: list[dict[str, Any]], week: str) -> list[int]:
    # Respect even a human-created issue with the exact reserved weekly title.
    return [issue["number"] for issue in history if not issue.get("pull_request") and (
        issue["title"] == f"Reading candidates {week}" or
        f"<!-- reading-candidates:{week} -->" in (issue.get("body") or "") or
        (issue.get("body") or "").startswith(f"# Reading candidates {week}\n"))]


def publication_decision(items: list[dict[str, Any]], history: list[dict[str, Any]],
                         now: dt.datetime, history_loaded: bool) -> dict[str, Any]:
    title = f"Reading candidates {week_key(now)}"
    existing = existing_week_issues(history, week_key(now))
    return {
        "title": title,
        "week": week_key(now),
        "candidate_count": len(items),
        "existing_issues": existing,
        "should_create": bool(items) and history_loaded and not existing,
        "reason": "existing_week" if existing else
                  "history_missing" if not history_loaded else
                  "new_candidates" if items else "no_new_candidates",
    }


def cleanup_plan(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce evidence for human review only; never close or edit an issue."""
    candidates = sorted((issue for issue in history if is_candidate_issue(issue)), key=lambda i: i["number"])
    first_seen: dict[str, int] = {}
    plans = []
    for issue in candidates:
        links = article_links(issue.get("body") or "")
        duplicates = {link: first_seen[link] for link in sorted(links) if link in first_seen}
        if re.fullmatch(r"Reading candidates \d{4}-\d{2}-\d{2}", issue["title"]) and issue["state"] == "open":
            plans.append({
                "number": issue["number"], "url": issue.get("html_url", ""),
                "title": issue["title"], "updated_at": issue.get("updated_at"),
                "body_sha256": hashlib.sha256((issue.get("body") or "").encode()).hexdigest(),
                "comment_count": issue.get("comments"), "article_count": len(links),
                "duplicates_with_earlier_issue": duplicates,
                "unique_links_to_preserve": sorted(links - duplicates.keys()),
                "action": "manual_review_only",
                "review_required": "Read current body and ALL comments; preserve decisions and unique links before considering closure. Zero comments does not prove an unedited body.",
            })
        for link in links:
            first_seen.setdefault(link, issue["number"])
    return {"version": 1, "automatic_mutations": False, "issues": plans}


def collect(args: argparse.Namespace, excluded: set[str], now: dt.datetime) -> tuple[list[dict[str, Any]], list[str]]:
    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    if not isinstance(sources, list) or not sources:
        raise ValueError("At least one RSS source is required")
    cutoff = now - dt.timedelta(days=args.since_days)
    candidates: list[dict[str, Any]] = []
    warnings: list[str] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        source_results = executor.map(lambda source: fetch_source_entries(source, args.timeout), sources)

        for source, entries, warning in source_results:
            if warning:
                warnings.append(warning)
                continue

            for item in entries:
                published = item.get("published")
                if not published and not args.include_undated:
                    continue
                if published and published < cutoff:
                    continue
                if published and published > now:
                    continue
                try:
                    item["canonical_url"] = canonical_url(item["link"])
                except ValueError:
                    continue
                if item["canonical_url"] in excluded:
                    continue
                if is_excluded(item, source):
                    continue

                score, matched_topics = score_item(item)
                min_score = max(args.min_score, int(source.get("min_score", args.min_score)))
                if score < min_score or not matched_topics:
                    continue

                item["score"] = score
                item["matched_topics"] = matched_topics
                candidates.append(item)

    if len(warnings) == len(sources):
        raise RuntimeError("All RSS sources failed; no candidate issue will be created.\n" + "\n".join(warnings))

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for item in sorted(
        candidates,
        key=lambda value: (value.get("score", 0), value.get("published") or dt.datetime.min.replace(tzinfo=dt.timezone.utc), value["canonical_url"]),
        reverse=True,
    ):
        link = item["canonical_url"]
        if link in seen:
            continue
        source = item["source"]
        if args.max_per_source > 0 and source_counts.get(source, 0) >= args.max_per_source:
            continue
        seen.add(link)
        source_counts[source] = source_counts.get(source, 0) + 1
        unique.append(item)
        if len(unique) >= args.max_items:
            break

    return unique, warnings


def safe_text(value: str) -> str:
    # Feed text is untrusted. Escape Markdown/HTML and prevent accidental mentions.
    value = html.escape(strip_html(value), quote=False).replace("@", "&#64;")
    return re.sub(r"([\\`*_\[\]])", r"\\\1", value)


def render_markdown(items: list[dict[str, Any]], warnings: list[str], args: argparse.Namespace,
                    now: dt.datetime) -> str:
    lines = [
        f"# Reading candidates {week_key(now)}",
        f"<!-- reading-candidates:{week_key(now)} -->",
        "",
        "自动收集的未评审候选链接；分数只用于初筛，不代表质量或推荐。",
        "人工核对原文后，再通过 PR 更新月度精选和 `reading/candidate-status.json`。",
        "本 issue 创建后不由自动化覆盖，正文与评论可用于保留人工评审。",
        "",
        f"- Collected at (UTC): {now.isoformat()}",
        f"- Window: last {args.since_days} days",
        f"- Max items: {args.max_items}",
        f"- Max per source: {args.max_per_source if args.max_per_source > 0 else 'unlimited'}",
        "",
    ]

    if warnings:
        lines.extend(["## Source warnings", ""])
        lines.extend(f"- {safe_text(warning.lstrip('- '))}" for warning in warnings)
        lines.append("")

    if not items:
        lines.extend(["## Candidates", "", "No matching candidates found."])
        return "\n".join(lines) + "\n"

    lines.extend(["## Candidates", ""])
    for index, item in enumerate(items, start=1):
        published = item.get("published")
        published_text = published.date().isoformat() if published else "unknown"
        lines.extend(
            [
                f"### {index}. {safe_text(item['title'])}",
                "",
                f"- Link: {item['link']}",
                f"- Source: {safe_text(item['source'])}",
                f"- Language: {safe_text(item.get('language') or 'unknown')}",
                f"- Published: {published_text}",
                f"- Matched topics: {', '.join(item.get('matched_topics', []))}",
                f"- Score: {item.get('score', 0)}",
                "- Status: pending（待人工评审）",
                "- 主线判断 / 可验证实验 / 取舍理由：待人工填写",
                "",
            ]
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sources", default="reading/sources.json")
    parser.add_argument("--since-days", type=int, default=7)
    parser.add_argument("--max-items", type=int, default=12)
    parser.add_argument("--max-per-source", type=int, default=2)
    parser.add_argument("--min-score", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--include-undated", action="store_true")
    parser.add_argument("--reading-dir", default="reading")
    parser.add_argument("--status-file", default="reading/candidate-status.json")
    parser.add_argument("--history", help="All open/closed GitHub issues from gh api --paginate --slurp")
    parser.add_argument("--require-history", action="store_true")
    parser.add_argument("--metadata-output", default="")
    parser.add_argument("--cleanup-plan", default="", help="Write a read-only historical daily-issue review plan")
    parser.add_argument("--cleanup-only", action="store_true", help="Generate review plan without fetching feeds")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    if any(getattr(args, key) <= 0 for key in ("since_days", "max_items", "timeout", "workers")) or args.max_per_source < 0:
        parser.error("days, max-items, timeout and workers must be positive; max-per-source must be nonnegative")
    if (args.require_history or args.cleanup_plan or args.cleanup_only) and not args.history:
        parser.error("--history is required for publication and historical review")
    if args.cleanup_only and not args.cleanup_plan:
        parser.error("--cleanup-only requires --cleanup-plan")

    try:
        history = load_history(args.history) if args.history else []
        excluded = known_links(Path(args.reading_dir), Path(args.status_file), history)
        if args.cleanup_plan:
            Path(args.cleanup_plan).write_text(json.dumps(cleanup_plan(history), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.cleanup_only:
            return 0
        now = dt.datetime.now(dt.timezone.utc)
        items, warnings = collect(args, excluded, now)
        markdown = render_markdown(items, warnings, args, now)
        metadata = publication_decision(items, history, now, bool(args.history))
        metadata["source_warnings"] = warnings
        if not args.history:
            print("Preview only: no GitHub history supplied; cross-period issue deduplication is unavailable.", file=sys.stderr)
        if args.metadata_output:
            Path(args.metadata_output).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Collection failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Exercise the pure Python functions printed in the learning notes.

No model downloads, credentials, third-party packages, or network calls are used.
"""

import ast
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_document_function(path, name):
    """Compile only the named function, not surrounding model/API examples."""
    document = (REPO_ROOT / path).read_text(encoding="utf-8")
    for block in re.findall(r"```python\n(.*?)```", document, re.DOTALL):
        for node in ast.parse(block).body:
            if isinstance(node, ast.FunctionDef) and node.name == name:
                namespace = {}
                module = ast.Module(body=[node], type_ignores=[])
                exec(compile(module, str(path), "exec"), namespace)
                return namespace[name]
    raise AssertionError(f"Function {name} not found in {path}")


class RetrievalMetricsTests(unittest.TestCase):
    def setUp(self):
        self.evaluate = load_document_function(
            "llm/rag-evaluation.md", "evaluate_retrieval"
        )

    def score(self, relevant, returned, k=5):
        return self.evaluate(
            [{"question": "test", "relevant_doc_ids": relevant}],
            lambda question, top_k: [{"doc_id": item} for item in returned],
            k=k,
        )

    def test_partial_coverage_differs_from_hit_rate(self):
        result = self.score(["a", "b"], ["a", "unrelated"], k=2)
        self.assertEqual(result["recall_at_2"], 0.5)
        self.assertEqual(result["hit_rate_at_2"], 1)
        self.assertEqual(result["mrr_at_2"], 1)

    def test_duplicates_do_not_inflate_coverage_or_compress_rank(self):
        result = self.score(["a", "b", "b"], ["x", "x", "a", "a"], k=4)
        self.assertEqual(result["recall_at_4"], 0.5)
        self.assertAlmostEqual(result["mrr_at_4"], 1 / 3)

    def test_cutoff_ignores_relevant_result_after_k(self):
        result = self.score(["a"], ["x", "y", "a"], k=2)
        self.assertEqual(result["hit_rate_at_2"], 0)
        self.assertEqual(result["recall_at_2"], 0)
        self.assertEqual(result["mrr_at_2"], 0)

    def test_empty_retrieval_is_a_miss(self):
        result = self.score(["a"], [], k=1)
        self.assertEqual(result["recall_at_1"], 0)
        self.assertEqual(result["mrr_at_1"], 0)

    def test_macro_average_and_unanswerable_questions(self):
        dataset = [
            {"question": "one", "relevant_doc_ids": ["a", "b"]},
            {"question": "two", "relevant_doc_ids": ["c"]},
            {"question": "unanswerable", "relevant_doc_ids": []},
        ]
        retrieved = {"one": [{"doc_id": "a"}], "two": []}
        result = self.evaluate(dataset, lambda q, top_k: retrieved[q], k=2)
        self.assertEqual(result["recall_at_2"], 0.25)
        self.assertEqual(result["hit_rate_at_2"], 0.5)
        self.assertEqual(result["mrr_at_2"], 0.5)
        self.assertEqual(result["evaluated_queries"], 2)
        self.assertEqual(result["skipped_queries"], 1)

    def test_empty_and_unanswerable_only_sets_are_rejected(self):
        for dataset in ([], [{"question": "q", "relevant_doc_ids": []}]):
            with self.subTest(dataset=dataset), self.assertRaises(ValueError):
                self.evaluate(dataset, lambda q, top_k: [])

    def test_invalid_k_is_rejected(self):
        for k in (0, -1, 1.5, True):
            with self.subTest(k=k), self.assertRaises(ValueError):
                self.score(["a"], ["a"], k=k)


class ChunkingTests(unittest.TestCase):
    def setUp(self):
        self.split_text = load_document_function(
            "llm/rag-from-scratch.md", "split_text"
        )

    def test_overlapping_chunks_cover_text_without_redundant_tail(self):
        self.assertEqual(self.split_text("abcdefg", 4, 1), ["abcd", "defg"])
        self.assertEqual(self.split_text("abcdef", 3, 0), ["abc", "def"])
        self.assertEqual(self.split_text("你好世界", 3, 1), ["你好世", "世界"])
        self.assertEqual(self.split_text("", 4, 1), [])

    def test_nonadvancing_and_invalid_parameters_are_rejected(self):
        for size, overlap in ((0, 0), (3, 3), (3, 4), (3, -1), (3.5, 1), (True, 0)):
            with self.subTest(size=size, overlap=overlap), self.assertRaises(ValueError):
                self.split_text("abc", size, overlap)


if __name__ == "__main__":
    unittest.main()

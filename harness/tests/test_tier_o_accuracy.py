"""Checks for paired denominators, incomplete data, and eligibility freezing."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import tier_o_accuracy as audit


class AccuracyAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.questions = [{"probe_id": p} for p in ("a", "b", "excluded")]
        self.eligibility = {p: {"probe_id": p, "eligible": p != "excluded",
            "reason_code": "eligible" if p != "excluded" else "missing_image",
            "reason": "test fixture", "key_concern": False} for p in ("a", "b", "excluded")}
        self.mapping, self.scores = [], []
        for c in audit.CONDITIONS:
            for pid in self.eligibility:
                for i in range(10):
                    aid = f"{c}-{pid}-{i}"
                    self.mapping.append({"answer_id": aid, "condition": c, "probe_id": pid})
                    if pid != "excluded":
                        correct = c == "C3" or (c == "C2" and i < 5)
                        self.scores.append({"answer_id": aid, "label": "correct" if correct else "incorrect", "reference_concern": False})
        audit.write(self.out / "scores.jsonl", self.scores)
        (self.out / "answers_config.json").write_text(json.dumps({"eligibility_sha256": audit.digest(self.eligibility)}))

    def analyze(self):
        with patch.object(audit, "OUT", self.out), patch.object(audit, "inputs", return_value=({}, self.questions, [], self.mapping)), patch.object(audit, "eligibility_rows", return_value=self.eligibility), patch("builtins.print"):
            audit.analyze()

    def test_exclusions_are_shared_and_differences_are_paired(self):
        self.analyze()
        results = json.loads((self.out / "results.json").read_text())
        self.assertEqual(results["scored_responses"], 100)
        self.assertEqual(results["excluded_responses"], 50)
        self.assertEqual(results["estimates"]["C3-C1"]["estimate"], 1)
        self.assertEqual(results["estimates"]["C3-C2"]["estimate"], .5)
        self.assertEqual(results["estimates"]["C3-C2"]["ci95"], [.5, .5])
        self.assertNotIn("C4", results["condition_counts"])

    def test_partial_scores_are_rejected(self):
        audit.write(self.out / "scores.jsonl", self.scores[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete/duplicate"):
            self.analyze()
        self.assertFalse((self.out / "results.json").exists())

    def test_post_scoring_eligibility_change_is_rejected(self):
        self.eligibility["excluded"]["reason"] = "changed"
        with self.assertRaisesRegex(ValueError, "eligibility changed"):
            self.analyze()

    def test_identical_stems_with_conflicting_eligibility_are_excluded(self):
        self.questions[0]["text"] = "Same question?"
        self.questions[2]["text"] = "Same question!"
        # Add another distinct eligible item so bootstrap has at least two.
        self.questions.append({"probe_id": "c", "text": "Another question"})
        self.eligibility["c"] = {**self.eligibility["b"], "probe_id": "c"}
        for c in audit.CONDITIONS:
            for i in range(10):
                aid = f"{c}-c-{i}"
                self.mapping.append({"answer_id": aid, "condition": c, "probe_id": "c"})
                self.scores.append({"answer_id": aid, "label": "correct", "reference_concern": False})
        audit.write(self.out / "scores.jsonl", self.scores)
        (self.out / "answers_config.json").write_text(json.dumps({"eligibility_sha256": audit.digest(self.eligibility)}))
        self.analyze()
        results = json.loads((self.out / "results.json").read_text())
        self.assertEqual(results["assessed_responses"], 150)
        self.assertEqual(results["scored_responses"], 100)
        self.assertEqual(results["assessed_then_excluded_responses"], 50)
        self.assertEqual(results["duplicate_eligibility_conflicts"], ["a", "excluded"])


if __name__ == "__main__":
    unittest.main()

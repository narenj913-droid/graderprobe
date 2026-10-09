from __future__ import annotations

import ast
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class Phase3TrialBundleTests(unittest.TestCase):
    def _assignment(self, path: Path, names: set[str]):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in names:
                        values[target.id] = ast.literal_eval(node.value)
        return values

    def test_deepeval_candidate_and_counterfactual_are_permutations(self):
        base = self._assignment(
            ROOT / 'corpus/external-trials/deepeval-3338/solution.py',
            {'EXPECTED', 'CALLED', 'THRESHOLD'},
        )
        alt = self._assignment(
            ROOT / 'corpus/external-trials/deepeval-3338/alternatives/reversed_expected.py',
            {'EXPECTED', 'CALLED', 'THRESHOLD'},
        )
        self.assertEqual(base['CALLED'], alt['CALLED'])
        self.assertEqual(base['THRESHOLD'], alt['THRESHOLD'])
        self.assertEqual(base['EXPECTED'], list(reversed(alt['EXPECTED'])))
        self.assertNotEqual(base['EXPECTED'], alt['EXPECTED'])

    def test_trial_tasks_have_required_schema_and_upstream_marker(self):
        for rel in [
            'corpus/external-trials/deepeval-3338/task.yaml',
            'corpus/external-trials/inspect-ai-4721/task.yaml',
        ]:
            data = yaml.safe_load((ROOT / rel).read_text(encoding='utf-8'))
            self.assertIn('description', data)
            self.assertIn('provenance', data)
            self.assertEqual(data['provenance']['reproduction_status'], 'upstream_trial_bundle')
            self.assertEqual(data['provenance']['external_validation_status'], 'pending_authorized_upstream_execution')

    def test_direct_trial_scripts_compile(self):
        for rel in [
            'scripts/external_trials/deepeval_3338_upstream.py',
            'scripts/external_trials/inspect_ai_4721_upstream.py',
        ]:
            compile((ROOT / rel).read_text(encoding='utf-8'), rel, 'exec')


if __name__ == '__main__':
    unittest.main()

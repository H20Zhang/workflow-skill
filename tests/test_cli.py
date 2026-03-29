from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    project_root: Path
    spec_path: Path
    actions_path: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.project_root = Path(__file__).resolve().parents[1]
        cls.spec_path = cls.project_root / 'examples' / 'research_workflow.txt'
        cls.actions_path = cls.project_root / 'examples' / 'research_workflow_actions.json'

    def _run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, '-m', 'fsm_agent', *args],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_validate_command(self) -> None:
        result = self._run_cli('validate', str(self.spec_path), '--json')
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['initial_state'], 'intake')
        self.assertEqual(payload['terminal_states'], ['done'])
        self.assertEqual(len(payload['states']), 4)

    def test_demo_command_runs_to_completion(self) -> None:
        result = self._run_cli(
            'demo',
            str(self.spec_path),
            '--final-goal',
            'Deliver a validated answer to the user',
            '--actions',
            str(self.actions_path),
            '--json',
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload['is_complete'])
        self.assertEqual(payload['current_state'], 'done')
        self.assertEqual(payload['goal_status'], 'complete')


if __name__ == '__main__':
    unittest.main()

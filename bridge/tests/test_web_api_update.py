from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from bridge.web_api import GITHUB_LATEST_RELEASE_URL, SonarDeckApiState


class UpdateAppTests(TestCase):
    def _make_state(self, root: Path) -> SonarDeckApiState:
        return SonarDeckApiState(config_path=str(root / 'config.json'))

    def test_update_app_uses_git_flow_inside_checkout(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.git').mkdir()
            state = self._make_state(root)
            calls: list[tuple[str, dict]] = []

            def fake_run(command: str, **kwargs):
                calls.append((command, kwargs))
                return subprocess.CompletedProcess(command, 0, stdout=f'{command}\n', stderr='')

            with patch('bridge.web_api.repo_root', return_value=root), patch('bridge.web_api.subprocess.run', side_effect=fake_run):
                result = state.update_app()

            self.assertEqual(result['mode'], 'git')
            self.assertIn('Dev checkout updated', result['message'])
            self.assertIsInstance(result['snapshot'], dict)
            self.assertEqual([command for command, _ in calls], ['git pull --ff-only', 'npm install --prefix ui'])
            for _, kwargs in calls:
                self.assertEqual(kwargs['cwd'], root)
                self.assertTrue(kwargs['shell'])
                self.assertEqual(kwargs['timeout'], 180)
                self.assertTrue(kwargs['capture_output'])
                self.assertTrue(kwargs['text'])

    def test_update_app_returns_release_download_page_outside_checkout(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self._make_state(root)

            with patch('bridge.web_api.repo_root', return_value=root), patch('bridge.web_api.subprocess.run') as run:
                result = state.update_app()

            run.assert_not_called()
            self.assertEqual(result['mode'], 'release')
            self.assertEqual(result['update_url'], GITHUB_LATEST_RELEASE_URL)
            self.assertIn('installer', result['message'])
            self.assertIn('run it again', result['message'])

from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


@override_settings(DEMO_MODE=False)
class ResetDemoGuardTests(TestCase):
    def test_refuses_to_run_without_demo_mode(self):
        with self.assertRaises(CommandError):
            call_command("reset_demo")


@override_settings(DEMO_MODE=True)
class ResetDemoRestoreTests(TestCase):
    @patch("common.management.commands.reset_demo.refresh_now_blocking")
    @patch("common.management.commands.reset_demo.subprocess.run")
    @patch("common.management.commands.reset_demo.call_command")
    def test_flushes_restores_and_refreshes_in_order(
        self, mock_call_command, mock_subprocess_run, mock_refresh
    ):
        call_order = []
        mock_call_command.side_effect = lambda *a, **k: call_order.append(
            ("call_command", a, k)
        )
        mock_subprocess_run.side_effect = lambda *a, **k: call_order.append(
            ("subprocess.run", a, k)
        )
        mock_refresh.side_effect = lambda *a, **k: call_order.append(
            ("refresh_now_blocking", a, k)
        )

        call_command("reset_demo")

        # flush() must run first (wipes data, keeps schema)
        self.assertEqual(call_order[0][0], "call_command")
        self.assertEqual(call_order[0][1], ("flush",))
        self.assertEqual(call_order[0][2], {"interactive": False})

        # pg_restore must run second, against the baked-in dump
        self.assertEqual(call_order[1][0], "subprocess.run")
        restore_cmd = call_order[1][1][0]
        self.assertIn("pg_restore", restore_cmd)
        self.assertIn("--data-only", restore_cmd)
        self.assertIn("--single-transaction", restore_cmd)
        self.assertIn("/app/fixtures_snapshot.dump", restore_cmd)

        # refresh_now_blocking(full_refresh=True) must run last, to rebuild
        # the unmanaged materialized-view tables flush()/restore never touch
        self.assertEqual(call_order[2][0], "refresh_now_blocking")
        self.assertEqual(call_order[2][2], {"full_refresh": True})

    @patch("common.management.commands.reset_demo.refresh_now_blocking")
    @patch("common.management.commands.reset_demo.subprocess.run")
    @patch("common.management.commands.reset_demo.call_command")
    def test_raises_if_pg_restore_fails(
        self, mock_call_command, mock_subprocess_run, mock_refresh
    ):
        import subprocess

        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["pg_restore"]
        )

        with self.assertRaises(subprocess.CalledProcessError):
            call_command("reset_demo")

        # a failed restore must NOT be papered over by still refreshing views
        mock_refresh.assert_not_called()

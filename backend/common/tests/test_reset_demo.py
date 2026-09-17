from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings


@override_settings(DEMO_MODE=False)
class ResetDemoGuardTests(TestCase):
    def test_refuses_to_run_without_demo_mode(self):
        with self.assertRaises(CommandError):
            call_command("reset_demo")


@override_settings(DEMO_MODE=True)
@patch("common.management.commands.reset_demo.os.path.exists", return_value=True)
class ResetDemoRestoreTests(TestCase):
    @patch("common.management.commands.reset_demo.refresh_now_blocking")
    @patch("common.management.commands.reset_demo.subprocess.run")
    @patch("common.management.commands.reset_demo.call_command")
    def test_flushes_restores_and_refreshes_in_order(
        self, mock_call_command, mock_subprocess_run, mock_refresh, mock_exists
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

        # the connection must be passed as discrete flags, never as a
        # password-bearing URL on the command line
        db = settings.DATABASES["default"]
        for flag, value in (
            ("--host", db["HOST"]),
            ("--port", str(db["PORT"])),
            ("--username", db["USER"]),
            ("--dbname", db["NAME"]),
        ):
            self.assertIn(flag, restore_cmd)
            self.assertEqual(restore_cmd[restore_cmd.index(flag) + 1], value)
        self.assertNotIn(settings.DATABASE_URL, restore_cmd)

        # the password travels through the environment instead
        restore_kwargs = call_order[1][2]
        self.assertEqual(restore_kwargs["env"]["PGPASSWORD"], db["PASSWORD"])

        # check=True is what turns a failed restore into an exception --
        # assert it explicitly, since the failure test below mocks the
        # exception in and so cannot detect its removal
        self.assertIs(restore_kwargs["check"], True)

        # refresh_now_blocking(full_refresh=True) must run last, to rebuild
        # the unmanaged materialized-view tables flush()/restore never touch
        self.assertEqual(call_order[2][0], "refresh_now_blocking")
        self.assertEqual(call_order[2][2], {"full_refresh": True})

    @patch("common.management.commands.reset_demo.refresh_now_blocking")
    @patch("common.management.commands.reset_demo.subprocess.run")
    @patch("common.management.commands.reset_demo.call_command")
    def test_raises_if_pg_restore_fails(
        self, mock_call_command, mock_subprocess_run, mock_refresh, mock_exists
    ):
        import subprocess

        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["pg_restore"]
        )

        with self.assertRaises(subprocess.CalledProcessError):
            call_command("reset_demo")

        # a failed restore must NOT be papered over by still refreshing views
        mock_refresh.assert_not_called()


@override_settings(DEMO_MODE=True)
class ResetDemoMissingDumpTests(TestCase):
    @patch("common.management.commands.reset_demo.refresh_now_blocking")
    @patch("common.management.commands.reset_demo.subprocess.run")
    @patch("common.management.commands.reset_demo.call_command")
    @patch("common.management.commands.reset_demo.os.path.exists", return_value=False)
    def test_refuses_to_flush_when_dump_is_missing(
        self, mock_exists, mock_call_command, mock_subprocess_run, mock_refresh
    ):
        with self.assertRaises(CommandError):
            call_command("reset_demo")

        # nothing destructive may have happened: no flush, no restore, no
        # refresh -- otherwise a missing snapshot empties the demo DB for good
        mock_call_command.assert_not_called()
        mock_subprocess_run.assert_not_called()
        mock_refresh.assert_not_called()

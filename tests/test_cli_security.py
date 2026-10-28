"""
Tests that exercise the real srd.cli module (not copies of its helpers):
shell-quoting of remote paths, SRD_DEST_MODE validation, SSH control-socket
location, and the configuration checks.
"""

import os
import shlex
import pytest

from srd import cli

NASTY = "/path/on/server/it's a \"test\"; $(touch pwned) `id`"


@pytest.fixture
def ssh_calls(monkeypatch):
    """Capture commands that would be sent to the server instead of running ssh."""
    calls = []

    def fake_run_ssh_command(command, timeout=0):
        calls.append(command)
        return "DIR_OK"

    monkeypatch.setattr(cli, "run_ssh_command", fake_run_ssh_command)
    return calls


class TestQuoting:
    def test_check_remote_path_quotes_path(self, ssh_calls):
        assert cli.check_remote_path(NASTY, "Source") is True
        assert shlex.quote(NASTY) in ssh_calls[0]
        # the raw, unquoted path must not appear outside the quoted form
        assert ssh_calls[0] == f"test -d {shlex.quote(NASTY)} && echo DIR_OK || echo DIR_MISSING"

    def test_remote_stats_quotes_path(self, ssh_calls):
        cli.get_remote_stats(NASTY)
        assert f"cd {shlex.quote(NASTY)} " in ssh_calls[0]

    def test_remote_dest_stats_quotes_path(self, ssh_calls):
        cli.get_remote_dest_stats(NASTY)
        assert f"cd {shlex.quote(NASTY)} " in ssh_calls[0]

    def test_stats_script_bash_test_has_spaces(self, ssh_calls):
        cli.get_remote_stats("/x")
        assert '[[ "$OSTYPE" == "darwin"* ]]' in ssh_calls[0]
        assert '[["$OSTYPE"' not in ssh_calls[0]


class TestDestMode:
    @pytest.mark.parametrize("mode", ["777", "775", "770", "2770", "0755"])
    def test_valid(self, mode):
        assert cli.validate_dest_mode(mode) == mode

    @pytest.mark.parametrize("mode", ["", "7", "77", "778", "u+rwx", "777; rm -rf /", "12345", "abc"])
    def test_invalid_exits(self, mode):
        with pytest.raises(SystemExit):
            cli.validate_dest_mode(mode)

    def test_default_is_777(self):
        # Long-standing behaviour is preserved unless SRD_DEST_MODE is set.
        if "SRD_DEST_MODE" not in os.environ:
            assert cli.DEST_MODE == "777"


class TestControlSocket:
    def test_socket_is_per_user_not_tmp(self):
        assert cli.CONTROL_SOCKET.startswith(os.path.expanduser("~"))
        assert not cli.CONTROL_SOCKET.startswith("/tmp")
        assert cli.CONTROL_SOCKET.endswith("srd_ctl_%h")

    def test_control_dir_created_private(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cli, "CONTROL_SOCKET", str(tmp_path / "newdir" / "srd_ctl_%h"))
        cli.ensure_control_dir()
        mode = (tmp_path / "newdir").stat().st_mode & 0o777
        assert mode & 0o077 == 0  # no group/other access


class TestConfigChecks:
    def test_remote_config_required(self, monkeypatch, capsys):
        monkeypatch.setattr(cli, "REMOTE_HOST_ALIAS", "YOUR_SERVER_HOSTNAME")
        monkeypatch.setattr(cli, "REMOTE_USER", "jsmith")
        with pytest.raises(SystemExit):
            cli.require_remote_config()
        assert "SRD_REMOTE_HOST" in capsys.readouterr().out

    def test_remote_config_ok(self, monkeypatch):
        monkeypatch.setattr(cli, "REMOTE_HOST_ALIAS", "server.example.edu")
        monkeypatch.setattr(cli, "REMOTE_USER", "jsmith")
        cli.require_remote_config()  # no exception

    def test_log_dir_unset_gives_message_not_traceback(self, monkeypatch, capsys):
        monkeypatch.setattr(cli, "LOG_DIR", "/path/to/your/srd_logs")
        with pytest.raises(SystemExit):
            cli.prepare_log_dir()
        assert "SRD_LOG_DIR" in capsys.readouterr().out

    def test_log_dir_unwritable_gives_message(self, monkeypatch, capsys, tmp_path):
        blocker = tmp_path / "file"
        blocker.write_text("x")
        monkeypatch.setattr(cli, "LOG_DIR", str(blocker / "sub"))
        with pytest.raises(SystemExit):
            cli.prepare_log_dir()
        assert "cannot create log directory" in capsys.readouterr().out

    def test_log_dir_created(self, monkeypatch, tmp_path):
        monkeypatch.setattr(cli, "LOG_DIR", str(tmp_path / "logs"))
        cli.prepare_log_dir()
        assert (tmp_path / "logs").is_dir()


class TestRemoteVerifyScript:
    """Run the server-side verification script locally (bash) against hostile filenames."""

    def test_nasty_filenames_verify_without_injection(self, tmp_path, monkeypatch):
        import hashlib
        import shutil
        import subprocess

        if not (shutil.which("bash") and shutil.which("md5sum")):
            pytest.skip("needs bash and md5sum (GNU coreutils)")

        dest = tmp_path / "dest dir's $HOME"
        dest.mkdir()
        names = ["plain.mov", "it's here.mov", "semi;colon.mov", "dollar$(touch PWNED).mov"]
        for n in names:
            data = n.encode()
            (dest / n).write_bytes(data)
            (dest / (n + ".md5")).write_text(f"{hashlib.md5(data).hexdigest()}  {n}\n")

        real_popen = subprocess.Popen

        def local_popen(cmd, **kw):
            # cmd is ['ssh', ..., verify_cmd]; run the script locally instead of over ssh
            return real_popen(["bash", "-c", cmd[-1]], **kw)

        monkeypatch.setattr(cli.subprocess, "Popen", local_popen)
        monkeypatch.setattr(cli, "REMOTE_HOST_ALIAS", "server.example.edu")
        monkeypatch.setattr(cli, "REMOTE_USER", "jsmith")

        manifest = set(names) | {n + ".md5" for n in names}
        stats = cli.verify_remote_integrity(manifest, str(tmp_path), str(dest), 100, 1.0, [])

        assert not (dest / "PWNED").exists()
        assert not (tmp_path / "PWNED").exists()
        assert not any(p.name == "PWNED" for p in tmp_path.rglob("*"))
        # every file verified, none reported as mismatched
        assert stats.verified_count == len(names)
        assert stats.checksum_mismatches == []

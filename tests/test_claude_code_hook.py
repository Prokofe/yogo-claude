"""The Claude Code hook signs each session separately, so parallel sessions
are arbitrated like any other producers instead of overwriting one file."""

import json
import pathlib
import subprocess

HOOK = pathlib.Path(__file__).resolve().parent.parent / "adapters" / "claude-code" / "hook"
SID = "0f3c9a1e-5b7d-4c2a-9e8f-123456789abc"


def run(state, payload, home):
    subprocess.run(["sh", str(HOOK), state], input=json.dumps(payload), text=True,
                   env={"YOGO_HOME": str(home), "PATH": "/usr/bin:/bin"}, check=True)


def sources(home):
    d = home / "sources"
    return {f.stem: json.loads(f.read_text())["state"] for f in d.glob("*.json")}


def test_each_session_gets_its_own_source(tmp_path):
    run("thinking", {"session_id": SID}, tmp_path)
    run("done", {"session_id": "a1b2c3d4-0000"}, tmp_path)
    assert sources(tmp_path) == {"claude-code-0f3c9a1e": "thinking",
                                 "claude-code-a1b2c3d4": "done"}


def test_idle_reminder_is_not_a_question(tmp_path):
    run("thinking", {"session_id": SID}, tmp_path)
    run("waiting", {"session_id": SID, "notification_type": "idle_prompt"}, tmp_path)
    assert sources(tmp_path) == {"claude-code-0f3c9a1e": "thinking"}
    run("waiting", {"session_id": SID, "notification_type": "permission_prompt"}, tmp_path)
    assert sources(tmp_path) == {"claude-code-0f3c9a1e": "waiting"}


def test_end_removes_the_session(tmp_path):
    run("done", {"session_id": SID}, tmp_path)
    run("end", {"session_id": SID}, tmp_path)
    assert sources(tmp_path) == {}


def test_without_a_session_id_it_falls_back_to_one_shared_source(tmp_path):
    run("tool", {}, tmp_path)
    assert sources(tmp_path) == {"claude-code": "tool"}

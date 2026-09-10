from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import minefield_companion as mc


class FakeCtx:
    def __init__(self):
        self.skills = []
        self.sections = []
        self.tools = {}
        self.hooks = {}

    def register_skill(self, name, path):
        self.skills.append((name, path))

    def register_system_prompt_section(self, *args, **kwargs):
        self.sections.append((args, kwargs))

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools[name] = (toolset, schema, handler)

    def register_hook(self, name, callback):
        self.hooks[name] = callback


def _ctx(tmp_path, monkeypatch):
    monkeypatch.setattr(mc, "DATA_ROOT", tmp_path / "minefield")
    monkeypatch.setattr(mc, "SESSIONS_ROOT", tmp_path / "minefield" / "sessions")
    mc._STATES.clear()
    ctx = FakeCtx()
    mc.register(ctx)
    return ctx


def test_relevance_router():
    assert mc._looks_relevant("vLLM Qwen NVFP4 decode drops to 8 tok/s")
    assert mc._looks_relevant("my GGUF tool calls are emitted as prose")
    assert not mc._looks_relevant("what should I make for dinner")


def test_public_redaction():
    text = (
        "Authorization: Bearer secret-token "
        "host=192.168.1.22 /home/victor/models "
        "github_pat_abcdefghijklmnopqrstuvwxyz123456"
    )
    redacted = mc.redact_text(text)
    assert "secret-token" not in redacted
    assert "192.168.1.22" not in redacted
    assert "/home/victor" not in redacted
    assert "github_pat_" not in redacted


def test_registers_skill_tools_and_hooks(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    assert ctx.skills[0][0] == "model-serving-minefield"
    assert "minefield_record_finding" in ctx.tools
    assert "minefield_get_draft" in ctx.tools
    for hook in (
        "pre_llm_call",
        "on_skill_lifecycle",
        "post_tool_call",
        "post_llm_call",
        "transform_llm_output",
        "pre_tool_call",
        "on_session_finalize",
    ):
        assert hook in ctx.hooks


def test_end_to_end_local_draft_and_confirmation(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    sid = "session:test"

    injected = ctx.hooks["pre_llm_call"](
        session_id=sid,
        user_message="vLLM tool calls became prose after a template change",
        conversation_history=[],
        is_first_turn=True,
        model="test-model",
        platform="cli",
    )
    assert "Minefield auto-route" in injected["context"]
    assert mc._state(sid)["active"]

    handler = ctx.tools["minefield_record_finding"][2]
    result = handler(
        {
            "disposition": "possible_new_trap",
            "title": "Parser silently drops tool calls",
            "category": "tools",
            "summary": "Observed tool calls becoming prose after a serving-path change.",
            "symptom": "Tool calls are described in prose.",
            "mechanism_status": "PROPOSED_NOT_PROVEN",
            "stack_build": "vLLM test build; exact revision recorded by caller",
            "check": "Compare raw wire response with parsed client response.",
            "refutation": "Raw wire response also lacks tool_calls.",
        },
        session_id=sid,
    )
    assert '"local_only": true' in result

    sdir = mc.SESSIONS_ROOT / mc._safe_session_id(sid)
    assert (sdir / "events.jsonl").exists()
    assert (sdir / "finding.json").exists()
    assert (sdir / "PR_DRAFT.md").exists()

    final = ctx.hooks["transform_llm_output"](
        "Diagnosis complete.", session_id=sid
    )
    assert "Submit it as a PR" in final
    assert "Nothing has been uploaded yet" in final

    approval = ctx.hooks["pre_llm_call"](
        session_id=sid,
        user_message="yes",
        conversation_history=[],
        is_first_turn=False,
        model="test-model",
        platform="cli",
    )
    assert "explicitly authorizes one contribution PR" in approval["context"]
    assert mc._state(sid)["pr_authorized"]


def test_pr_guard_requires_approval_without_chat_yes(tmp_path, monkeypatch):
    ctx = _ctx(tmp_path, monkeypatch)
    sid = "session:guard"
    mc._activate(sid, "test")
    decision = ctx.hooks["pre_tool_call"](
        tool_name="terminal",
        args={"command": "gh pr create -R Blackwellboy/model-serving-minefield"},
        task_id=sid,
        session_id=sid,
    )
    assert decision["action"] == "approve"

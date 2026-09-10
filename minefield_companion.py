"""Always-on Hermes companion for the Model Serving Minefield skill.

The plugin is deliberately local-first:
- it activates only for model-serving/inference/evaluation work,
- records redacted evidence under HERMES_HOME,
- prepares contribution metadata locally,
- never uploads anything itself,
- requires an explicit user confirmation before a PR workflow may proceed.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_NAME = "model-serving-minefield"
UPSTREAM_REPO = "Blackwellboy/model-serving-minefield"
SESSION_RETENTION_DAYS = 30
MAX_TEXT = 65536
MAX_TOOL_TEXT = 32768

ROOT = Path(__file__).resolve().parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()
DATA_ROOT = HERMES_HOME / "model-serving-minefield"
SESSIONS_ROOT = DATA_ROOT / "sessions"

_STATES: dict[str, dict[str, Any]] = {}

RELEVANCE_RE = re.compile(
    r"""(?ix)\b(
        model[-\s]?serv(?:e|ing)|inference|vllm|llama\.cpp|gguf|ollama|sglang|
        tensorrt[-\s]?llm|tgi|text-generation-inference|tabbyapi|exllama|
        lm\s*studio|transformers|openai[-\s]?compatible|quant(?:ization|ized)?|
        nvfp4|mxfp4|fp8|awq|gptq|exl[23]|mtp|speculative\s+decod(?:e|ing)|
        tokens?/s|tok/s|throughput|prefill|decode|kv\s*cache|context\s+window|
        chat\s+template|reasoning(?:_content)?|tool[-\s]?call|cuda|rocm|oom|
        tensor\s+parallel|pipeline\s+parallel|benchmark|eval(?:uation)?\s+harness
    )\b"""
)

YES_RE = re.compile(r"(?i)^\s*(yes|y|submit|submit it|open it|open the pr|create the pr|send it|go ahead|do it)\s*[.!]?\s*$")
NO_RE = re.compile(r"(?i)^\s*(no|n|don't|do not|skip|cancel|not now)\s*[.!]?\s*$")
REVIEW_RE = re.compile(r"(?i)^\s*(review|show me|show draft|preview|let me see it)\s*[.!]?\s*$")

SECRET_PATTERNS = [
    (re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s,;]+"), r"\1<REDACTED_SECRET>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"), "<REDACTED_HF_TOKEN>"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "<REDACTED_API_KEY>"),
    (
        re.compile(
            r"""(?ix)\b(api[_-]?key|token|secret|password|passwd|access[_-]?key)
                (\s*[:=]\s*)
                (["']?)[^\s,"';]+(\3)"""
        ),
        r"\1\2<REDACTED_SECRET>",
    ),
    (re.compile(r"(?i)https?://[^/\s:@]+:[^@\s/]+@"), "https://<REDACTED_CREDENTIALS>@"),
]

PUBLIC_PATTERNS = [
    (re.compile(r"\b10(?:\.\d{1,3}){3}\b"), "<PRIVATE_IP>"),
    (re.compile(r"\b192\.168(?:\.\d{1,3}){2}\b"), "<PRIVATE_IP>"),
    (re.compile(r"\b172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}\b"), "<PRIVATE_IP>"),
    (re.compile(r"(?i)\b(?:fd|fc)[0-9a-f:]{2,}\b"), "<PRIVATE_IPV6>"),
    (re.compile(r"(?i)\bfe80:[0-9a-f:%]+\b"), "<LINK_LOCAL_IPV6>"),
    (re.compile(r"(?i)\b::1\b"), "<LOOPBACK_IPV6>"),
    (re.compile(r"(?i)\blocalhost(?::\d{1,5})?\b"), "HOST:PORT"),
    (re.compile(r"(?i)\b[\w.-]+\.ts\.net(?::\d{1,5})?\b"), "<TAILNET_HOST>"),
    (re.compile(r"(?i)(?:/home|/Users)/[^/\s]+(?:/[^\s]*)?"), "<HOME_PATH>"),
    (re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+(?:\\[^\s]*)?"), "<HOME_PATH>"),
    (
        re.compile(
            r"""(?ix)\b
            (?!(?:http|https)\b)
            (?:[a-z0-9][a-z0-9-]*\.)*(?:lan|local|internal|corp|home)
            (?::\d{1,5})?\b"""
        ),
        "<PRIVATE_HOST>",
    ),
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_session_id(session_id: str | None) -> str:
    raw = session_id or "unknown"
    return re.sub(r"[^A-Za-z0-9_.-]", "_", raw)[:160]


def _ensure_dirs() -> None:
    SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(DATA_ROOT, 0o700)
        os.chmod(SESSIONS_ROOT, 0o700)
    except OSError:
        pass


def _cleanup_old_sessions() -> None:
    _ensure_dirs()
    cutoff = time.time() - SESSION_RETENTION_DAYS * 86400
    for path in SESSIONS_ROOT.iterdir():
        try:
            if path.is_dir() and path.stat().st_mtime < cutoff:
                for child in sorted(path.rglob("*"), reverse=True):
                    if child.is_file() or child.is_symlink():
                        child.unlink(missing_ok=True)
                    elif child.is_dir():
                        child.rmdir()
                path.rmdir()
        except OSError:
            continue


def redact_text(value: Any, *, public: bool = True, limit: int = MAX_TEXT) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):
            text = repr(value)
    else:
        text = str(value)

    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    if public:
        for pattern, replacement in PUBLIC_PATTERNS:
            text = pattern.sub(replacement, text)

    if len(text) > limit:
        text = text[:limit] + f"\n<TRUNCATED {len(text) - limit} CHARS>"
    return text


def _state(session_id: str | None) -> dict[str, Any]:
    sid = session_id or "unknown"
    if sid not in _STATES:
        _STATES[sid] = {
            "session_id": sid,
            "active": False,
            "activated_at": None,
            "activation_reason": None,
            "finding": None,
            "pr_ready": False,
            "pr_prompted": False,
            "pr_pending": False,
            "pr_authorized": False,
            "pr_submitted": False,
            "last_platform": None,
            "last_model": None,
        }
    return _STATES[sid]


def _session_dir(session_id: str | None) -> Path:
    _ensure_dirs()
    path = SESSIONS_ROOT / _safe_session_id(session_id)
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass
    return path


def _append_event(session_id: str | None, event: str, payload: dict[str, Any]) -> None:
    path = _session_dir(session_id) / "events.jsonl"
    record = {
        "ts": _utc_now(),
        "event": event,
        "session_id": session_id,
        **payload,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _activate(session_id: str | None, reason: str) -> dict[str, Any]:
    state = _state(session_id)
    if not state["active"]:
        state["active"] = True
        state["activated_at"] = _utc_now()
        state["activation_reason"] = reason
        _append_event(session_id, "minefield_activated", {"reason": reason})
    return state


def _looks_relevant(user_message: str) -> bool:
    return bool(RELEVANCE_RE.search(user_message or ""))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _render_draft(finding: dict[str, Any], session_id: str | None) -> str:
    def g(key: str, default: str = "") -> str:
        return redact_text(finding.get(key, default), public=True)

    trap_id = g("trap_id") or "new/provisional"
    title = g("title") or "Minefield contribution"
    return f"""# Minefield contribution draft

This draft was generated locally by the Hermes Model Serving Minefield companion.
**Nothing in this file has been uploaded.**

Target repository: `{UPSTREAM_REPO}`
Session: `{_safe_session_id(session_id)}`
Disposition: `{g("disposition")}`
Existing trap: `{trap_id}`
Suggested category: `{g("category") or "unknown"}`

## Proposed title

{title}

## Symptom

{g("symptom")}

## Mechanism status

{g("mechanism_status") or "UNRESOLVED"}

## Proposed mechanism

{g("mechanism")}

## Stacks and builds bitten

{g("stack_build")}

## The check

{g("check")}

## Refutation criterion

{g("refutation")}

## Conditional fix

{g("fix")}

## Evidence status

{g("evidence_status") or "contributor-measured, conditions as reported"}

## Evidence pointer

{g("evidence_pointer") or "LOCAL_REDACTED_SESSION_LOG - replace with public/runnable evidence before PR if required"}

## Attribution

{g("attribution") or "@vcruz305"}

## Summary

{g("summary")}

## Before submission

At submission time Hermes must re-read the current upstream `CONTRIBUTING.md`
and PR template, determine the current next free trap number, ensure the check is
runnable, add the README symptom row and any required model index update, and
run the upstream integrity checks. Never publish raw session logs automatically.
"""


def _store_finding(session_id: str | None, finding: dict[str, Any]) -> dict[str, str]:
    state = _activate(session_id, "contribution-worthy finding recorded")
    cleaned = {k: redact_text(v, public=True) for k, v in finding.items()}
    cleaned["recorded_at"] = _utc_now()
    cleaned["session_id"] = session_id
    cleaned["upstream_repo"] = UPSTREAM_REPO
    state["finding"] = cleaned
    state["pr_ready"] = True
    state["pr_pending"] = True
    state["pr_prompted"] = False
    state["pr_authorized"] = False

    sdir = _session_dir(session_id)
    finding_path = sdir / "finding.json"
    draft_path = sdir / "PR_DRAFT.md"
    _write_json(finding_path, cleaned)
    draft_path.write_text(_render_draft(cleaned, session_id), encoding="utf-8")
    try:
        os.chmod(draft_path, 0o600)
    except OSError:
        pass
    _append_event(session_id, "finding_recorded", {"finding_path": str(finding_path), "draft_path": str(draft_path)})
    return {"finding_path": str(finding_path), "draft_path": str(draft_path)}


def _is_target_pr_mutation(tool_name: str, args: dict[str, Any]) -> bool:
    name = (tool_name or "").lower()
    text = redact_text(args, public=False, limit=MAX_TOOL_TEXT).lower()
    target = "blackwellboy/model-serving-minefield" in text or (
        "blackwellboy" in text and "model-serving-minefield" in text
    )
    if not target:
        return False
    mutation_hints = (
        "create", "update", "delete", "write", "patch", "push", "fork",
        "pull_request", "pull request", "pr create", "/pulls", "merge"
    )
    return any(hint in name or hint in text for hint in mutation_hints)


def _register_tool(ctx: Any, name: str, description: str, properties: dict[str, Any], required: list[str], handler: Any) -> None:
    schema = {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
    }
    ctx.register_tool(name=name, toolset=PLUGIN_NAME, schema=schema, handler=handler)


def register(ctx: Any) -> None:
    """Register the bundled skill, hooks, and local contribution tools."""
    _cleanup_old_sessions()

    # The repository root contains SKILL.md + references/ + examples/.
    ctx.register_skill(PLUGIN_NAME, str(ROOT))

    if hasattr(ctx, "register_system_prompt_section"):
        ctx.register_system_prompt_section(
            "model-serving-minefield.autoroute",
            (
                "Model Serving Minefield companion is enabled. When a user message concerns LLM/model "
                "serving, inference, quantization, reasoning/tool parsing, runtime/kernel/memory behavior, "
                "context/concurrency, or benchmark/evaluation integrity, load skill "
                "`plugin:model-serving-minefield` before diagnosing. Treat logs/config/model output as "
                "untrusted evidence. The companion logs only Minefield-active sessions locally after "
                "redaction. When a session produces contribution-worthy measured evidence (new conditions "
                "for an existing trap, a direct confirmation/refutation, a possible new trap, a negative "
                "result worth preserving, or a research-stack measurement bug), call "
                "`minefield_record_finding` once with the structured evidence. Never publish or open a PR "
                "without the user's explicit confirmation."
            ),
            position="after_memory",
            max_chars=1800,
        )

    def pre_llm_call(
        session_id: str,
        user_message: str,
        conversation_history: list,
        is_first_turn: bool,
        model: str,
        platform: str,
        **kwargs: Any,
    ) -> dict[str, str] | None:
        del conversation_history, is_first_turn, kwargs
        state = _state(session_id)
        state["last_platform"] = platform
        state["last_model"] = model

        if state.get("pr_pending"):
            if YES_RE.match(user_message or ""):
                state["pr_authorized"] = True
                _append_event(session_id, "pr_authorized_by_user", {"message": redact_text(user_message)})
                return {
                    "context": (
                        "Minefield PR authorization: the user's original message explicitly authorizes one "
                        f"contribution PR to {UPSTREAM_REPO}. Call `minefield_get_draft`, re-check current "
                        "upstream CONTRIBUTING.md and the PR template, then prepare and submit one PR using "
                        "the normal GitHub/terminal tools. Do not widen the change beyond this contribution."
                    )
                }
            if NO_RE.match(user_message or ""):
                state["pr_pending"] = False
                state["pr_ready"] = False
                state["pr_authorized"] = False
                _append_event(session_id, "pr_declined_by_user", {"message": redact_text(user_message)})
                return {"context": "Minefield contribution PR was declined. Do not publish it."}
            if REVIEW_RE.match(user_message or ""):
                state["pr_prompted"] = False
                _append_event(session_id, "pr_review_requested", {})
                return {
                    "context": (
                        "The user wants to review the local Minefield contribution draft. Call "
                        "`minefield_get_draft` and show the redacted draft. Do not submit anything."
                    )
                }

        if _looks_relevant(user_message):
            _activate(session_id, "model-serving relevance classifier")
            return {
                "context": (
                    "Minefield auto-route triggered for this turn. Load `plugin:model-serving-minefield` "
                    "before diagnosing, preserve evidence status, and keep canonical traps separate from "
                    "possible/unverified leads."
                )
            }

        if state["active"]:
            return {
                "context": (
                    "Minefield remains active for this session. Continue using the skill's evidence and "
                    "mutation boundaries. If a contribution-worthy measured finding is established, record "
                    "it with `minefield_record_finding` before concluding."
                )
            }
        return None

    def on_skill_lifecycle(skill_name: str, session_id: str | None = None, **kwargs: Any) -> None:
        del kwargs
        if skill_name == PLUGIN_NAME or skill_name.endswith(f":{PLUGIN_NAME}"):
            _activate(session_id, "Hermes skill lifecycle")

    def post_tool_call(
        tool_name: str,
        args: dict,
        result: str,
        task_id: str = "",
        duration_ms: int = 0,
        session_id: str | None = None,
        status: str | None = None,
        **kwargs: Any,
    ) -> None:
        del kwargs
        sid = session_id or task_id or None
        state = _state(sid)
        if not state["active"]:
            return
        _append_event(
            sid,
            "tool_call",
            {
                "tool_name": tool_name,
                "args": redact_text(args, public=True, limit=MAX_TOOL_TEXT),
                "result": redact_text(result, public=True, limit=MAX_TOOL_TEXT),
                "duration_ms": duration_ms,
                "status": status,
            },
        )
        if state.get("pr_authorized") and _is_target_pr_mutation(tool_name, args):
            lowered = (tool_name + " " + redact_text(result, public=False, limit=4096)).lower()
            if "pull" in lowered and ("http" in lowered or "created" in lowered or "number" in lowered):
                state["pr_submitted"] = True
                state["pr_pending"] = False
                state["pr_authorized"] = False
                _append_event(sid, "pr_submission_observed", {"tool_name": tool_name})

    def post_llm_call(
        session_id: str,
        user_message: str,
        assistant_response: str,
        conversation_history: list,
        model: str,
        platform: str,
        **kwargs: Any,
    ) -> None:
        del conversation_history, kwargs
        state = _state(session_id)
        if not state["active"]:
            return
        _append_event(
            session_id,
            "turn",
            {
                "model": model,
                "platform": platform,
                "user_message": redact_text(user_message, public=True),
                "assistant_response": redact_text(assistant_response, public=True),
            },
        )

    def transform_llm_output(response_text: str, session_id: str | None = None, **kwargs: Any) -> str | None:
        del kwargs
        state = _state(session_id)
        if not state.get("pr_ready") or not state.get("pr_pending") or state.get("pr_prompted"):
            return None
        state["pr_prompted"] = True
        _append_event(session_id, "pr_confirmation_prompted", {})
        return (
            response_text.rstrip()
            + "\n\n---\n"
            + "Minefield captured a **redacted contribution draft locally** from this diagnostic session. "
              f"Submit it as a PR to `{UPSTREAM_REPO}`? Reply **yes**, **review**, or **no**. "
              "**Nothing has been uploaded yet.**"
        )

    def pre_tool_call(
        tool_name: str,
        args: dict,
        task_id: str = "",
        session_id: str | None = None,
        **kwargs: Any,
    ) -> dict[str, str] | None:
        del kwargs
        sid = session_id or task_id or None
        if not _is_target_pr_mutation(tool_name, args):
            return None
        state = _state(sid)
        if state.get("pr_authorized"):
            return None
        return {
            "action": "approve",
            "message": (
                f"This action may mutate or publish to {UPSTREAM_REPO}. "
                "Minefield has not observed an explicit user confirmation for this contribution PR."
            ),
            "rule_key": "model-serving-minefield:upstream-pr",
        }

    def on_session_finalize(session_id: str | None, platform: str, **kwargs: Any) -> None:
        state = _state(session_id)
        if state["active"]:
            _append_event(
                session_id,
                "session_finalize",
                {
                    "platform": platform,
                    "reason": redact_text(kwargs.get("reason", ""), public=True),
                    "pr_ready": state.get("pr_ready", False),
                    "pr_prompted": state.get("pr_prompted", False),
                    "pr_authorized": state.get("pr_authorized", False),
                    "pr_submitted": state.get("pr_submitted", False),
                },
            )

    def record_finding(params: dict[str, Any], **kwargs: Any) -> str:
        sid = kwargs.get("session_id") or kwargs.get("task_id")
        result = _store_finding(sid, params)
        return json.dumps(
            {
                "success": True,
                "local_only": True,
                "redacted": True,
                "target_repo": UPSTREAM_REPO,
                **result,
                "next_step": (
                    "Continue the diagnostic answer. The plugin will append an explicit PR confirmation "
                    "question to the final response. Do not submit before the user answers yes."
                ),
            },
            indent=2,
        )

    def get_draft(params: dict[str, Any], **kwargs: Any) -> str:
        del params
        sid = kwargs.get("session_id") or kwargs.get("task_id")
        state = _state(sid)
        sdir = _session_dir(sid)
        draft_path = sdir / "PR_DRAFT.md"
        finding_path = sdir / "finding.json"
        if not draft_path.exists():
            return json.dumps({"success": False, "error": "no contribution draft for this session"})
        return json.dumps(
            {
                "success": True,
                "authorized_for_submission": bool(state.get("pr_authorized")),
                "target_repo": UPSTREAM_REPO,
                "draft_path": str(draft_path),
                "finding_path": str(finding_path),
                "draft": draft_path.read_text(encoding="utf-8"),
                "submission_requirements": [
                    "re-read current upstream CONTRIBUTING.md and PR template",
                    "use current next free global trap number if proposing a new trap",
                    "add the trap file under the correct category",
                    "add/update README symptom row",
                    "update models/README.md when required",
                    "run current upstream integrity checks",
                    "never include raw private session logs",
                ],
            },
            indent=2,
        )

    _register_tool(
        ctx,
        "minefield_record_finding",
        (
            "Record a contribution-worthy Minefield finding locally after a diagnostic session establishes "
            "measured evidence. This never uploads anything. Use for direct confirmation/refutation, new "
            "conditions on an existing trap, a possible new trap, a valuable negative result, or a "
            "research-stack measurement bug."
        ),
        {
            "disposition": {
                "type": "string",
                "enum": [
                    "confirmed_existing_trap",
                    "refuted_existing_trap",
                    "existing_trap_new_conditions",
                    "possible_new_trap",
                    "negative_result",
                    "research_stack_bug",
                ],
            },
            "title": {"type": "string"},
            "category": {
                "type": "string",
                "enum": [
                    "template", "tools", "reasoning", "quantization", "routing",
                    "runtime", "memory", "evaluation", "versioning", "unknown",
                ],
            },
            "trap_id": {"type": "string"},
            "summary": {"type": "string"},
            "symptom": {"type": "string"},
            "mechanism_status": {"type": "string"},
            "mechanism": {"type": "string"},
            "stack_build": {"type": "string"},
            "check": {"type": "string"},
            "refutation": {"type": "string"},
            "fix": {"type": "string"},
            "evidence_status": {"type": "string"},
            "evidence_pointer": {"type": "string"},
            "attribution": {"type": "string"},
        },
        [
            "disposition", "title", "category", "summary", "symptom",
            "mechanism_status", "stack_build", "check", "refutation",
        ],
        record_finding,
    )

    _register_tool(
        ctx,
        "minefield_get_draft",
        (
            "Read the current session's local redacted Minefield contribution draft. Use when the user asks "
            "to review it or after the user explicitly authorizes submission. This tool never uploads."
        ),
        {},
        [],
        get_draft,
    )

    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_hook("on_skill_lifecycle", on_skill_lifecycle)
    ctx.register_hook("post_tool_call", post_tool_call)
    ctx.register_hook("post_llm_call", post_llm_call)
    ctx.register_hook("transform_llm_output", transform_llm_output)
    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_hook("on_session_finalize", on_session_finalize)

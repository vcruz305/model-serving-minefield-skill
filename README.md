# Model Serving Minefield — Hermes Skill + Always-On Companion

A Hermes-first diagnostic layer for LLM serving failures **before blaming the
model**, built around and attributed to
[`Blackwellboy/model-serving-minefield`](https://github.com/Blackwellboy/model-serving-minefield).

> **The model is innocent until the serving path is proven clean.**

The repository now ships two pieces together:

1. **The Minefield skill** — evidence-aware diagnosis, canonical-trap routing,
   Core-12 fast path, bounded probes, and research-stack integrity checks.
2. **The Minefield companion plugin** — automatic relevance routing, local
   redacted evidence logging, contribution-draft generation, and an explicit
   PR-confirmation flow.

## Recommended install: automatic mode

Install this repository as an enabled Hermes plugin:

```bash
hermes plugins install vcruz305/model-serving-minefield-skill --enable
```

Start a new Hermes session after installation.

The plugin registers the bundled `model-serving-minefield` skill itself, so
this is the preferred one-command install. You do **not** need a separate skill
install when using automatic mode.

Once enabled, the companion:

- injects a small always-on routing rule into Hermes;
- detects model-serving/inference/quantization/evaluation incidents;
- tells Hermes to load `plugin:model-serving-minefield` only when relevant;
- starts a local Minefield evidence log only after the session is relevant;
- records redacted Minefield turns and tool evidence;
- can generate a structured local contribution draft when the session produces
  contribution-worthy measured evidence;
- appends a final **yes / review / no** PR question;
- never uploads the log or draft automatically.

Hermes plugins are deliberately opt-in. Installing with `--enable` is what
allows the lifecycle hooks to load on the next session.

## What “automatic” means

A normal skill cannot execute code merely because it was installed. Hermes
loads skills when the agent decides they are relevant.

The companion plugin closes that gap with supported Hermes lifecycle APIs:

```text
new turn
   |
   v
pre_llm_call relevance router
   |
   +-- unrelated ----------> no Minefield logging
   |
   `-- serving/eval issue -> activate local session
                             -> load Minefield skill
                             -> diagnose
                             -> record redacted evidence
                             -> mark contribution-worthy finding
                             -> ask PR confirmation
```

This keeps Minefield effectively always-on for the work it is meant to catch
without paying the full skill/context cost in unrelated conversations.

See [`references/automatic-mode.md`](references/automatic-mode.md).

## PR contribution loop

The companion does **not** submit every diagnosis upstream.

A contribution draft is created only when Hermes determines that the session
has useful measured evidence such as:

- a direct confirmation of an existing trap;
- a direct refutation/negative result;
- an existing trap reproduced under meaningfully new conditions;
- a plausible new trap with a runnable confirm/refute check;
- a research-stack or measurement-integrity bug worth preserving.

When that happens, Hermes calls the local-only
`minefield_record_finding` tool. The plugin writes:

```text
$HERMES_HOME/model-serving-minefield/sessions/<session>/
  events.jsonl
  finding.json
  PR_DRAFT.md
```

The response then ends with:

```text
Minefield captured a redacted contribution draft locally.
Submit it as a PR to Blackwellboy/model-serving-minefield?
Reply yes, review, or no. Nothing has been uploaded yet.
```

- **review** — Hermes loads and shows the redacted draft.
- **no** — the draft stays local and publication is cancelled.
- **yes** — the original user message is recorded as authorization for one
  contribution PR. Hermes then re-checks the *current* upstream
  `CONTRIBUTING.md` and PR template before building the diff.

The plugin also places a `pre_tool_call` guard around apparent mutating actions
against `Blackwellboy/model-serving-minefield`. If Hermes tries to publish
without a captured explicit `yes`, the action is escalated to Hermes' normal
human-approval gate instead of silently proceeding.

## Privacy and logging

This repository is intended for public open-source contributions, so the
logger is intentionally conservative.

It automatically redacts common credentials plus public-PR hazards such as:

- bearer/API/GitHub/Hugging Face tokens;
- private RFC1918 addresses;
- tailnet/internal-style hosts;
- home-directory paths;
- localhost endpoints.

Logs remain local. The plugin does not transmit them, does not call GitHub, and
does not make network requests on its own.

Session logs are stored with private filesystem permissions where supported and
old Minefield session directories are pruned after 30 days.

**Never treat automatic redaction as proof that a draft is safe to publish.**
Hermes must review the public projection against the current upstream rules
before opening a PR.

## Skill-only fallback

If you do not want Python hooks or automatic local logging, install only the
skill:

```bash
hermes skills install https://raw.githubusercontent.com/vcruz305/model-serving-minefield-skill/main/SKILL.md
```

Then invoke it manually or let Hermes select it normally:

```text
/model-serving-minefield My Qwen model stopped reasoning after a few turns...
```

Skill-only mode keeps the diagnostic workflow but does not provide automatic
routing/logging/PR prompts.

## Diagnostic features

The skill adds:

- canonical-trap vs possible/unverified-lead separation;
- strict evidence-status preservation;
- hardware/build/checkpoint/topology applicability checks;
- confirmation **and** refutation criteria before fixes;
- bounded live-endpoint diagnostics;
- benchmark/research-stack integrity checks;
- mutation boundaries;
- lazy-load references so the full registry does not sit in context.

Current tree:

```text
plugin.yaml
__init__.py
minefield_companion.py
SKILL.md
references/
  automatic-mode.md
  diagnostic-contract.md
  core-traps.md
  operator-playbook.md
  source-map.md
examples/
  diagnosis-example.md
tests/
  test_companion.py
```

## Upstream evidence contract

This project deliberately follows the upstream contribution rules rather than
creating a competing evidence format.

For a full upstream trap PR, Hermes is instructed to re-read the current
upstream contribution docs at submission time and satisfy the current
requirements, including the canonical status vocabulary, exact stack/build and
model revision, runnable check, README symptom row, model-index update when
required, attribution, and public-data scrub.

The diagnostic skill itself remains pinned to this reviewed upstream revision
for reproducible routing:

```text
4040f43f2cdc06447ccff4492a7d035c07390c08
```

The **submission** path intentionally checks current upstream `main` instead of
blindly using the pin, because contribution requirements and the next free trap
number can change.

## Upstream CLI

For the deepest local workflow:

```bash
git clone https://github.com/Blackwellboy/model-serving-minefield.git
cd model-serving-minefield
python -m pip install .
```

Examples:

```bash
minefield guide "empty content at a token ceiling" --stack vllm
minefield quick --base-url http://HOST:PORT/v1 --json doctor.json
minefield bundle --no-write
python3 -m minefield evidence-preflight --packet packet.json
```

The live doctor is bounded/read-only, but endpoint contact should still be
explicitly authorized by the operator.

## Attribution

Canonical traps, evidence labels, Core selection, registry content, doctor
semantics, and much of the diagnostic methodology originate from
[`Blackwellboy/model-serving-minefield`](https://github.com/Blackwellboy/model-serving-minefield),
copyright 2026 Blackwellboy, MIT licensed.

This repository adapts and packages that work for Hermes and adds the automatic
routing, local evidence capture, contribution workflow, and Hermes-specific
ergonomics. See [LICENSE](LICENSE).

## Maintainer

Victor Cruz — [`@vcruz305`](https://github.com/vcruz305)

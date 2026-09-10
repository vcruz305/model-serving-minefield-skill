# Model Serving Minefield — Hermes Skill

A Hermes-first skill for diagnosing LLM serving failures **before blaming the
model**.

It turns the excellent
[`Blackwellboy/model-serving-minefield`](https://github.com/Blackwellboy/model-serving-minefield)
registry into a token-efficient Hermes workflow with:

- canonical-trap vs possible/unverified-lead separation;
- strict evidence-status preservation;
- hardware/build/checkpoint/topology applicability checks;
- confirmation **and** refutation criteria before fixes;
- bounded live-endpoint diagnostics;
- benchmark/research-stack integrity checks;
- mutation boundaries so diagnosis does not quietly become "restart random
  things until it works";
- lazy-load references so the whole registry does not have to sit in context.

> **The model is innocent until the serving path is proven clean.**

## Install in Hermes

Current Hermes releases support direct `SKILL.md` URL installation and can
pull explicitly linked support files under `references/`, `scripts/`,
`templates/`, `assets/`, and `examples/`.

Inspect first if you want to review it:

```bash
hermes skills inspect https://raw.githubusercontent.com/vcruz305/model-serving-minefield-skill/main/SKILL.md
```

Install:

```bash
hermes skills install https://raw.githubusercontent.com/vcruz305/model-serving-minefield-skill/main/SKILL.md
```

Then use it directly:

```text
/model-serving-minefield My Qwen model stopped reasoning after a few turns...
```

or simply describe a model-serving problem and let Hermes select the skill when
its description matches.

Installed skills normally become available to new sessions. If your Hermes
build supports immediate prompt-cache invalidation, use its `--now` option when
installing/updating if you need the skill in the current session.

## What gets loaded

`SKILL.md` is the operating procedure. Deeper material is split so Hermes can
load it only when needed:

```text
SKILL.md
references/
  diagnostic-contract.md
  core-traps.md
  operator-playbook.md
  source-map.md
examples/
  diagnosis-example.md
```

The skill pins the upstream Minefield registry at:

```text
4040f43f2cdc06447ccff4492a7d035c07390c08
```

That gives diagnoses a reproducible registry revision instead of silently
mixing whatever happens to be on `main` today.

## Why a separate repo?

Upstream already includes an agent/Hermes-oriented skill. This repository is
not pretending otherwise.

This version is intentionally focused on **Hermes distribution and operator
ergonomics**:

1. keep the top-level skill small enough to route efficiently;
2. exploit current Hermes multi-file direct installs;
3. keep source-of-truth data pinned upstream instead of forking 100k+ lines of
   registry content;
4. give Hermes an explicit escalation order from Core -> stack/model indexes ->
   canonical registry -> L-series leads;
5. make the evidence and mutation boundaries hard to accidentally blur.

If upstream and this skill disagree about a canonical trap, **upstream wins**.

## Upstream CLI

For the deepest local workflow, clone/install the upstream package and let the
skill interpret its output:

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

The canonical traps, evidence labels, Core selection, registry, doctor
semantics, and much of the diagnostic methodology originate from
[`Blackwellboy/model-serving-minefield`](https://github.com/Blackwellboy/model-serving-minefield),
copyright 2026 Blackwellboy and licensed under MIT.

This repository adapts and packages that work for Hermes and adds its own
routing/workflow material. See [LICENSE](LICENSE).

## Maintainer

Victor Cruz — [`@vcruz305`](https://github.com/vcruz305)

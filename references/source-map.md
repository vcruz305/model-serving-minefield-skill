# Pinned upstream source map

Source of truth:

- Repository: `Blackwellboy/model-serving-minefield`
- Pinned revision for this skill release:
  `4040f43f2cdc06447ccff4492a7d035c07390c08`
- License: MIT

Use the pinned revision for reproducible diagnosis. Mutable `main` may contain
newer traps or changed evidence and should be treated as a different registry
revision.

## High-value upstream paths

Repository root:

`https://github.com/Blackwellboy/model-serving-minefield/tree/4040f43f2cdc06447ccff4492a7d035c07390c08`

Agent start:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/AGENT_START_HERE.md`

Canonical registry:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/dist/MINEFIELD_REGISTRY.json`

Full offline agent bundle:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/dist/MINEFIELD_AGENT_BUNDLE.md`

Lite agent router:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/dist/MINEFIELD_AGENT_BUNDLE_LITE.md`

Core 12:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/CORE.md`

Model index:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/models/README.md`

Stack index:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/stacks/README.md`

Main README / symptom map:

`https://raw.githubusercontent.com/Blackwellboy/model-serving-minefield/4040f43f2cdc06447ccff4492a7d035c07390c08/README.md`

## Stack pages

Use these when the serving stack is known:

```text
stacks/vllm.md
stacks/llama-cpp.md
stacks/ollama.md
stacks/sglang.md
stacks/mlx.md
stacks/hf-transformers.md
stacks/tensorrt-llm.md
stacks/text-generation-inference.md
stacks/tabbyapi.md
stacks/lm-studio.md
stacks/text-generation-webui.md
```

Resolve them against the pinned repository revision.

## Playbooks

Useful upstream playbooks include:

```text
playbooks/before-you-publish-an-ab.md
playbooks/thinking-died-multi-turn.md
playbooks/porting-a-harness.md
playbooks/long-context-looks-broken.md
playbooks/reading-a-soak.md
playbooks/agentic-research-integrity.md
playbooks/minefield-repro-loop.md
```

Use the matching playbook when the user's task is a workflow rather than a
single symptom.

## Search strategy

When web/GitHub access exists:

1. search the canonical registry by distinctive symptom text;
2. inspect exact candidate trap entries;
3. compare structured applicability against the user's incident fingerprint;
4. preserve the candidate's published evidence status;
5. only then consider the separate L-series lead layer.

Do not use GitHub issue text, model cards, or third-party posts to silently
upgrade a canonical entry's evidence status.

## Freshness

This skill intentionally pins its canonical source map for reproducibility.
When checking for **new traps added after this skill release**, inspect upstream
`main` separately and clearly label that as a newer registry revision rather
than mixing revisions inside one diagnosis.

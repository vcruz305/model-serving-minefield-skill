# Automatic Mode

Automatic mode is provided by the companion Python plugin in this repository.
It uses supported Hermes lifecycle hooks rather than pretending a `SKILL.md`
file can execute itself.

## Install

```bash
hermes plugins install vcruz305/model-serving-minefield-skill --enable
```

The plugin registers the repository root as a bundled skill named
`plugin:model-serving-minefield`.

## Lifecycle

### 1. Lightweight routing

`pre_llm_call` checks only the current user message for model-serving and
evaluation concepts. On a match it marks the session Minefield-active and
injects a small instruction telling Hermes to load the bundled skill.

Unrelated conversations are not logged by this plugin.

### 2. Skill lifecycle

If Hermes loads the bundled Minefield skill through another route,
`on_skill_lifecycle` also marks that session active.

### 3. Local evidence capture

For active sessions only:

- `post_llm_call` stores a redacted user/assistant turn;
- `post_tool_call` stores bounded redacted tool arguments/results;
- `on_session_finalize` stores final session metadata.

The evidence log is JSONL under:

```text
$HERMES_HOME/model-serving-minefield/sessions/<session>/events.jsonl
```

Default `$HERMES_HOME` is `~/.hermes`.

### 4. Contribution candidate

The system-prompt section instructs Hermes to call
`minefield_record_finding` only when there is contribution-worthy measured
evidence.

That tool writes only local files:

```text
finding.json
PR_DRAFT.md
```

It does not use the network.

### 5. Confirmation

When a draft exists, `transform_llm_output` appends a yes/review/no confirmation
question to the agent's final response.

An exact affirmative user reply while a draft is pending authorizes one
contribution PR. A review request does not authorize publication. A negative
reply clears the pending publication state.

### 6. Publication guard

`pre_tool_call` checks apparent mutating actions aimed at
`Blackwellboy/model-serving-minefield`.

If no explicit affirmative reply has been observed for the pending draft, the
plugin returns Hermes' `approve` directive so the host human-approval gate
decides. The plugin does not auto-approve its own publication.

## Redaction boundary

The logger strips common credentials and public-repository hazards including
private addresses, tailnet/internal-style hosts, home paths, and localhost
endpoints.

This is defense in depth, not a publication guarantee. Before submission the
agent must inspect the current upstream contribution rules and the actual diff.

## Why PR construction is not hard-coded

The upstream registry assigns a global trap number, updates a symptom table,
may require a model-index change, and enforces an evolving integrity contract.
Hard-coding those details into a background hook would create stale or invalid
PRs.

Instead, the plugin captures the durable evidence and authorization state.
After the user says yes, Hermes uses its normal GitHub/terminal workflow to:

1. re-read current upstream `CONTRIBUTING.md`;
2. re-read the current PR template;
3. determine the current next free number;
4. build the minimal compliant diff;
5. run upstream integrity checks;
6. show/report the resulting PR.

This keeps automatic collection stable while letting the final publication
respect upstream's current rules.

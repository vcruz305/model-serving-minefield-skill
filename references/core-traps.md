# Core 12 quick router

These are the upstream project's twelve highest-yield canonical entries: traps
chosen because they have cost operators significant time and their symptoms
often masquerade as model behavior.

This file is a **router**, not the full registry. Preserve the exact upstream
evidence status when returning a candidate.

| ID | Symptom / trap | Upstream evidence | First discriminating check |
|---|---|---|---|
| 04 | Multi-turn reasoning collapses because prior reasoning is stripped from history | reproduced here | Render an actual multi-turn prompt with a unique marker in prior assistant reasoning and verify the marker survives |
| 01 | Reasoning firing rate reads 0% although the model visibly reasons | reproduced here | Inspect both runtime reasoning field variants and a positive-control response |
| 03 | Same model behaves differently because thinking defaults drift by revision/stack | reproduced here | Render the actual serving template and pin the checkpoint revision; send thinking control explicitly |
| 12 | HTTP 200 but empty/missing content at a token ceiling | reproduced here | Separate reasoning tokens, answer tokens, and cap behavior across controlled token budgets |
| 17 | A/B effect comes from each arm using different "recommended" sampling | reported by others; confound reproduced here | Re-run both arms under identical explicit sampling |
| 35 | Identical weights do not necessarily score identically | reproduced here | Establish repeatability/agreement floor before interpreting a small delta |
| 16 | `finish_reason` is treated as pass/fail and moves the score | reported by others and reproduced here | Re-score raw outputs without using finish reason as a correctness signal |
| 10 | Quant label says FP4/NVFP4/etc. but runtime takes a fallback kernel path | reproduced here | Verify a runtime tell for the actual kernel/path rather than trusting the checkpoint label |
| 19 | Model appears unable to tool-call because server template/parser flags are wrong | reported by others | Compare raw generated tool structure with the server's parsed OpenAI-compatible response |
| 53 | Config edit did not actually take effect | contributor-measured, conditions as reported | Verify the live process/launch/config state, not only the edited file or restart message |
| 61 | Advertised context window accepts the prompt but silently loses early context | reproduced here (arithmetic) and measured here, raw not published (curve) | Use unique early-context retrieval probes across increasing prompt lengths |
| 77 | Server validates one request field but silently accepts/ignores others | reproduced here | Paired control: intentionally misspell a parameter and require rejection; then verify behavior separately |

## High-value symptom aliases

### Reasoning / thinking

Start with 01, 03, 04, 12, 16, 20, 23, 29, 30, 63, 77 when the symptom is:

- "thinking stopped"
- "0% reasoning"
- multi-turn thinking collapse
- `reasoning_effort` appears ignored
- answer lands in reasoning channel
- empty content at high reasoning budgets
- "thinking off" lane still thinks

### Quantization / performance

Start with 10 and related quantization/runtime entries when:

- an FP4/NVFP4/MXFP4 label is unexpectedly slow
- accuracy collapses after a quantized upload
- kernel path changes across images/builds
- the same weights perform differently across serving images

### Tools

Start with 19 and adjacent tool/template entries when:

- model describes a tool call in prose
- raw generation contains a tool call but API response does not
- `tool_choice` is accepted but behavior does not change
- one stack tool-calls and another does not

### Evaluation / benchmark integrity

Start with 12, 16, 17, 35, 61 and the evaluation playbooks when:

- a score delta is suspiciously clean
- an A/B will not replicate
- cap-hit handling changes aggregate scores
- long-context results collapse silently
- model output looks fine but the scorer says otherwise

## Important

Do not report one of these as confirmed merely because the symptom text
matches. Use the conditions and confirmation/refutation logic from the full
pinned upstream entry.

Pinned upstream revision for this skill release:
`4040f43f2cdc06447ccff4492a7d035c07390c08`.

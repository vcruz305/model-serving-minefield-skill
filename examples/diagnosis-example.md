# Example diagnosis

User symptom:

> "My NVFP4 model is much slower than expected. The model name says NVFP4, so I
> assumed the fast FP4 kernels are active."

A strong Minefield-style response would look like this:

## Most likely canonical candidate

**Trap 10 — the quant label is not the kernel path**

Evidence status: preserve the exact upstream evidence status for the pinned
entry.

Diagnosis level: `POSSIBLE_RELATED_TRAP` until runtime evidence is collected.

Why it resembles the incident:

- The observed symptom is performance inconsistent with the advertised
  quantization format.
- The assumption being tested is exactly the dangerous one: checkpoint label
  -> runtime kernel path.
- No runtime tell has yet established which path the engine actually selected.

What is still unknown:

- exact checkpoint revision
- serving stack/build
- GPU architecture and device class
- runtime kernel/backend selection
- whether the slowdown is prefill, decode, or both

Fastest confirmation:

> Capture a runtime-supported indicator of the actual quantization/kernel path
> on this exact stack/build and compare it with a known fast control.

Refutation:

> If the runtime positively identifies the expected FP4 path and a matched
> control shows the same path, investigate another cause instead of retaining
> Trap 10 as the explanation.

Conditional mitigation:

> Only after confirming a fallback/mismatched path, change the relevant
> runtime/build/image/config variable one at a time and re-measure against the
> preserved baseline.

This example intentionally does **not** claim "Trap 10 is the root cause" from
the symptom alone.

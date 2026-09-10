# Changelog

## 1.1.0

- Add an enabled-plugin automatic mode for Hermes.
- Auto-route model-serving, inference, quantization, and evaluation incidents to the bundled Minefield skill.
- Capture redacted session and tool evidence locally only after Minefield activation.
- Add structured local contribution findings and PR drafts.
- Append a yes/review/no upstream PR confirmation question when a contribution-worthy finding exists.
- Guard apparent mutations to `Blackwellboy/model-serving-minefield` behind explicit user authorization or Hermes' human approval gate.
- Add offline tests for routing, redaction, hook/tool registration, contribution draft flow, and PR guard behavior.

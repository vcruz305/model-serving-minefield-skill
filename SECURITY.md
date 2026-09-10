# Security and privacy

The companion plugin is local-first and intentionally does not perform network requests or GitHub publication by itself.

Automatic Minefield logs may still contain sensitive diagnostic context despite redaction. Review `PR_DRAFT.md` and the final upstream diff before approving publication. Never submit credentials, private hostnames, internal paths, LAN/tailnet addresses, confidential prompts, or proprietary configuration to the public upstream repository.

If you discover a security issue in this plugin, report it privately to the repository maintainer rather than placing secrets or exploit details in a public issue.

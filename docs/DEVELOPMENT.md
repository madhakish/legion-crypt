# Fork development guide

This guide is for `madhakish/legion-crypt`. Upstream architecture remains in [CLAUDE.md](../CLAUDE.md); this file is the canonical fork-local validation and automation guidance. Use the checked-out source and [lib/legion/crypt/version.rb](../lib/legion/crypt/version.rb) for current behavior/version, rather than historical example counts.

Agent entrypoints: [AGENTS.md](../AGENTS.md) and the [review-legion-auth skill](../.agents/skills/review-legion-auth/SKILL.md).

## Change routing

- Trace JWT changes through `lib/legion/crypt/jwt.rb`, `jwks_client.rb`, and `spec/legion/{jwt,jwks_client}_spec.rb`. `verify_with_jwks` currently requires non-empty issuer and audience arguments. Header decoding is untrusted inspection, not authentication.
- External-key lookup occurs before issuer/audience option validation. Cover invalid options with stubbed lookup; do not assume rejecting a token makes no HTTP request.
- `cluster_secret.rb` uses one `cluster_secret_vault_path`, sets the secret before writing, and supports legacy option aliases. Test these contracts instead of repeating older resolved-defect notes.
- Use controlled clocks and client doubles for Vault leases, renewers and SPIFFE. Assert worker shutdown and failure behavior; never validate by rotating a real key or changing trust settings.

## Safe validation

The existing spec helper loads Legion settings. Use synthetic settings and test-only generated keys in a disposable environment without Vault, SPIRE, Kerberos credentials or user key files. Do not print token bodies or plaintext.

Python 3.9+ is sufficient for the read-only helper; it uses only the standard library:

```sh
python3 scripts/spec_plan.py lib/legion/crypt/jwt.rb
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Pass repository-relative changed paths to the planner. It returns existing spec candidates, cross-component review notes, unmapped files and stale curated patterns. It never loads Ruby or executes a test. Basename matching is conservative; inspect the result and add relevant integration coverage. It does not establish coverage or make the Ruby suite safe to run.

With Ruby >= 3.4 and dependencies provisioned in an approved disposable environment, inspect the spec helper, run the targeted specs, then `bundle exec rspec` and non-mutating `bundle exec rubocop`. Run `bundle check` before installing missing gems. Dependency installation may fetch packages and execute build hooks. If Ruby, dependencies or isolation are absent, report the blocked command; do not label static checks as passing RSpec. Autocorrection (`rubocop -A`) is an explicit code change, not a prerequisite to reading or reviewing this fork.

## GitHub Actions recommendations (not activated)

Prioritize JWT rejection matrix (issuer, audience, algorithm, missing kid, expiry), JWKS cache/rotation behavior and clean renewer shutdown with HTTP/clock doubles. Keep real Vault/PKI tests separate and explicitly approved.

The checked-in workflows do not verify an available self-hosted runner. Direct jobs in this family use `ubuntu-latest`; reusable jobs call `LegionIO/.github` workflows at mutable `@main`. The inspected upstream workflows use `${{ inputs.runner || 'ubuntu-latest' }}` and these callers do not supply `runner`, so they inherit GitHub-hosted defaults at the reviewed snapshot. Before implementing the requested self-hosted policy, inspect the reusable workflows and the registered runner inventory; choose only verified labels. Do not guess OS/architecture labels or silently fall back to GitHub-hosted runners.

Because this is a public repository, never run unreviewed pull-request code on a personal persistent runner. Prefer an isolated ephemeral runner with no host mounts, production network access or reusable credentials. If only the personal runner exists, keep proposed validation disabled until that isolation is established. A trusted manual dispatch must validate an exact maintainer-reviewed commit; do not use `pull_request_target` to check out and execute a PR head. Minimize token permissions, pin reviewed actions/reusable workflows to immutable SHAs, set timeouts/concurrency, and separate test artifacts from secrets. Release, publishing and infrastructure changes need their own approval. No workflow files are changed by this development overlay.

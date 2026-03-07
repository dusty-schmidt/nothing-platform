<!-- CANARY-30-SNIPPET-SMOKE-TEST -->
# Smoke Test — Prompt Stack Audit
Canary-tagged backups of all 23 prompt configuration files in the system prompt stack.
Each file backed up with a CANARY-XX tag for traceability across container rebuilds.
Manifest: /a0/usr/workdir/smoke-test-backup/manifest.json
Backups: /a0/usr/workdir/smoke-test-backup/*.bak
Purpose: auditable answer to "did we lose a prompt layer?" after any rebuild.

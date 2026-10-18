# Project instructions

## Versioning

- Use four numeric components for `VERSION` in `launcher/uncharted_launcher.py`: `<upstream major>.<upstream minor>.<upstream patch>.<fork revision>`.
- The first three components identify the upstream Supermedo/uncharted_pc release actually integrated into this fork. Check upstream releases before each update; do not advance that prefix just because a newer upstream release exists without integrating it.
- Current upstream base is `0.3.6` (tag `v0.3.6`, commit `b787c1068c3a9a9ba3ec43dd8086af2bf7d35c7d`); the first fork build on this base is `0.3.6.1`. Increase only the fourth component for each subsequent user-facing fork update, including local builds. The previous upstream base was `0.3.3`, last released as `0.3.3.8`.
- When adopting upstream `0.3.7`, `0.4.0`, or another release, match those first three components and restart the fork revision at `1` (for example `0.3.7.1` or `0.4.0.1`).
- Bump once per delivered update, not once per commit or rebuild of the same update.
- Treat the launcher constant as the source of truth. The Windows packaging script derives the ZIP filename and packaged `VERSION.txt` from it.
- Preserve ZIPs from previous versions. Do not publish a GitHub release unless the user requests one.

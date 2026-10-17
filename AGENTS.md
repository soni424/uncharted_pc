# Project instructions

## Versioning

- Increase the patch component of `VERSION` in `launcher/uncharted_launcher.py` for every user-facing update delivered to this user, including local builds.
- Bump once per delivered update, not once per commit or rebuild of the same update. Use a minor or major bump only when requested or justified by a larger change.
- Treat the launcher constant as the source of truth. The Windows packaging script derives the ZIP filename and packaged `VERSION.txt` from it.
- Preserve ZIPs from previous versions. Do not publish a GitHub release unless the user requests one.

# Jarvis Ultimate 0.2.6a — Test-Safe App Agent Hotfix

## Fixes

- Updates the legacy app/file ability test so it uses App Agent dry-run mode.
- Prevents the `open notepad` unit test from launching real Notepad during `python -m unittest discover -s tests -v`.
- Keeps the 0.2.6 app-agent reliability features unchanged.

## Notes

This is a small hotfix for the uncommitted 0.2.6 patch. It should be committed together with 0.2.6 once the full test suite passes.

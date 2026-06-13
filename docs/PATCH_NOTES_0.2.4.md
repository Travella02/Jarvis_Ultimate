# Jarvis Ultimate 0.2.4 — App Discovery Speed + Router Polish

## Added

- Background app-index warmup after voice warmup completes.
- Fast known-app resolution before deep Windows scanning.
- Snipping Tool aliases and fast launch candidates.
- Natural app-control phrasing such as “pull up,” “bring up,” and “can you open.”
- Ability-router fallback for unclear app-control phrases.
- Stronger purple thinking state in the Electron orb UI.

## Improved

- Built-in app aliases no longer have to wait for a deep scan when Jarvis already knows a safe launcher or common path.
- Real path candidates beat generic shell commands when scores tie.
- App closer ability is now registered in the ability system.
- App shell version is aligned to 0.2.4.

## Safety

- Background app indexing is disabled during tests.
- App launch/close dry-run guards remain active during unittest/pytest.
- No real apps should open during `python -m unittest discover -s tests -v`.

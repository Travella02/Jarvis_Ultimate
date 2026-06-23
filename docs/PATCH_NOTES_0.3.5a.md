# Patch Notes — Jarvis Ultimate 0.3.5a

## Sensitive Memory Vault Routing Foundation

This update adds the safe routing layer for future password-manager behavior.

### Added

- New `SecureVaultStore` foundation.
- Sensitive-memory classification for:
  - passwords,
  - passcodes/PIN-like phrases,
  - API keys,
  - access tokens,
  - recovery/backup codes,
  - seed phrases,
  - private keys,
  - Wi-Fi passwords,
  - account/routing/card-number style financial details.
- Secure vault status command.
- App-shell memory snapshot field for secure vault status.
- Config placeholders for future encrypted local vault storage.
- Tests proving sensitive explicit saves do not enter long-term, short-term, or entity memory.

### Changed

- Explicit sensitive save requests now route to secure-vault handling instead of normal memory.
- `financial` and `secrets` remain blocked from automatic memory.
- Jarvis now gives a clearer response: he cannot save the value in normal memory, and encrypted vault storage is not enabled yet.

### Not included yet

- Real encrypted password storage.
- Master password / Windows Hello / PIN unlock.
- Autofill.
- Password reveal/copy commands.
- Vault sync.

Those should be built later as a dedicated Secure Vault / Password Manager Agent.

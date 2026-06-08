# Jarvis 3 Architecture

```text
User Input → Jarvis Brain/Router → Agent Registry → Selected Agent → Agent Tools/Providers → Standard Result → Response Builder → User Response + UI Events
```

Core principles:
- Keep the brain separate from the UI.
- Keep agents specialized.
- Keep providers swappable.
- Keep tools deterministic whenever possible.
- Keep runtime behavior logged and testable.

# Development Rules

For every Jarvis patch/update/fix package:
- Include patch notes.
- Include a user-facing testing guide.
- Prefer downloadable replacement/patch files over code pasted in chat.
- Run the full test suite before delivery when the codebase is available: `python -m unittest discover -s tests -v`
- Keep Jarvis modular: brain, agents, tools, providers, memory, UI.
- Do not let UI code become the brain.
- Do not let one agent control everything.
- Keep providers swappable through config.

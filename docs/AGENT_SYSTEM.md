# Agent System

Every agent should follow this structure:

```text
agents/example_agent/
  agent.py
  manifest.py
  models.py
  prompts.py
  tools/
```

The manifest explains agent name, description, supported intents, permissions required, tools owned by the agent, and whether the agent is enabled.

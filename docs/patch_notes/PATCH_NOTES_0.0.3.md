# Jarvis Ultimate 0.0.3 — LM Studio Conversation Provider

## Summary

This update reconnects Jarvis to a real local LLM conversation path through LM Studio while keeping the new modular architecture intact.

## Added

- LM Studio LLM provider using the OpenAI-compatible local API.
- LLM provider response model.
- LLM provider factory.
- Mock LLM provider upgrades for stable tests.
- Conversation Agent now uses the configured LLM provider for normal chat.
- Runtime now creates and passes the LLM provider into the router.
- Router now passes the provider to agents through context.
- Provider config placeholders in `config/providers.yaml`.
- `.env.example` settings for LM Studio.
- Tests for LM Studio request shape, mock provider behavior, and conversation routing.

## Behavior change

In 0.0.2, normal chat was hardcoded. In 0.0.3, normal chat routes through the Conversation Agent and then through the configured LLM provider.

## LM Studio default

Default base URL:

```text
http://localhost:1234/v1
```

Default model setting:

```text
auto
```

`auto` means Jarvis will ask LM Studio for loaded models and use the first model returned. You can replace this with a specific model id later.

## Current limitations

- No long-term conversation memory yet.
- No streaming token output yet.
- No tool-calling through the LLM yet.
- If LM Studio is not running, Jarvis will return a clear provider error instead of pretending it answered.

## Next recommended update

`0.0.4 — Short-Term Conversation Memory + Cleaner Chat Loop`

"""Simple hybrid-ready intent classifier.

This milestone uses deterministic rules only. Later, the LLM provider can assist
with intent selection while these rules remain as guardrails/triggers.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IntentResult:
    intent: str
    confidence: float
    reason: str


class IntentClassifier:
    def classify(self, command: str) -> IntentResult:
        text = command.strip().lower()
        if not text:
            return IntentResult("empty", 1.0, "No input was provided.")

        if any(phrase in text for phrase in ["list agents", "what agents", "available agents", "show agents"]):
            return IntentResult("list_agents", 0.95, "Agent listing phrase detected.")

        if text in {"status", "system status", "jarvis status"} or "are you online" in text:
            return IntentResult("status", 0.95, "Status phrase detected.")

        relationship_phrases = (
            "related to me",
            "relationship to me",
            "what relationships",
            "list relationships",
            "show relationships",
            "relationship memory",
            "relationship graph",
            "connected to",
            "who works on",
            "works on jarvis",
            "who is my",
            "who are my",
            "what pets do i have",
            "which pets do i have",
            "what dogs do i have",
            "which dogs do i have",
        )
        if any(phrase in text for phrase in relationship_phrases):
            return IntentResult("memory_search", 0.88, "Relationship memory phrase detected.")

        entity_edit_type_words = ("same person", "same people", "same dog", "same cat", "same pet", "same project", "same app", "same device", "same vehicle", "same car", "same organization")
        if any(phrase in text for phrase in entity_edit_type_words):
            return IntentResult("memory_write", 0.92, "Entity merge/correction phrase detected.")
        if text.startswith(("rename ", "change ")) and " to " in text:
            return IntentResult("memory_write", 0.84, "Entity rename phrase detected.")
        if " as an alias for " in text or " as alias for " in text or " is an alias for " in text or " is another name for " in text:
            return IntentResult("memory_write", 0.86, "Entity alias phrase detected.")
        if text.startswith(("forget the alias ", "remove the alias ", "delete the alias ")) and "keep" in text:
            return IntentResult("memory_write", 0.9, "Entity alias removal phrase detected.")
        if text.startswith("call ") and " app" not in text and " tool" not in text and " program" not in text:
            return IntentResult("memory_write", 0.72, "Entity nickname phrase detected.")

        sensitive_vault_phrases = (
            "secure vault",
            "password vault",
            "password manager",
            "save my password",
            "store my password",
            "remember my password",
            "save this password",
            "store this password",
            "save my api key",
            "store my api key",
            "remember my api key",
            "save my recovery code",
            "store my recovery code",
            "remember my recovery code",
            "save my account number",
            "store my account number",
        )
        if any(phrase in text for phrase in sensitive_vault_phrases):
            if any(phrase in text for phrase in ["status", "show", "what is"]):
                return IntentResult("memory_search", 0.9, "Secure vault status/search phrase detected.")
            return IntentResult("memory_write", 0.92, "Sensitive secure-vault phrase detected.")

        memory_preference_phrases = (
            "memory preferences",
            "memory settings",
            "remember project rules automatically",
            "remember app settings automatically",
            "remember game settings automatically",
            "ask me before remembering",
            "ask before remembering",
            "ask me before saving",
            "never remember",
            "do not remember",
            "don't remember",
            "dont remember",
            "temporary memory",
            "short term memory",
            "short-term memory",
        )
        if any(phrase in text for phrase in memory_preference_phrases):
            if any(phrase in text for phrase in ["show", "what are", "how are"]):
                return IntentResult("memory_search", 0.9, "Memory preference status phrase detected.")
            return IntentResult("memory_write", 0.9, "Memory preference control phrase detected.")

        app_prefixes = ["open ", "launch ", "start app ", "start ", "run ", "open website ", "open site ", "close ", "quit ", "exit ", "switch to ", "focus ", "show "]
        app_phrases = [
            "pull up",
            "bring up",
            "open up",
            "can you open",
            "could you open",
            "can you launch",
            "could you launch",
            "can you close",
            "could you close",
            "close out of",
            "when i say",
            "call this app",
            "remember this app",
            "what app aliases",
            "what aliases",
            "list aliases",
            "show aliases",
            "forget the alias",
            "forget the name",
            "forget the nickname",
            "remove the alias",
            "remove the name",
            "remove the nickname",
            "delete the app name",
            "stop using",
            "don't call",
            "dont call",
            "use ",
            " as my main browser",
            " as my default browser",
            " as my browser",
            " as my music app",
            " as my editor",
        ]
        if any(text.startswith(prefix) for prefix in app_prefixes) or any(phrase in text for phrase in app_phrases):
            if "when i say" in text and any(phrase in text for phrase in [" open ", " launch ", " start ", " run "]):
                return IntentResult("app_control", 0.92, "App alias teaching phrase detected.")
            if any(phrase in text for phrase in ["alias", "nickname", "app name", "when i say", " as my ", "default browser", "main browser"]):
                return IntentResult("app_control", 0.9, "App alias/default-role phrase detected.")
            return IntentResult("app_control", 0.85, "App control trigger detected.")

        if any(phrase in text for phrase in ["screen", "read this", "look at this", "what does this say", "what am i looking at"]):
            return IntentResult("screen_question", 0.8, "Screen awareness phrase detected.")

        if any(phrase in text for phrase in ["change your voice", "use a different voice", "voice", "tts", "speak like"]):
            return IntentResult("voice_control", 0.75, "Voice phrase detected.")

        if any(phrase in text for phrase in ["avatar", "body", "character", "change how you look", "visual"]):
            return IntentResult("avatar_control", 0.75, "Avatar/body phrase detected.")

        # Explicit forget commands must route to the Memory Agent before the
        # conversation fallback sees relevant context and merely *claims* it forgot.
        # This catches natural commands like "Forget Scout." where the older
        # phrase list only matched "forget that" or "forget memory".
        memory_forget_prefixes = (
            "forget ",
            "remove remembered ",
            "remove memory ",
            "delete memory ",
            "stop remembering ",
            "do not remember ",
            "don't remember ",
            "dont remember ",
        )
        if text.startswith(memory_forget_prefixes):
            return IntentResult("memory_write", 0.9, "Explicit memory/entity forget command detected.")

        memory_phrases = [
            "remember",
            "save this",
            "save that",
            "store this",
            "store that",
            "make a note",
            "note that",
            "memory",
            "memories",
            "what do you remember",
            "what memories",
            "list memories",
            "show memories",
            "search memory",
            "search memories",
            "forget that",
            "forget memory",
            "forget memories",
            "memory candidate",
            "memory candidates",
            "waiting for review",
            "what did you learn recently",
            "what have you learned recently",
            "approve that",
            "approve memory",
            "save that permanently",
            "promote that",
            "reject that",
            "forget that candidate",
            "entity memory",
            "structured memory",
            "remembered entities",
            "what entities",
            "who is",
            "what do you know about",
        ]
        if any(phrase in text for phrase in memory_phrases):
            if any(phrase in text for phrase in ["what do you remember", "what memories", "list memories", "show memories", "search memory", "search memories", "memory candidates", "waiting for review", "what did you learn recently", "what have you learned recently", "entity memory", "structured memory", "remembered entities", "what entities", "who is", "what do you know about"]):
                return IntentResult("memory_search", 0.86, "Memory search/list/review phrase detected.")
            return IntentResult("memory_write", 0.78, "Memory phrase detected.")

        if any(phrase in text for phrase in ["search project files", "find file", "project status", "jarvis project status", "file", "folder", "storage", "delete", "move this"]):
            return IntentResult("file_task", 0.7, "File/storage phrase detected.")

        if any(phrase in text for phrase in ["record", "clip that", "start recording", "stop recording"]):
            return IntentResult("recording_task", 0.8, "Recording phrase detected.")

        if "weather" in text or "forecast" in text or "temperature" in text:
            return IntentResult("weather_lookup", 0.8, "Weather phrase detected.")

        return IntentResult("general_chat", 0.45, "No tool-specific intent detected; using conversation fallback.")

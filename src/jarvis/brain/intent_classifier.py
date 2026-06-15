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
            "stop remembering",
        ]
        if any(phrase in text for phrase in memory_phrases):
            if any(phrase in text for phrase in ["what do you remember", "what memories", "list memories", "show memories", "search memory", "search memories"]):
                return IntentResult("memory_search", 0.82, "Memory search/list phrase detected.")
            return IntentResult("memory_write", 0.78, "Memory phrase detected.")

        if any(phrase in text for phrase in ["search project files", "find file", "project status", "jarvis project status", "file", "folder", "storage", "delete", "move this"]):
            return IntentResult("file_task", 0.7, "File/storage phrase detected.")

        if any(phrase in text for phrase in ["record", "clip that", "start recording", "stop recording"]):
            return IntentResult("recording_task", 0.8, "Recording phrase detected.")

        if "weather" in text or "forecast" in text or "temperature" in text:
            return IntentResult("weather_lookup", 0.8, "Weather phrase detected.")

        return IntentResult("general_chat", 0.45, "No tool-specific intent detected; using conversation fallback.")

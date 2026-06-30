"""Tests for 0.3.6 sensitive chat redaction and memory log hygiene."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities
from jarvis.core.logging import JarvisLogger
from jarvis.core.result import JarvisResult
from jarvis.memory.always_on import ChatArchiveStore, MemoryCandidateStore
from jarvis.memory.hygiene import redact_sensitive_runtime_files
from jarvis.memory.secure_vault import redact_sensitive_payload, redact_sensitive_text
from jarvis.ui.workspace import UIWorkspaceState


class MemoryRedactionHygiene036Tests(unittest.TestCase):
    def test_version_and_capabilities_include_redaction_hygiene(self) -> None:
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d3")
        capabilities = set(app_shell_capabilities())
        self.assertIn("sensitive_chat_archive_redaction", capabilities)
        self.assertIn("sensitive_ui_history_redaction", capabilities)
        self.assertIn("memory_log_hygiene_redaction", capabilities)

    def test_redactor_masks_sensitive_values_but_keeps_safe_password_sentences(self) -> None:
        self.assertEqual(redact_sensitive_text("I cannot save passwords in normal memory."), "I cannot save passwords in normal memory.")
        redacted = redact_sensitive_text("Remember that my password is Hunter 2.")
        self.assertIn("password [redacted]", redacted.lower())
        self.assertNotIn("Hunter", redacted)
        self.assertNotIn(" 2", redacted)

        financial = redact_sensitive_text("Remember that my bank account number is 123456789.")
        self.assertIn("account number [redacted]", financial.lower())
        self.assertNotIn("123456789", financial)

    def test_chat_archive_redacts_before_writing_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = ChatArchiveStore(root_dir=Path(tmp) / "archive")
            record = archive.append_turn(
                user="Remember that my password is Hunter 2.",
                assistant="I cannot save passwords in normal memory, sir.",
                metadata={"command": "Remember that my bank account number is 123456789."},
            )
            self.assertIsNotNone(record)
            written = "\n".join(path.read_text(encoding="utf-8") for path in (Path(tmp) / "archive").glob("*.jsonl"))
            self.assertNotIn("Hunter", written)
            self.assertNotIn("123456789", written)
            self.assertIn("[redacted]", written)
            self.assertIn("sensitive_redacted", written)

    def test_memory_candidate_sources_are_redacted_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MemoryCandidateStore(path=Path(tmp) / "candidates.json")
            store.add(
                "Remember that my API key is sk-test-12345678901234567890.",
                source_user="My password is Hunter 2.",
                source_assistant="I routed the password to the vault.",
                metadata={"token": "secret-token-12345678901234567890"},
            )
            raw = (Path(tmp) / "candidates.json").read_text(encoding="utf-8")
            self.assertNotIn("sk-test", raw)
            self.assertNotIn("Hunter", raw)
            self.assertNotIn("secret-token", raw)
            self.assertIn("[redacted", raw)

    def test_workspace_chat_messages_redact_sensitive_values(self) -> None:
        workspace = UIWorkspaceState()
        workspace.add_chat_message("user", "Remember that my password is Hunter 2.")
        snapshot = workspace.snapshot()
        text = snapshot["chat_messages"][-1]["text"]
        self.assertIn("password [redacted]", text.lower())
        self.assertNotIn("Hunter", text)

    def test_logger_redacts_jsonl_events_and_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logger = JarvisLogger(logs_dir=Path(tmp) / "logs")
            logger.log_event("test.secret", source="test", message="Secret event", data={"command": "my password is Hunter 2"})
            logger.log_result(JarvisResult.ok("Done", data={"api_key": "sk-test-12345678901234567890"}))
            combined = "\n".join(path.read_text(encoding="utf-8") for path in (Path(tmp) / "logs").rglob("*.jsonl"))
            self.assertNotIn("Hunter", combined)
            self.assertNotIn("sk-test", combined)
            self.assertIn("[redacted", combined)

    def test_runtime_file_hygiene_redacts_existing_chat_and_log_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_dir = root / "data" / "memory" / "chat_archive"
            archive_dir.mkdir(parents=True)
            archive_file = archive_dir / "2026-06-23.jsonl"
            archive_file.write_text(
                json.dumps({"user": "my password is Hunter 2", "assistant": "ok"}) + "\n",
                encoding="utf-8",
            )
            log_dir = root / "logs" / "brain"
            log_dir.mkdir(parents=True)
            (log_dir / "events.jsonl").write_text(
                json.dumps({"data": {"account_number": "123456789"}}) + "\n",
                encoding="utf-8",
            )

            result = redact_sensitive_runtime_files(root)
            self.assertGreaterEqual(result.scanned_files, 2)
            self.assertGreaterEqual(result.updated_files, 2)
            combined = archive_file.read_text(encoding="utf-8") + (log_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertNotIn("Hunter", combined)
            self.assertNotIn("123456789", combined)
            self.assertIn("[redacted", combined)

    def test_recursive_payload_redaction_redacts_sensitive_keys(self) -> None:
        payload = {"nested": {"password": "Hunter 2", "safe": "password vault status"}}
        redacted = redact_sensitive_payload(payload)
        self.assertEqual(redacted["nested"]["password"], "[redacted]")
        self.assertEqual(redacted["nested"]["safe"], "password vault status")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

"""Secure-vault routing foundation for sensitive Jarvis memory.

This 0.3.5a layer deliberately keeps passwords, API keys, account numbers,
recovery codes, and similar sensitive values out of normal memory, chat
summaries, and entity memory.  It prepares the future Password Manager / Secure
Vault Agent by detecting explicit save attempts and routing them to a vault
response without storing the raw secret until encrypted local vault storage is
implemented and enabled.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
    return " ".join(cleaned.split())


VAULT_CATEGORY_LABELS: dict[str, str] = {
    "vault_password": "password",
    "vault_api_key": "API key",
    "vault_token": "access token",
    "vault_recovery_code": "recovery code",
    "vault_financial": "financial information",
    "vault_private_key": "private key",
    "vault_wifi_password": "Wi-Fi password",
    "vault_secret": "secret",
}


VAULT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("vault_private_key", (r"\bprivate\s+key\b", r"-----BEGIN\s+(?:RSA\s+|OPENSSH\s+|EC\s+)?PRIVATE\s+KEY-----")),
    ("vault_api_key", (r"\bapi\s*key\b", r"\bsecret\s*key\b", r"\bclient\s*secret\b")),
    ("vault_token", (r"\baccess\s*token\b", r"\bbearer\s+[a-z0-9_\-\.]{12,}\b", r"\bauth\s*token\b")),
    ("vault_recovery_code", (r"\brecovery\s+code\b", r"\bbackup\s+code\b", r"\bseed\s+phrase\b", r"\bmnemonic\b")),
    ("vault_wifi_password", (r"\bwifi\s+password\b", r"\bwi\s*fi\s+password\b", r"\bwireless\s+password\b")),
    ("vault_password", (r"\bpassword\b", r"\bpasscode\b", r"\bpin\b")),
    ("vault_financial", (r"\bcredit\s+card\b", r"\bcard\s+number\b", r"\bcvv\b", r"\brouting\s+number\b", r"\baccount\s+number\b", r"\bbank\s+account\b", r"\bfinancial\b", r"\bbank\b", r"\bdebit\s+card\b")),
)


EXPLICIT_SAVE_VERBS = (
    "remember",
    "save",
    "store",
    "keep",
    "write down",
    "note",
)


@dataclass(slots=True)
class SecureVaultDecision:
    """Result of routing a sensitive save request."""

    sensitive: bool
    explicit: bool
    vault_category: str
    label: str
    action: str
    reason: str
    stored: bool = False
    enabled: bool = False
    encrypted_storage_ready: bool = False
    redacted_preview: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SecureVaultStore:
    """Placeholder vault service until encrypted local storage is implemented.

    This object intentionally does not write raw secrets.  It gives the Memory
    Agent a clear future integration point for an encrypted local vault while
    preventing secret-like data from leaking into normal memory today.
    """

    enabled: bool = False
    path: str | Path | None = None
    encrypted_storage_ready: bool = False
    schema_version: int = 1
    updated_at: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        self.path = Path(self.path) if self.path else Path("data/secure_vault/vault.json")

    def status(self) -> dict[str, Any]:
        return {
            "enabled": bool(self.enabled),
            "encrypted_storage_ready": bool(self.encrypted_storage_ready),
            "path": str(self.path),
            "schema_version": self.schema_version,
            "stores_raw_values": False,
            "routing_only": not (self.enabled and self.encrypted_storage_ready),
            "updated_at": self.updated_at,
        }

    def route_sensitive_save(self, text: str, *, category: str = "", explicit: bool = True, metadata: dict[str, Any] | None = None) -> SecureVaultDecision:
        vault_category = classify_vault_category(text, category=category)
        label = vault_category_label(vault_category)
        sensitive = bool(vault_category)
        if not sensitive:
            return SecureVaultDecision(
                sensitive=False,
                explicit=explicit,
                vault_category="",
                label="",
                action="not_sensitive",
                reason="The text does not look like secure-vault data.",
                stored=False,
                enabled=bool(self.enabled),
                encrypted_storage_ready=bool(self.encrypted_storage_ready),
                redacted_preview=redact_sensitive_text(text),
            )

        if not explicit:
            return SecureVaultDecision(
                sensitive=True,
                explicit=False,
                vault_category=vault_category,
                label=label,
                action="blocked_auto_capture",
                reason="Sensitive vault data is never captured automatically.",
                stored=False,
                enabled=bool(self.enabled),
                encrypted_storage_ready=bool(self.encrypted_storage_ready),
                redacted_preview=redact_sensitive_text(text),
            )

        # Future encrypted implementation hooks in here.  Until then, never
        # persist the raw value.  This protects SaaS users from secrets leaking
        # into normal memory, backups, chat summaries, or LLM context.
        return SecureVaultDecision(
            sensitive=True,
            explicit=True,
            vault_category=vault_category,
            label=label,
            action="vault_storage_not_enabled",
            reason="Encrypted local vault storage is not enabled yet.",
            stored=False,
            enabled=bool(self.enabled),
            encrypted_storage_ready=bool(self.encrypted_storage_ready),
            redacted_preview=redact_sensitive_text(text),
        )


def classify_vault_category(text: str, *, category: str = "") -> str:
    normalized_category = normalize_text(str(category or "")).replace(" ", "_")
    if normalized_category in {"secrets", "secret", "private"}:
        # Prefer a more specific pattern if one is present.
        detected = classify_vault_category(text, category="")
        return detected or "vault_secret"
    if normalized_category == "financial":
        detected = classify_vault_category(text, category="")
        return detected if detected and detected != "vault_secret" else "vault_financial"

    lowered = str(text or "").lower()
    for vault_category, patterns in VAULT_PATTERNS:
        for pattern in patterns:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                return vault_category
    return ""


def is_vault_like(text: str, *, category: str = "") -> bool:
    return bool(classify_vault_category(text, category=category))


def is_explicit_sensitive_save_request(text: str) -> bool:
    lowered = normalize_text(text)
    return any(verb in lowered for verb in EXPLICIT_SAVE_VERBS) and is_vault_like(text)


def vault_category_label(vault_category: str) -> str:
    return VAULT_CATEGORY_LABELS.get(str(vault_category or ""), "sensitive information")


def redact_sensitive_text(text: str, *, max_chars: int = 120) -> str:
    """Return a short preview that avoids echoing likely secret values."""

    value = " ".join(str(text or "").split())
    if not value:
        return ""
    replacements: Iterable[tuple[str, str]] = (
        (r"(?i)(password|passcode|pin)\s*(?:is|=|:)?\s*\S+", r"\1 [redacted]"),
        (r"(?i)(api\s*key|secret\s*key|client\s*secret|access\s*token|auth\s*token)\s*(?:is|=|:)?\s*\S+", r"\1 [redacted]"),
        (r"(?i)(account\s+number|routing\s+number|card\s+number|credit\s+card|cvv)\s*(?:is|=|:)?\s*[\w\- ]+", r"\1 [redacted]"),
        (r"(?i)(recovery\s+code|backup\s+code|seed\s+phrase|private\s+key)\s*(?:is|=|:)?\s*.+", r"\1 [redacted]"),
        (r"\b\d{12,19}\b", "[redacted-number]"),
        (r"\b[A-Za-z0-9_\-]{20,}\b", "[redacted-secret]"),
    )
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value)
    if len(value) > max_chars:
        value = value[: max_chars - 3].rstrip() + "..."
    return value

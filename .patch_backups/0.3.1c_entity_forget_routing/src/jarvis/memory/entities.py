"""Scalable entity memory foundation for Jarvis.

Entity memory is a structured layer beside long-term facts, short-term facts,
chat archives, and memory candidates.  Long-term memory answers "what fact did
I save?" while entity memory answers "who/what is this thing and what do I know
about it?"  The registry is intentionally data-driven so SaaS deployments can
add new entity types later without rewriting the store.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Crash-safe JSON write used by all entity-memory persistence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(value or "").lower())
    return " ".join(cleaned.split())


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    return sorted({normalize_text(tag) for tag in tags if normalize_text(tag)})


def _token_variants(tokens: Iterable[str]) -> set[str]:
    expanded: set[str] = set()
    for token in tokens:
        token = str(token or "").strip().lower()
        if not token:
            continue
        expanded.add(token)
        if len(token) > 4 and token.endswith("es"):
            expanded.add(token[:-2])
        if len(token) > 3 and token.endswith("s"):
            expanded.add(token[:-1])
    return expanded


def _clean_title(value: str) -> str:
    cleaned = " ".join(str(value or "").strip().strip(" .?!,;:\"'").split())
    return cleaned


@dataclass(slots=True)
class EntityTypeDefinition:
    """Configurable entity type definition.

    The default registry covers common assistant memory objects, but SaaS
    deployments can register tenant-specific types such as team, ticket,
    workspace, medication, asset, subscription, or customer without changing the
    core storage schema.
    """

    type_name: str
    label: str
    aliases: list[str] = field(default_factory=list)
    description: str = ""
    default_attributes: list[str] = field(default_factory=list)
    sensitive: bool = False
    retention_policy: str = "user_controlled"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "EntityTypeDefinition | None":
        type_name = normalize_entity_type(str(item.get("type_name") or item.get("name") or ""))
        if not type_name:
            return None
        aliases_raw = item.get("aliases")
        attrs_raw = item.get("default_attributes")
        return cls(
            type_name=type_name,
            label=str(item.get("label") or type_name.replace("_", " ").title()),
            aliases=[normalize_text(alias) for alias in aliases_raw if normalize_text(alias)] if isinstance(aliases_raw, list) else [],
            description=str(item.get("description") or ""),
            default_attributes=[normalize_text(attr) for attr in attrs_raw if normalize_text(attr)] if isinstance(attrs_raw, list) else [],
            sensitive=bool(item.get("sensitive", False)),
            retention_policy=str(item.get("retention_policy") or "user_controlled"),
        )


@dataclass(slots=True)
class EntityRecord:
    """One structured thing Jarvis knows about."""

    name: str
    entity_type: str = "general"
    summary: str = ""
    aliases: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    source: str = "user"
    importance: int = 3
    confidence: float = 0.7
    sensitivity: str = "normal"
    scope: str = "personal"
    id: str = field(default_factory=lambda: f"ent_{uuid4().hex[:12]}")
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_name(self) -> str:
        return normalize_text(self.name)

    @property
    def normalized_aliases(self) -> set[str]:
        return {normalize_text(alias) for alias in self.aliases if normalize_text(alias)}

    @property
    def search_blob(self) -> str:
        parts = [self.name, self.entity_type, self.summary, " ".join(self.aliases), " ".join(self.tags)]
        for key, value in self.attributes.items():
            parts.append(str(key))
            parts.append(str(value))
        for rel in self.relationships:
            parts.extend(str(value) for value in rel.values())
        return normalize_text(" ".join(parts))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, item: dict[str, Any]) -> "EntityRecord | None":
        name = _clean_title(str(item.get("name") or ""))
        if not name:
            return None
        aliases_raw = item.get("aliases")
        relationships_raw = item.get("relationships")
        tags_raw = item.get("tags")
        try:
            importance = int(item.get("importance", 3))
        except (TypeError, ValueError):
            importance = 3
        try:
            confidence = float(item.get("confidence", 0.7))
        except (TypeError, ValueError):
            confidence = 0.7
        return cls(
            id=str(item.get("id") or f"ent_{uuid4().hex[:12]}"),
            name=name,
            entity_type=normalize_entity_type(str(item.get("entity_type") or "general")) or "general",
            summary=str(item.get("summary") or ""),
            aliases=sorted({_clean_title(alias) for alias in aliases_raw if _clean_title(alias)}) if isinstance(aliases_raw, list) else [],
            attributes=item.get("attributes") if isinstance(item.get("attributes"), dict) else {},
            relationships=[rel for rel in relationships_raw if isinstance(rel, dict)] if isinstance(relationships_raw, list) else [],
            tags=_normalize_tags(tags_raw if isinstance(tags_raw, list) else []),
            source=str(item.get("source") or "user"),
            importance=max(1, min(5, importance)),
            confidence=max(0.0, min(1.0, confidence)),
            sensitivity=str(item.get("sensitivity") or "normal"),
            scope=str(item.get("scope") or "personal"),
            created_at=str(item.get("created_at") or utc_now_iso()),
            updated_at=str(item.get("updated_at") or item.get("created_at") or utc_now_iso()),
            metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
        )


@dataclass(slots=True)
class EntitySearchResult:
    record: EntityRecord
    score: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = self.record.to_dict()
        data["score"] = self.score
        data["reason"] = self.reason
        data["tier"] = "entity"
        return data


def default_entity_types() -> dict[str, EntityTypeDefinition]:
    """Built-in registry for the first scalable entity memory milestone."""

    definitions = [
        EntityTypeDefinition(
            "user",
            "User profile",
            aliases=["owner", "account_user", "customer", "sir"],
            description="Stable user profile details and broad assistant preferences.",
            default_attributes=["name", "preferences", "goals", "working_style"],
        ),
        EntityTypeDefinition(
            "person",
            "Person",
            aliases=["people", "friend", "family", "contact", "relationship"],
            description="People the user wants Jarvis to remember, such as family, friends, team members, or customers.",
            default_attributes=["relationship", "preferences", "notes"],
        ),
        EntityTypeDefinition(
            "pet",
            "Pet",
            aliases=["animal", "dog", "cat"],
            description="Pets and care-related details.",
            default_attributes=["species", "breed", "care", "preferences"],
        ),
        EntityTypeDefinition(
            "project",
            "Project",
            aliases=["product", "repo", "codebase", "saas", "milestone"],
            description="Projects, products, repos, goals, versions, and decisions.",
            default_attributes=["status", "version", "roadmap", "rules", "decisions"],
        ),
        EntityTypeDefinition(
            "app",
            "App or tool",
            aliases=["software", "program", "tool", "service"],
            description="Apps, tools, app aliases, roles, settings, and common workflows.",
            default_attributes=["role", "path", "aliases", "settings", "workflow"],
        ),
        EntityTypeDefinition(
            "place",
            "Place",
            aliases=["location", "city", "venue"],
            description="Places the user references often. Exact private addresses should stay user-controlled.",
            default_attributes=["area", "notes", "preferences"],
        ),
        EntityTypeDefinition(
            "device",
            "Device",
            aliases=["hardware", "computer", "laptop", "phone", "monitor"],
            description="User devices, specs, settings, and issues.",
            default_attributes=["model", "specs", "settings", "issues"],
        ),
        EntityTypeDefinition(
            "vehicle",
            "Vehicle",
            aliases=["car", "truck"],
            description="Vehicles, specs, mileage, and repair context.",
            default_attributes=["year", "make", "model", "mileage", "issues"],
        ),
        EntityTypeDefinition(
            "organization",
            "Organization",
            aliases=["company", "school", "bank", "vendor", "team"],
            description="Companies, schools, teams, banks, or services the user talks about.",
            default_attributes=["role", "notes", "relationship"],
        ),
    ]
    return {definition.type_name: definition for definition in definitions}


def normalize_entity_type(value: str) -> str:
    normalized = normalize_text(value).replace(" ", "_")
    aliases = {
        "people": "person",
        "persons": "person",
        "friend": "person",
        "family": "person",
        "contact": "person",
        "pet": "pet",
        "pets": "pet",
        "dog": "pet",
        "dogs": "pet",
        "cat": "pet",
        "cats": "pet",
        "animal": "pet",
        "animals": "pet",
        "project": "project",
        "projects": "project",
        "repo": "project",
        "repos": "project",
        "codebase": "project",
        "codebases": "project",
        "product": "project",
        "products": "project",
        "saas": "project",
        "app": "app",
        "apps": "app",
        "tool": "app",
        "tools": "app",
        "software": "app",
        "program": "app",
        "tool": "app",
        "service": "app",
        "services": "app",
        "place": "place",
        "places": "place",
        "location": "place",
        "locations": "place",
        "city": "place",
        "cities": "place",
        "device": "device",
        "devices": "device",
        "computer": "device",
        "laptop": "device",
        "phone": "device",
        "monitor": "device",
        "hardware": "device",
        "vehicle": "vehicle",
        "vehicles": "vehicle",
        "car": "vehicle",
        "cars": "vehicle",
        "truck": "vehicle",
        "trucks": "vehicle",
        "organization": "organization",
        "organizations": "organization",
        "company": "organization",
        "companies": "organization",
        "school": "organization",
        "schools": "organization",
        "bank": "organization",
        "banks": "organization",
        "team": "organization",
        "teams": "organization",
    }
    return aliases.get(normalized, normalized)


class EntityMemoryStore:
    """JSON-backed structured entity memory store."""

    schema_version = 1

    def __init__(
        self,
        *,
        enabled: bool = True,
        path: str | Path | None = None,
        max_records: int = 2000,
        inject_limit: int = 5,
        entity_types: Iterable[EntityTypeDefinition] | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.path = Path(path) if path else Path("data/memory/entities.json")
        self.max_records = max(50, int(max_records))
        self.inject_limit = max(0, int(inject_limit))
        self._entity_types: dict[str, EntityTypeDefinition] = default_entity_types()
        if entity_types:
            for definition in entity_types:
                self._entity_types[definition.type_name] = definition
        self._records: list[EntityRecord] = []
        self.load()

    @property
    def records(self) -> tuple[EntityRecord, ...]:
        return tuple(self._records)

    @property
    def entity_types(self) -> dict[str, EntityTypeDefinition]:
        return dict(self._entity_types)

    def register_entity_type(
        self,
        type_name: str,
        *,
        label: str | None = None,
        aliases: Iterable[str] | None = None,
        description: str = "",
        default_attributes: Iterable[str] | None = None,
        sensitive: bool = False,
        retention_policy: str = "user_controlled",
    ) -> EntityTypeDefinition | None:
        """Register or update an entity type without changing code elsewhere."""

        normalized = normalize_entity_type(type_name)
        if not normalized:
            return None
        existing = self._entity_types.get(normalized)
        definition = EntityTypeDefinition(
            type_name=normalized,
            label=label or (existing.label if existing else normalized.replace("_", " ").title()),
            aliases=sorted({*(_normalize_tags(aliases or [])), *(existing.aliases if existing else [])}),
            description=description or (existing.description if existing else ""),
            default_attributes=sorted({*(_normalize_tags(default_attributes or [])), *(existing.default_attributes if existing else [])}),
            sensitive=bool(sensitive or (existing.sensitive if existing else False)),
            retention_policy=retention_policy or (existing.retention_policy if existing else "user_controlled"),
        )
        self._entity_types[normalized] = definition
        self.save()
        return definition

    def upsert(
        self,
        name: str,
        *,
        entity_type: str = "general",
        summary: str = "",
        aliases: Iterable[str] | None = None,
        attributes: dict[str, Any] | None = None,
        relationships: Iterable[dict[str, Any]] | None = None,
        tags: Iterable[str] | None = None,
        source: str = "user",
        importance: int = 3,
        confidence: float = 0.7,
        sensitivity: str = "normal",
        scope: str = "personal",
        metadata: dict[str, Any] | None = None,
    ) -> EntityRecord | None:
        if not self.enabled:
            return None
        cleaned_name = _clean_title(name)
        if not cleaned_name:
            return None
        normalized_type = normalize_entity_type(entity_type) or "general"
        alias_list = sorted({_clean_title(alias) for alias in aliases or [] if _clean_title(alias) and normalize_text(alias) != normalize_text(cleaned_name)})
        tag_list = _normalize_tags([*(tags or []), normalized_type])
        now = utc_now_iso()
        existing = self._find_duplicate(cleaned_name, normalized_type, aliases=alias_list)
        if existing is None:
            record = EntityRecord(
                name=cleaned_name,
                entity_type=normalized_type,
                summary=" ".join(str(summary or "").split()),
                aliases=alias_list,
                attributes=dict(attributes or {}),
                relationships=self._dedupe_relationships(list(relationships or [])),
                tags=tag_list,
                source=source,
                importance=max(1, min(5, int(importance))),
                confidence=max(0.0, min(1.0, float(confidence))),
                sensitivity=str(sensitivity or "normal"),
                scope=str(scope or "personal"),
                metadata=dict(metadata or {}),
            )
            self._records.append(record)
            self._trim()
            self.save()
            return record

        existing.summary = self._merge_summary(existing.summary, summary)
        existing.aliases = sorted({*existing.aliases, *alias_list})
        existing.attributes = self._merge_attributes(existing.attributes, attributes or {})
        existing.relationships = self._dedupe_relationships([*existing.relationships, *(relationships or [])])
        existing.tags = sorted({*existing.tags, *tag_list})
        existing.source = source or existing.source
        existing.importance = max(existing.importance, max(1, min(5, int(importance))))
        existing.confidence = max(existing.confidence, max(0.0, min(1.0, float(confidence))))
        if sensitivity and existing.sensitivity == "normal":
            existing.sensitivity = str(sensitivity)
        existing.scope = str(scope or existing.scope or "personal")
        existing.updated_at = now
        existing.metadata.update(metadata or {})
        self.save()
        return existing

    def upsert_from_text(
        self,
        text: str,
        *,
        source: str = "user",
        metadata: dict[str, Any] | None = None,
        confidence: float | None = None,
    ) -> EntityRecord | None:
        extraction = infer_entity_from_text(text)
        if extraction is None:
            return None
        return self.upsert(
            extraction["name"],
            entity_type=extraction.get("entity_type", "general"),
            summary=extraction.get("summary", text),
            aliases=extraction.get("aliases", []),
            attributes=extraction.get("attributes", {}),
            relationships=extraction.get("relationships", []),
            tags=extraction.get("tags", []),
            source=source,
            importance=int(extraction.get("importance", 3)),
            confidence=confidence if confidence is not None else float(extraction.get("confidence", 0.72)),
            sensitivity=str(extraction.get("sensitivity", "normal")),
            metadata={**dict(extraction.get("metadata", {})), **dict(metadata or {}), "source_text": text},
        )

    def search(self, query: str, *, entity_type: str | None = None, limit: int = 5) -> list[EntitySearchResult]:
        if not self.enabled:
            return []
        normalized_query = normalize_text(query)
        if not normalized_query:
            return []
        query_tokens = _token_variants(normalized_query.split())
        type_filter = normalize_entity_type(entity_type or "") if entity_type else ""
        results: list[EntitySearchResult] = []
        for record in self._records:
            if type_filter and record.entity_type != type_filter:
                continue
            score, reason = self._score(record, normalized_query, query_tokens)
            if score > 0:
                score += record.importance * 0.03
                results.append(EntitySearchResult(record=record, score=round(score, 3), reason=reason))
        results.sort(key=lambda item: (item.score, item.record.updated_at), reverse=True)
        return results[: max(1, int(limit))]

    def relevant_context(self, query: str, *, limit: int | None = None) -> str:
        selected_limit = self.inject_limit if limit is None else int(limit)
        if selected_limit <= 0:
            return ""
        results = self.search(query, limit=selected_limit)
        if not results:
            return ""
        lines = ["Relevant remembered entities:"]
        for result in results:
            record = result.record
            summary = record.summary or f"{record.name} is remembered as {record.entity_type}."
            lines.append(f"- {record.name} ({record.entity_type}): {_second_person_summary(summary)}")
        return "\n".join(lines)

    def list_records(self, *, entity_type: str | None = None, limit: int = 8) -> list[EntityRecord]:
        if not self.enabled:
            return []
        records = list(self._records)
        if entity_type:
            type_filter = normalize_entity_type(entity_type)
            records = [record for record in records if record.entity_type == type_filter]
        records.sort(key=lambda record: record.updated_at, reverse=True)
        return records[: max(1, int(limit))]

    def forget(self, query: str, *, entity_type: str | None = None, limit: int | None = None) -> list[EntityRecord]:
        if not self.enabled:
            return []
        normalized = normalize_text(query)
        if not normalized:
            return []

        type_filter = normalize_entity_type(entity_type or "") if entity_type else ""
        query_tokens = _token_variants(normalized.split())
        removed: list[EntityRecord] = []
        kept: list[EntityRecord] = []
        max_remove = len(self._records) if limit is None else max(1, int(limit))

        for record in self._records:
            if type_filter and record.entity_type != type_filter:
                kept.append(record)
                continue
            if self._record_matches_forget_query(record, normalized, query_tokens) and len(removed) < max_remove:
                removed.append(record)
            else:
                kept.append(record)

        if removed:
            self._records = kept
            self.save()
        return removed

    def format_records(self, *, query: str = "", entity_type: str | None = None, limit: int = 8) -> str:
        if not self.enabled:
            return "Entity memory is disabled, sir."
        if query:
            records = [match.record for match in self.search(query, entity_type=entity_type, limit=limit)]
            if not records:
                return f"I do not have any entity memories matching {query!r}, sir."
        else:
            records = self.list_records(entity_type=entity_type, limit=limit)
            if not records:
                if entity_type:
                    label = normalize_entity_type(entity_type).replace("_", " ")
                    return f"I do not have any remembered {label} records yet, sir."
                return "I do not have any structured entity memories yet, sir."
        lines = ["Structured entity memories:"]
        for record in records:
            label = record.entity_type.replace("_", " ")
            summary = _second_person_summary(record.summary or f"remembered {label}")
            lines.append(f"- {record.name} ({label}): {summary}")
        return "\n".join(lines)

    def format_status(self) -> str:
        info = self.status()
        state = "enabled" if info["enabled"] else "disabled"
        by_type = info.get("by_type", {})
        if by_type:
            type_summary = ", ".join(f"{key}: {value}" for key, value in sorted(by_type.items()))
        else:
            type_summary = "no entities saved yet"
        return f"Entity memory status: {state}, {info['records']} records across {info['entity_type_count']} registered entity types ({type_summary})."

    def status(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for record in self._records:
            by_type[record.entity_type] = by_type.get(record.entity_type, 0) + 1
        return {
            "enabled": self.enabled,
            "path": str(self.path),
            "records": len(self._records),
            "max_records": self.max_records,
            "inject_limit": self.inject_limit,
            "entity_type_count": len(self._entity_types),
            "entity_types": sorted(self._entity_types),
            "by_type": by_type,
            "schema_version": self.schema_version,
        }

    def save(self) -> None:
        if not self.enabled:
            return
        payload = {
            "schema_version": self.schema_version,
            "updated_at": utc_now_iso(),
            "entity_types": {key: definition.to_dict() for key, definition in sorted(self._entity_types.items())},
            "records": [record.to_dict() for record in self._records],
        }
        atomic_write_json(self.path, payload)

    def load(self) -> None:
        if not self.enabled or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        raw_types = payload.get("entity_types")
        if isinstance(raw_types, dict):
            for raw in raw_types.values():
                if isinstance(raw, dict):
                    definition = EntityTypeDefinition.from_dict(raw)
                    if definition is not None:
                        self._entity_types[definition.type_name] = definition
        raw_records = payload.get("records", [])
        records: list[EntityRecord] = []
        if isinstance(raw_records, list):
            for raw in raw_records:
                if isinstance(raw, dict):
                    record = EntityRecord.from_dict(raw)
                    if record is not None:
                        records.append(record)
        self._records = self._dedupe_loaded_records(records)

    def _score(self, record: EntityRecord, normalized_query: str, query_tokens: set[str]) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []
        normalized_name = record.normalized_name
        alias_tokens = {token for alias in record.normalized_aliases for token in alias.split()}
        tag_tokens = {token for tag in record.tags for token in normalize_text(tag).split()}
        type_tokens = set(normalize_text(record.entity_type).split())
        blob = record.search_blob
        blob_tokens = _token_variants(blob.split())
        if normalized_query == normalized_name:
            score += 3.0
            reasons.append("exact entity name match")
        elif normalized_query in {normalized_name, *record.normalized_aliases}:
            score += 2.5
            reasons.append("entity alias match")
        elif normalized_query in blob:
            score += 1.4
            reasons.append("entity text contains query")
        overlap = query_tokens & (blob_tokens | alias_tokens | tag_tokens | type_tokens)
        if overlap:
            score += len(overlap) / max(len(query_tokens), 1)
            reasons.append("token overlap: " + ", ".join(sorted(overlap)))
        if query_tokens & type_tokens:
            score += 0.5
            reasons.append("entity type match")
        if query_tokens & tag_tokens:
            score += 0.4
            reasons.append("entity tag match")
        return score, "; ".join(reasons)

    def _find_duplicate(self, name: str, entity_type: str, *, aliases: Iterable[str] = ()) -> EntityRecord | None:
        normalized_name = normalize_text(name)
        alias_set = {normalize_text(alias) for alias in aliases if normalize_text(alias)}
        for record in self._records:
            if record.entity_type != entity_type:
                continue
            record_names = {record.normalized_name, *record.normalized_aliases}
            if normalized_name in record_names or record.normalized_name in alias_set or record_names & alias_set:
                return record
        return None

    def _record_matches_forget_query(self, record: EntityRecord, normalized_query: str, query_tokens: set[str]) -> bool:
        if not normalized_query:
            return False
        identity_values = {record.normalized_name, *record.normalized_aliases}
        if str(record.id).lower() == normalized_query:
            return True
        if normalized_query in identity_values:
            return True
        identity_tokens = {token for value in identity_values for token in value.split()}
        if query_tokens and query_tokens <= identity_tokens:
            return True
        blob = record.search_blob
        blob_tokens = _token_variants(blob.split())
        if normalized_query in blob:
            return True
        if query_tokens and query_tokens <= blob_tokens:
            return True
        source_text = ""
        if isinstance(record.metadata, dict):
            source_text = normalize_text(str(record.metadata.get("source_text") or record.metadata.get("source_command") or ""))
        return bool(source_text and normalized_query in source_text)

    def _merge_record_into(self, existing: EntityRecord, incoming: EntityRecord) -> EntityRecord:
        existing.summary = self._merge_summary(existing.summary, incoming.summary)
        existing.aliases = sorted({*existing.aliases, *incoming.aliases})
        existing.attributes = self._merge_attributes(existing.attributes, incoming.attributes)
        existing.relationships = self._dedupe_relationships([*existing.relationships, *incoming.relationships])
        existing.tags = sorted({*existing.tags, *incoming.tags})
        existing.importance = max(existing.importance, incoming.importance)
        existing.confidence = max(existing.confidence, incoming.confidence)
        if existing.sensitivity == "normal" and incoming.sensitivity != "normal":
            existing.sensitivity = incoming.sensitivity
        if incoming.updated_at >= existing.updated_at:
            existing.name = incoming.name or existing.name
            existing.source = incoming.source or existing.source
            existing.scope = incoming.scope or existing.scope
            existing.updated_at = incoming.updated_at
        existing.metadata.update(incoming.metadata or {})
        return existing

    def _trim(self) -> None:
        if self.max_records and len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]

    def _dedupe_loaded_records(self, records: list[EntityRecord]) -> list[EntityRecord]:
        selected: list[EntityRecord] = []
        for record in records:
            existing = None
            identity = {record.normalized_name, *record.normalized_aliases}
            for current in selected:
                if current.entity_type != record.entity_type:
                    continue
                current_identity = {current.normalized_name, *current.normalized_aliases}
                if identity & current_identity:
                    existing = current
                    break
            if existing is None:
                selected.append(record)
            else:
                self._merge_record_into(existing, record)
        return selected

    @staticmethod
    def _merge_summary(old: str, new: str) -> str:
        old_clean = " ".join(str(old or "").split())
        new_clean = " ".join(str(new or "").split())
        if not new_clean:
            return old_clean
        if not old_clean:
            return new_clean
        old_norm = normalize_text(old_clean)
        new_norm = normalize_text(new_clean)
        if new_norm in old_norm:
            return old_clean
        if old_norm in new_norm:
            return new_clean
        return f"{old_clean}; {new_clean}"

    @staticmethod
    def _merge_attributes(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        merged = dict(old or {})
        for key, value in (new or {}).items():
            clean_key = normalize_text(str(key)).replace(" ", "_")
            if not clean_key or value in (None, "", [], {}):
                continue
            existing = merged.get(clean_key)
            if existing in (None, "", [], {}):
                merged[clean_key] = value
            elif existing != value:
                if isinstance(existing, list):
                    merged[clean_key] = sorted({*map(str, existing), str(value)})
                else:
                    merged[clean_key] = sorted({str(existing), str(value)})
        return merged

    @staticmethod
    def _dedupe_relationships(relationships: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for relationship in relationships:
            if not isinstance(relationship, dict):
                continue
            cleaned = {str(key): value for key, value in relationship.items() if value not in (None, "")}
            if not cleaned:
                continue
            key = json.dumps(cleaned, sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(cleaned)
        return deduped



_PERSON_NAME_PATTERN = r"([A-Z][A-Za-z0-9_\-']{1,40}(?:\s+[A-Z][A-Za-z0-9_\-']{1,40}){0,3})"


def _normalize_relationship_label(value: str) -> str:
    relation = _clean_title(str(value or "").lower())
    aliases = {
        "fiance": "fiancée",
        "fiancee": "fiancée",
        "fiancée": "fiancée",
        "mom": "mother",
        "dad": "father",
    }
    return aliases.get(relation, relation)


def _second_person_summary(summary: str) -> str:
    text = " ".join(str(summary or "").split())
    if not text:
        return text
    replacements = [
        ("the user's", "your"),
        ("The user's", "Your"),
        ("user's", "your"),
        ("User's", "Your"),
        ("the user", "you"),
        ("The user", "You"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    text = re.sub(r"\bUser\b", "you", text)
    return text

def infer_entity_from_text(text: str) -> dict[str, Any] | None:
    """Infer a simple entity candidate from natural memory text.

    This is deliberately conservative. It does not try to extract payment,
    password, precise address, medical, or other sensitive records. Those can be
    modeled later behind explicit user consent and SaaS policy controls.
    """

    cleaned = _clean_title(text)
    if not cleaned:
        return None
    lowered = cleaned.lower()
    if any(word in lowered for word in ["password", "passcode", "social security", "ssn", "credit card", "debit card", "api key", "secret key"]):
        return None

    # User profile: "my name is Tanner".
    match = re.search(r"\bmy name is\s+([A-Z][A-Za-z0-9_\-']{1,40})\b", cleaned)
    if match:
        name = _clean_title(match.group(1))
        return {
            "name": "user",
            "entity_type": "user",
            "summary": f"User's name is {name}.",
            "aliases": [name],
            "attributes": {"name": name},
            "tags": ["user", "identity"],
            "importance": 4,
            "confidence": 0.86,
        }

    # Relationship: "Kenleigh is my fiancée" or "my fiancée is Kenleigh".
    relationship_words = "lead developer|fiancee|fiance|fiancée|wife|girlfriend|brother|sister|mom|mother|dad|father|friend|coworker|teammate|developer"
    match = re.search(rf"\b{_PERSON_NAME_PATTERN}\s+is\s+my\s+({relationship_words})\b", cleaned, flags=re.IGNORECASE)
    if match:
        name = _clean_title(match.group(1))
        relation = _normalize_relationship_label(match.group(2))
        return {
            "name": name,
            "entity_type": "person",
            "summary": f"{name} is your {relation}.",
            "attributes": {"relationship": relation},
            "relationships": [{"type": relation, "to": "user"}],
            "tags": ["person", "relationship"],
            "importance": 4,
            "confidence": 0.84,
        }
    match = re.search(rf"\bmy\s+({relationship_words})\s+is\s+{_PERSON_NAME_PATTERN}\b", cleaned, flags=re.IGNORECASE)
    if match:
        relation = _normalize_relationship_label(match.group(1))
        name = _clean_title(match.group(2))
        return {
            "name": name,
            "entity_type": "person",
            "summary": f"{name} is your {relation}.",
            "attributes": {"relationship": relation},
            "relationships": [{"type": relation, "to": "user"}],
            "tags": ["person", "relationship"],
            "importance": 4,
            "confidence": 0.84,
        }

    # Pets: "my dog Scout is a golden doodle" or "Scout is my dog".
    match = re.search(r"\bmy\s+(dog|cat|pet)\s+([A-Z][A-Za-z0-9_\-']{1,40})(?:\s+is\s+(?:a|an)?\s*([^.;!?]+))?", cleaned, flags=re.IGNORECASE)
    if match:
        species = match.group(1).lower()
        name = _clean_title(match.group(2))
        breed_or_note = _clean_title(match.group(3) or "")
        attributes: dict[str, Any] = {"species": species}
        if breed_or_note:
            attributes["breed_or_note"] = breed_or_note
        return {
            "name": name,
            "entity_type": "pet",
            "summary": f"{name} is your {species}." + (f" {breed_or_note}." if breed_or_note else ""),
            "attributes": attributes,
            "tags": ["pet", species],
            "importance": 4,
            "confidence": 0.83,
        }
    match = re.search(r"\b([A-Z][A-Za-z0-9_\-']{1,40})\s+is\s+my\s+(dog|cat|pet)\b", cleaned, flags=re.IGNORECASE)
    if match:
        name = _clean_title(match.group(1))
        species = match.group(2).lower()
        return {
            "name": name,
            "entity_type": "pet",
            "summary": f"{name} is your {species}.",
            "attributes": {"species": species},
            "tags": ["pet", species],
            "importance": 4,
            "confidence": 0.83,
        }

    # Projects/products: keep Jarvis project history structured.
    match = re.search(r"\b(Jarvis(?:\s+Ultimate)?|[A-Z][A-Za-z0-9_\-']{2,40})\s+(?:project|saas|app|assistant)\b", cleaned)
    if match and any(word in lowered for word in ["project", "saas", "assistant", "patch", "update", "version"]):
        name = _clean_title(match.group(1))
        return {
            "name": name,
            "entity_type": "project",
            "summary": cleaned,
            "aliases": ["Jarvis"] if "jarvis" in name.lower() and name.lower() != "jarvis" else [],
            "attributes": {},
            "tags": ["project", "jarvis" if "jarvis" in lowered else "product"],
            "importance": 5 if "jarvis" in lowered else 3,
            "confidence": 0.78,
        }
    if "jarvis" in lowered and any(word in lowered for word in ["patch", "update", "version", "memory", "agent", "saas"]):
        return {
            "name": "Jarvis Ultimate",
            "entity_type": "project",
            "summary": cleaned,
            "aliases": ["Jarvis"],
            "attributes": {},
            "tags": ["project", "jarvis"],
            "importance": 5,
            "confidence": 0.8,
        }

    # Apps/tools: "my main music app is Spotify".
    match = re.search(r"\bmy\s+(?:main\s+|default\s+|favorite\s+)?([a-zA-Z0-9_\- ]{2,30})\s+(?:app|tool|software|program)\s+is\s+([A-Z][A-Za-z0-9_\- ]{1,40})\b", cleaned, flags=re.IGNORECASE)
    if match:
        role = normalize_text(match.group(1)).replace(" ", "_")
        name = _clean_title(match.group(2))
        return {
            "name": name,
            "entity_type": "app",
            "summary": f"{name} is your {role.replace('_', ' ')} app.",
            "attributes": {"role": role},
            "tags": ["app", role],
            "importance": 3,
            "confidence": 0.78,
        }

    # Vehicles: "my car is a 2013 Ford Fusion Hybrid SE".
    match = re.search(r"\bmy\s+(car|truck|vehicle)\s+is\s+(?:a\s+|an\s+)?((?:19|20)\d{2})?\s*([^.;!?]+)", cleaned, flags=re.IGNORECASE)
    if match:
        kind = match.group(1).lower()
        year = _clean_title(match.group(2) or "")
        model = _clean_title(match.group(3))
        name = " ".join(part for part in [year, model] if part).strip() or kind
        attributes = {"kind": kind}
        if year:
            attributes["year"] = year
        if model:
            attributes["model"] = model
        return {
            "name": name,
            "entity_type": "vehicle",
            "summary": f"Your {kind} is {name}.",
            "attributes": attributes,
            "tags": ["vehicle", kind],
            "importance": 3,
            "confidence": 0.75,
        }

    # Devices: "my laptop is an RTX..." or "my monitor is...".
    match = re.search(r"\bmy\s+(desktop|laptop|phone|monitor|computer|pc)\s+is\s+(?:a\s+|an\s+)?([^.;!?]+)", cleaned, flags=re.IGNORECASE)
    if match:
        kind = match.group(1).lower()
        detail = _clean_title(match.group(2))
        name = f"{kind.title()}"
        return {
            "name": name,
            "entity_type": "device",
            "summary": f"Your {kind} is {detail}.",
            "attributes": {"kind": kind, "details": detail},
            "tags": ["device", kind],
            "importance": 3,
            "confidence": 0.72,
        }

    return None

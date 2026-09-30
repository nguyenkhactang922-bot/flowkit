"""Canonical dialogue, setup/payoff and screenplay realization for IMP-026.

Authority boundaries:
- DialogueIntent owns communicative/subtext intent, not character/story truth.
- SetupPayoffLink owns ledger linkage/status, not setup/payoff narrative content.
- ScreenplayScene and FullScreenplay are realization artifacts over accepted
  canonical Scene/SceneDramaticBeat truth.
- Legacy prompt/provider/runtime state is never canonical authority here.
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .character_state import (
    CharacterEpistemicState,
    CharacterKnowledgeState,
    CharacterModelVersion,
    RelationshipState,
    character_knowledge_logical_id,
    character_model_logical_id,
)
from .invalidation import (
    DependencyGraphRepository,
    InvalidationRecord,
    InvalidationRepository,
)
from .entity import EntityKind, EntityVersion
from .narrative_hierarchy import (
    Scene as CanonicalScene,
    SceneBreakdownManifest,
    SceneDramaticBeat,
    scene_breakdown_manifest_logical_id,
    scene_dramatic_beat_logical_id,
    scene_logical_id,
)
from .primitives import (
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .story_core import (
    CausalStoryGraph,
    StoryGraphEdgeKind,
    StoryGraphNodeKind,
    story_graph_logical_id,
)
from .versioning import CurrentPointerNotFound, CurrentVersionPointer, VersionRepository


_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class ScreenplayRealizationError(ValueError):
    """Base error for IMP-026 canonical realization boundaries."""


class ScreenplayRealizationGateBlocked(ScreenplayRealizationError):
    """Raised when exact-version, knowledge or realization gates fail closed."""


class ScreenplayRealizationIdentityError(ScreenplayRealizationError):
    """Raised when identity/provenance crosses canonical ownership."""


class SetupPayoffStatus(str, Enum):
    PLANTED = "PLANTED"
    DEVELOPING = "DEVELOPING"
    PAID = "PAID"
    INTENTIONALLY_OPEN = "INTENTIONALLY_OPEN"
    BROKEN = "BROKEN"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _optional_trimmed(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _trimmed(value, label)


def _key(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if not _KEY_RE.fullmatch(value):
        raise ValueError(
            f"{label} must use only letters, digits, '.', '_' or '-'"
        )
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return (ref.logical_id.root, ref.version_id.root)


def _active_profile_id(project_id: LogicalId) -> LogicalId:
    return LogicalId(f"active-profile:{project_id.root}")


def _is_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
) -> bool:
    base = f"{prefix}{project_id.root}"
    root = ref.logical_id.root
    return root == base or root.startswith(base + ":")


def _require_project_scoped(
    ref: VersionRef,
    *,
    prefix: str,
    project_id: LogicalId,
    label: str,
) -> None:
    if not _is_project_scoped(ref, prefix=prefix, project_id=project_id):
        raise ValueError(f"{label} must belong to the same project")


def _require_exact_ref(ref: VersionRef, expected: LogicalId, label: str) -> None:
    if ref.logical_id != expected:
        raise ValueError(f"{label} must reference canonical object for same project")


def dialogue_intent_logical_id(
    project_id: LogicalId,
    scene_key: str,
    beat_key: str,
    intent_key: str,
) -> LogicalId:
    return LogicalId(
        "dialogue-intent:"
        f"{project_id.root}:{_key(scene_key, 'scene_key')}:"
        f"{_key(beat_key, 'beat_key')}:{_key(intent_key, 'intent_key')}"
    )


def setup_payoff_link_logical_id(
    project_id: LogicalId,
    link_key: str,
) -> LogicalId:
    return LogicalId(
        f"setup-payoff-link:{project_id.root}:{_key(link_key, 'link_key')}"
    )


def screenplay_scene_logical_id(
    project_id: LogicalId,
    scene_key: str,
) -> LogicalId:
    return LogicalId(
        f"screenplay-scene:{project_id.root}:{_key(scene_key, 'scene_key')}"
    )


def screenplay_logical_id(
    project_id: LogicalId,
    screenplay_key: str,
) -> LogicalId:
    return LogicalId(
        f"screenplay:{project_id.root}:{_key(screenplay_key, 'screenplay_key')}"
    )


class DialogueIntent(BaseModel):
    """Provider-neutral communicative intent constrained by exact knowledge state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    scene_key: str
    beat_key: str
    intent_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    scene_dramatic_beat_ref: VersionRef
    speaker_character_ref: VersionRef
    character_model_ref: VersionRef
    knowledge_state_ref: VersionRef
    relationship_refs: tuple[VersionRef, ...] = ()

    communicative_goal: str
    surface_intent: str
    subtext: str
    tactic: str
    disclosed_claim_keys: tuple[str, ...] = ()
    withheld_claim_keys: tuple[str, ...] = ()
    audience_effect: str

    information_discipline_verdict: GateVerdict = GateVerdict.PASS
    subtext_verdict: GateVerdict = GateVerdict.PASS
    voice_verdict: GateVerdict = GateVerdict.PASS

    @field_validator("scene_key", "beat_key", "intent_key")
    @classmethod
    def validate_keys(cls, value: str, info) -> str:
        return _key(value, info.field_name)

    @field_validator(
        "communicative_goal",
        "surface_intent",
        "subtext",
        "tactic",
        "audience_effect",
    )
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("disclosed_claim_keys", "withheld_claim_keys")
    @classmethod
    def normalize_claim_keys(
        cls,
        values: tuple[str, ...],
        info,
    ) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _key(value, info.field_name)
            if item not in result:
                result.append(item)
        return tuple(result)

    @model_validator(mode="after")
    def validate_authority(self) -> "DialogueIntent":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.scene_ref,
            scene_logical_id(self.project_id, self.scene_key),
            "scene_ref",
        )
        _require_exact_ref(
            self.scene_dramatic_beat_ref,
            scene_dramatic_beat_logical_id(
                self.project_id,
                self.scene_key,
                self.beat_key,
            ),
            "scene_dramatic_beat_ref",
        )
        _require_exact_ref(
            self.character_model_ref,
            character_model_logical_id(self.speaker_character_ref.logical_id),
            "character_model_ref",
        )
        _require_exact_ref(
            self.knowledge_state_ref,
            character_knowledge_logical_id(self.speaker_character_ref.logical_id),
            "knowledge_state_ref",
        )
        for ref in self.relationship_refs:
            _require_project_scoped(
                ref,
                prefix="relationship:",
                project_id=self.project_id,
                label="relationship_refs",
            )
        if set(self.disclosed_claim_keys) & set(self.withheld_claim_keys):
            raise ValueError(
                "DialogueIntent claim cannot be both disclosed and withheld"
            )
        if not (
            self.disclosed_claim_keys
            or self.withheld_claim_keys
            or self.communicative_goal
        ):
            raise ValueError("DialogueIntent requires an explicit communicative intent")
        if any(
            verdict is not GateVerdict.PASS
            for verdict in (
                self.information_discipline_verdict,
                self.subtext_verdict,
                self.voice_verdict,
            )
        ):
            raise ValueError(
                "persisted DialogueIntent must pass information/subtext/voice gates"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return dialogue_intent_logical_id(
            self.project_id,
            self.scene_key,
            self.beat_key,
            self.intent_key,
        )

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(
                role="scene_dramatic_beat",
                source=self.scene_dramatic_beat_ref,
            ),
            SourceVersionBinding(
                role="speaker_character",
                source=self.speaker_character_ref,
            ),
            SourceVersionBinding(
                role="character_model",
                source=self.character_model_ref,
            ),
            SourceVersionBinding(
                role="knowledge_state",
                source=self.knowledge_state_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"relationship_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.relationship_refs)
        )
        return tuple(values)


class SetupPayoffLink(BaseModel):
    """Canonical ledger link over accepted narrative refs; owns no narrative text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    link_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    story_graph_ref: VersionRef
    setup_ref: VersionRef
    setup_graph_node_id: str
    payoff_ref: VersionRef | None = None
    payoff_graph_node_id: str | None = None
    status: SetupPayoffStatus
    intentional_open_reason: str | None = None
    broken_reason: str | None = None

    @field_validator("link_key")
    @classmethod
    def validate_link_key(cls, value: str) -> str:
        return _key(value, "link_key")

    @field_validator("setup_graph_node_id")
    @classmethod
    def validate_setup_graph_node_id(cls, value: str) -> str:
        return _trimmed(value, "setup_graph_node_id")

    @field_validator(
        "payoff_graph_node_id",
        "intentional_open_reason",
        "broken_reason",
    )
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return _optional_trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_link(self) -> "SetupPayoffLink":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.story_graph_ref,
            story_graph_logical_id(self.project_id),
            "story_graph_ref",
        )
        self._validate_endpoint(self.setup_ref, "setup_ref")
        if self.payoff_ref is not None:
            self._validate_endpoint(self.payoff_ref, "payoff_ref")
            if self.payoff_ref == self.setup_ref:
                raise ValueError("setup_ref and payoff_ref must be different")
        if (self.payoff_ref is None) != (self.payoff_graph_node_id is None):
            raise ValueError(
                "payoff_ref and payoff_graph_node_id must be present together"
            )
        if self.status is SetupPayoffStatus.PAID and (
            self.payoff_ref is None or self.payoff_graph_node_id is None
        ):
            raise ValueError(
                "PAID SetupPayoffLink requires payoff_ref and payoff_graph_node_id"
            )
        if self.status in {
            SetupPayoffStatus.PLANTED,
            SetupPayoffStatus.INTENTIONALLY_OPEN,
        } and self.payoff_ref is not None:
            raise ValueError(
                f"{self.status.value} SetupPayoffLink cannot already bind a payoff"
            )
        if (
            self.status is SetupPayoffStatus.INTENTIONALLY_OPEN
            and self.intentional_open_reason is None
        ):
            raise ValueError(
                "INTENTIONALLY_OPEN SetupPayoffLink requires intentional_open_reason"
            )
        if self.status is SetupPayoffStatus.BROKEN and self.broken_reason is None:
            raise ValueError("BROKEN SetupPayoffLink requires broken_reason")
        return self

    def _validate_endpoint(self, ref: VersionRef, label: str) -> None:
        if ref.logical_id.root.startswith("scene-dramatic-beat:"):
            _require_project_scoped(
                ref,
                prefix="scene-dramatic-beat:",
                project_id=self.project_id,
                label=label,
            )
            return
        if ref.logical_id.root.startswith("scene:"):
            _require_project_scoped(
                ref,
                prefix="scene:",
                project_id=self.project_id,
                label=label,
            )
            return
        raise ValueError(
            f"{label} must reference canonical Scene or SceneDramaticBeat"
        )

    @property
    def logical_id(self) -> LogicalId:
        return setup_payoff_link_logical_id(self.project_id, self.link_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(
                role="causal_story_graph",
                source=self.story_graph_ref,
            ),
            SourceVersionBinding(role="setup", source=self.setup_ref),
        ]
        if self.payoff_ref is not None:
            values.append(
                SourceVersionBinding(role="payoff", source=self.payoff_ref)
            )
        return tuple(values)


class ScreenplayDialogueLine(BaseModel):
    """One realized line bound to DialogueIntent; line is not narrative truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    line_id: str
    dialogue_intent_ref: VersionRef
    speaker_character_ref: VersionRef
    text: str
    realized_claim_keys: tuple[str, ...] = ()

    @field_validator("line_id")
    @classmethod
    def validate_line_id(cls, value: str) -> str:
        return _key(value, "line_id")

    @field_validator("text")
    @classmethod
    def validate_line_text(cls, value: str) -> str:
        return _trimmed(value, "text")

    @field_validator("realized_claim_keys")
    @classmethod
    def normalize_claim_keys(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _key(value, "realized_claim_keys")
            if item not in result:
                result.append(item)
        return tuple(result)

    @model_validator(mode="after")
    def validate_intent_ref(self) -> "ScreenplayDialogueLine":
        if not self.dialogue_intent_ref.logical_id.root.startswith(
            "dialogue-intent:"
        ):
            raise ValueError(
                "dialogue_intent_ref must reference canonical DialogueIntent"
            )
        return self


class ScreenplayScene(BaseModel):
    """Versioned screenplay realization for one canonical Scene."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    scene_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    scene_ref: VersionRef
    scene_breakdown_manifest_ref: VersionRef
    scene_dramatic_beat_refs: tuple[VersionRef, ...] = Field(min_length=1)
    dialogue_intent_refs: tuple[VersionRef, ...] = ()
    setup_payoff_refs: tuple[VersionRef, ...] = ()

    slugline: str
    action_blocks: tuple[str, ...] = Field(min_length=1)
    dialogue_lines: tuple[ScreenplayDialogueLine, ...] = ()
    noncanonical_texture_notes: tuple[str, ...] = ()

    scene_intent_fidelity_verdict: GateVerdict = GateVerdict.PASS
    knowledge_discipline_verdict: GateVerdict = GateVerdict.PASS
    setup_payoff_verdict: GateVerdict = GateVerdict.PASS

    @field_validator("scene_key")
    @classmethod
    def validate_scene_key(cls, value: str) -> str:
        return _key(value, "scene_key")

    @field_validator("slugline")
    @classmethod
    def validate_slugline(cls, value: str) -> str:
        return _trimmed(value, "slugline")

    @field_validator("action_blocks", "noncanonical_texture_notes")
    @classmethod
    def normalize_text_groups(
        cls,
        values: tuple[str, ...],
        info,
    ) -> tuple[str, ...]:
        result: list[str] = []
        for value in values:
            item = _trimmed(value, info.field_name)
            if item not in result:
                result.append(item)
        return tuple(result)

    @model_validator(mode="after")
    def validate_realization(self) -> "ScreenplayScene":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        _require_exact_ref(
            self.scene_ref,
            scene_logical_id(self.project_id, self.scene_key),
            "scene_ref",
        )
        _require_exact_ref(
            self.scene_breakdown_manifest_ref,
            scene_breakdown_manifest_logical_id(
                self.project_id,
                self.scene_key,
            ),
            "scene_breakdown_manifest_ref",
        )
        for ref in self.scene_dramatic_beat_refs:
            _require_project_scoped(
                ref,
                prefix="scene-dramatic-beat:",
                project_id=self.project_id,
                label="scene_dramatic_beat_refs",
            )
        for ref in self.dialogue_intent_refs:
            _require_project_scoped(
                ref,
                prefix="dialogue-intent:",
                project_id=self.project_id,
                label="dialogue_intent_refs",
            )
        for ref in self.setup_payoff_refs:
            _require_project_scoped(
                ref,
                prefix="setup-payoff-link:",
                project_id=self.project_id,
                label="setup_payoff_refs",
            )
        for label, refs in (
            ("scene_dramatic_beat_refs", self.scene_dramatic_beat_refs),
            ("dialogue_intent_refs", self.dialogue_intent_refs),
            ("setup_payoff_refs", self.setup_payoff_refs),
        ):
            keys = [_ref_key(ref) for ref in refs]
            if len(keys) != len(set(keys)):
                raise ValueError(f"{label} must not contain duplicate refs")
        line_ids = [line.line_id for line in self.dialogue_lines]
        if len(line_ids) != len(set(line_ids)):
            raise ValueError("ScreenplayScene line_id values must be unique")
        allowed_intents = {_ref_key(ref) for ref in self.dialogue_intent_refs}
        for line in self.dialogue_lines:
            if _ref_key(line.dialogue_intent_ref) not in allowed_intents:
                raise ValueError(
                    "ScreenplayDialogueLine must bind a declared DialogueIntent"
                )
        if any(
            verdict is not GateVerdict.PASS
            for verdict in (
                self.scene_intent_fidelity_verdict,
                self.knowledge_discipline_verdict,
                self.setup_payoff_verdict,
            )
        ):
            raise ValueError(
                "persisted ScreenplayScene must pass fidelity/knowledge/setup-payoff gates"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return screenplay_scene_logical_id(self.project_id, self.scene_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            ),
            SourceVersionBinding(role="scene", source=self.scene_ref),
            SourceVersionBinding(
                role="scene_breakdown_manifest",
                source=self.scene_breakdown_manifest_ref,
            ),
        ]
        values.extend(
            SourceVersionBinding(
                role=f"scene_dramatic_beat_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.scene_dramatic_beat_refs)
        )
        values.extend(
            SourceVersionBinding(
                role=f"dialogue_intent_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.dialogue_intent_refs)
        )
        values.extend(
            SourceVersionBinding(
                role=f"setup_payoff_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.setup_payoff_refs)
        )
        return tuple(values)


class ScreenplaySceneEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    order_index: int = Field(ge=0)
    scene_ref: VersionRef
    screenplay_scene_ref: VersionRef

    @model_validator(mode="after")
    def validate_ref(self) -> "ScreenplaySceneEntry":
        if not self.scene_ref.logical_id.root.startswith("scene:"):
            raise ValueError("scene_ref must reference canonical Scene")
        if not self.screenplay_scene_ref.logical_id.root.startswith(
            "screenplay-scene:"
        ):
            raise ValueError(
                "screenplay_scene_ref must reference canonical ScreenplayScene realization"
            )
        return self


class FullScreenplay(BaseModel):
    """Assembled versioned screenplay artifact over ScreenplayScene realizations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    project_id: LogicalId
    screenplay_key: str
    version_id: VersionId
    active_profile_ref: VersionRef
    entries: tuple[ScreenplaySceneEntry, ...] = Field(min_length=1)
    setup_payoff_refs: tuple[VersionRef, ...] = ()
    assembled_text: str
    realization_verdict: GateVerdict = GateVerdict.PASS
    continuity_verdict: GateVerdict = GateVerdict.PASS
    setup_payoff_verdict: GateVerdict = GateVerdict.PASS

    @field_validator("screenplay_key")
    @classmethod
    def validate_screenplay_key(cls, value: str) -> str:
        return _key(value, "screenplay_key")

    @field_validator("assembled_text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        return _trimmed(value, "assembled_text")

    @model_validator(mode="after")
    def validate_screenplay(self) -> "FullScreenplay":
        _require_exact_ref(
            self.active_profile_ref,
            _active_profile_id(self.project_id),
            "active_profile_ref",
        )
        indexes = [entry.order_index for entry in self.entries]
        if indexes != list(range(len(self.entries))):
            raise ValueError("FullScreenplay order indexes must be contiguous")
        refs = [_ref_key(entry.screenplay_scene_ref) for entry in self.entries]
        if len(refs) != len(set(refs)):
            raise ValueError("FullScreenplay cannot duplicate ScreenplayScene refs")
        for entry in self.entries:
            _require_project_scoped(
                entry.scene_ref,
                prefix="scene:",
                project_id=self.project_id,
                label="scene_ref",
            )
            _require_project_scoped(
                entry.screenplay_scene_ref,
                prefix="screenplay-scene:",
                project_id=self.project_id,
                label="screenplay_scene_ref",
            )
        for ref in self.setup_payoff_refs:
            _require_project_scoped(
                ref,
                prefix="setup-payoff-link:",
                project_id=self.project_id,
                label="setup_payoff_refs",
            )
        setup_keys = [_ref_key(ref) for ref in self.setup_payoff_refs]
        if len(setup_keys) != len(set(setup_keys)):
            raise ValueError("FullScreenplay setup_payoff_refs must be unique")
        if any(
            verdict is not GateVerdict.PASS
            for verdict in (
                self.realization_verdict,
                self.continuity_verdict,
                self.setup_payoff_verdict,
            )
        ):
            raise ValueError(
                "persisted FullScreenplay must pass realization/continuity/setup-payoff gates"
            )
        return self

    @property
    def logical_id(self) -> LogicalId:
        return screenplay_logical_id(self.project_id, self.screenplay_key)

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.logical_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values = [
            SourceVersionBinding(
                role="active_production_profile",
                source=self.active_profile_ref,
            )
        ]
        for entry in self.entries:
            values.append(
                SourceVersionBinding(
                    role=f"scene_{entry.order_index:03d}",
                    source=entry.scene_ref,
                )
            )
            values.append(
                SourceVersionBinding(
                    role=f"screenplay_scene_{entry.order_index:03d}",
                    source=entry.screenplay_scene_ref,
                )
            )
        values.extend(
            SourceVersionBinding(
                role=f"setup_payoff_{index:03d}",
                source=ref,
            )
            for index, ref in enumerate(self.setup_payoff_refs)
        )
        return tuple(values)


ScreenplayValue: TypeAlias = (
    DialogueIntent | SetupPayoffLink | ScreenplayScene | FullScreenplay
)


class ScreenplayArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: ScreenplayValue

    @model_validator(mode="after")
    def validate_artifact(self) -> "ScreenplayArtifact":
        if self.metadata.logical_id != self.value.logical_id:
            raise ValueError("screenplay artifact logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("screenplay artifact version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError(
                "screenplay artifact provenance must exactly bind declared sources"
            )
        if self.metadata.provenance.rule_version != self.value.active_profile_ref:
            raise ValueError(
                "screenplay provenance rule_version must pin ActiveProductionProfile"
            )
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


def build_screenplay_provenance(
    value: ScreenplayValue,
    *,
    actor_ref: str,
    reason: str,
    recorded_at: datetime,
    source_refs: tuple[str, ...] = (),
    correlation_id: str | None = None,
) -> Provenance:
    return Provenance(
        source_versions=value.source_bindings(),
        source_refs=source_refs,
        actor_ref=actor_ref,
        reason=reason,
        recorded_at=recorded_at,
        rule_version=value.active_profile_ref,
        correlation_id=correlation_id,
    )


class ScreenplayRealizationRepository:
    """Immutable IMP-026 repository over shared Studio version/dependency stores."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, self.graph)

    async def create_dialogue_intent(
        self,
        *,
        value: DialogueIntent,
        provenance: Provenance,
        created_at: datetime,
    ) -> ScreenplayArtifact:
        await self._assert_dialogue_intent_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_dialogue_intent(
        self,
        *,
        value: DialogueIntent,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ScreenplayArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_dialogue_intent_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="DialogueIntent",
            cause="DialogueIntent realization revision",
            scope="dialogue_intent_descendants",
            repair=(
                "Re-realize dependency-reachable screenplay lines/scenes only; "
                "canonical Scene/SceneDramaticBeat/character truth remains unchanged."
            ),
        )

    async def create_setup_payoff_link(
        self,
        *,
        value: SetupPayoffLink,
        provenance: Provenance,
        created_at: datetime,
    ) -> ScreenplayArtifact:
        await self._assert_setup_payoff_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_setup_payoff_link(
        self,
        *,
        value: SetupPayoffLink,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ScreenplayArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_setup_payoff_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="SetupPayoffLink",
            cause="SetupPayoffLink ledger revision",
            scope="setup_payoff_descendants",
            repair=(
                "Re-evaluate dependency-reachable screenplay realization/QA consumers; "
                "do not rewrite canonical narrative endpoints."
            ),
        )

    async def create_screenplay_scene(
        self,
        *,
        value: ScreenplayScene,
        provenance: Provenance,
        created_at: datetime,
    ) -> ScreenplayArtifact:
        await self._assert_screenplay_scene_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_screenplay_scene(
        self,
        *,
        value: ScreenplayScene,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ScreenplayArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_screenplay_scene_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="ScreenplayScene",
            cause="ScreenplayScene realization revision",
            scope="screenplay_scene_descendants",
            repair=(
                "Reassemble dependency-reachable FullScreenplay/QA descendants only; "
                "accepted Scene/Beat truth remains unchanged."
            ),
        )

    async def create_full_screenplay(
        self,
        *,
        value: FullScreenplay,
        provenance: Provenance,
        created_at: datetime,
    ) -> ScreenplayArtifact:
        await self._assert_full_screenplay_inputs(value)
        return await self._create_approved(value, provenance, created_at)

    async def revise_full_screenplay(
        self,
        *,
        value: FullScreenplay,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
    ) -> tuple[ScreenplayArtifact, tuple[InvalidationRecord, ...]]:
        await self._assert_full_screenplay_inputs(value)
        return await self._revise_approved(
            value=value,
            predecessor=predecessor,
            provenance=provenance,
            created_at=created_at,
            expected_revision=expected_revision,
            label="FullScreenplay",
            cause="FullScreenplay realization revision",
            scope="full_screenplay_descendants",
            repair=(
                "Re-run screenplay-quality/lock/directing descendants that consumed "
                "the previous screenplay version; upstream truth is preserved."
            ),
        )

    async def get_dialogue_intent(
        self,
        ref: VersionRef,
    ) -> ScreenplayArtifact | None:
        return await self._get_typed(ref, DialogueIntent, "dialogue-intent:")

    async def get_setup_payoff_link(
        self,
        ref: VersionRef,
    ) -> ScreenplayArtifact | None:
        return await self._get_typed(ref, SetupPayoffLink, "setup-payoff-link:")

    async def get_screenplay_scene(
        self,
        ref: VersionRef,
    ) -> ScreenplayArtifact | None:
        return await self._get_typed(ref, ScreenplayScene, "screenplay-scene:")

    async def get_full_screenplay(
        self,
        ref: VersionRef,
    ) -> ScreenplayArtifact | None:
        return await self._get_typed(ref, FullScreenplay, "screenplay:")

    async def trace_ancestors(self, ref: VersionRef):
        return tuple(await self.graph.ancestors(ref))

    async def trace_descendants(self, ref: VersionRef):
        return tuple(await self.graph.descendants(ref))

    async def _create_approved(
        self,
        value: ScreenplayValue,
        provenance: Provenance,
        created_at: datetime,
    ) -> ScreenplayArtifact:
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, None)
        stored = await self.versions.create_initial(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            status=LifecycleState.DRAFT,
        )
        materialized = ScreenplayArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=0,
        )
        return materialized

    async def _revise_approved(
        self,
        *,
        value: ScreenplayValue,
        predecessor: VersionRef,
        provenance: Provenance,
        created_at: datetime,
        expected_revision: int,
        label: str,
        cause: str,
        scope: str,
        repair: str,
    ) -> tuple[ScreenplayArtifact, tuple[InvalidationRecord, ...]]:
        if predecessor.logical_id != value.logical_id:
            raise ScreenplayRealizationIdentityError(
                f"{label} revision must preserve logical identity"
            )
        await self._assert_current(
            predecessor,
            f"{label} revision predecessor",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        self._assert_provenance(value, provenance)
        artifact = self._artifact(value, provenance, created_at, predecessor)
        stored = await self.versions.create_successor(
            metadata=artifact.metadata,
            payload=value.model_dump(mode="json"),
            supersession_reason=provenance.reason,
        )
        materialized = ScreenplayArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(materialized)
        await self.versions.update_current(
            logical_id=value.logical_id,
            version_id=value.version_id,
            status=LifecycleState.APPROVED,
            expected_revision=expected_revision,
        )
        records = await self.invalidations.create_for_change(
            cause=cause,
            source_old=predecessor,
            source_new=materialized.ref,
            provenance=provenance,
            scope=scope,
            repair_or_recompute_requirement=repair,
        )
        return materialized, tuple(records)

    async def _get_typed(
        self,
        ref: VersionRef,
        model,
        prefix: str,
    ) -> ScreenplayArtifact | None:
        if not ref.logical_id.root.startswith(prefix):
            raise ScreenplayRealizationIdentityError(
                f"expected {prefix.rstrip(':')} artifact, got {ref.logical_id.root}"
            )
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = model.model_validate(stored.payload)
        return ScreenplayArtifact(metadata=stored.metadata, value=value)

    async def _register_dependencies(
        self,
        artifact: ScreenplayArtifact,
    ) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            if binding.source == artifact.ref:
                continue
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="screenplay_realization_input",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

    async def _assert_dialogue_intent_inputs(
        self,
        value: DialogueIntent,
    ) -> None:
        await self._assert_all_sources_exist(value)
        for ref, label, allowed in (
            (
                value.active_profile_ref,
                "ActiveProductionProfile",
                {LifecycleState.LOCKED},
            ),
            (
                value.scene_ref,
                "Scene",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.scene_dramatic_beat_ref,
                "SceneDramaticBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.speaker_character_ref,
                "speaker EntityVersion",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.character_model_ref,
                "CharacterModelVersion",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
            (
                value.knowledge_state_ref,
                "CharacterKnowledgeState",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            ),
        ):
            await self._assert_current(ref, label, allowed)
        for ref in value.relationship_refs:
            await self._assert_current(
                ref,
                "RelationshipState",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        scene = await self._load(value.scene_ref, CanonicalScene, "Scene")
        beat = await self._load(
            value.scene_dramatic_beat_ref,
            SceneDramaticBeat,
            "SceneDramaticBeat",
        )
        entity = await self._load(
            value.speaker_character_ref,
            EntityVersion,
            "EntityVersion",
        )
        character = await self._load(
            value.character_model_ref,
            CharacterModelVersion,
            "CharacterModelVersion",
        )
        knowledge = await self._load(
            value.knowledge_state_ref,
            CharacterKnowledgeState,
            "CharacterKnowledgeState",
        )
        if beat.scene_ref != value.scene_ref:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent SceneDramaticBeat must belong to exact Scene"
            )
        if (
            scene.active_profile_ref != value.active_profile_ref
            or character.active_profile_ref != value.active_profile_ref
        ):
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent upstream profile lineage mismatch"
            )
        if value.project_id not in entity.project_ids:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent speaker EntityVersion belongs to different project"
            )
        if entity.kind is not EntityKind.CHARACTER:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent speaker must be EntityKind.CHARACTER"
            )
        if character.character_ref != value.speaker_character_ref:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent speaker must match CharacterModelVersion"
            )
        if knowledge.character_ref != value.speaker_character_ref:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent speaker must match CharacterKnowledgeState"
            )
        if (
            character.project_id != value.project_id
            or knowledge.project_id != value.project_id
        ):
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent character/knowledge belongs to different project"
            )
        if value.character_model_ref not in scene.character_refs:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent CharacterModelVersion must be declared by Scene"
            )
        if value.knowledge_state_ref not in scene.knowledge_refs:
            raise ScreenplayRealizationGateBlocked(
                "DialogueIntent CharacterKnowledgeState must be declared by Scene"
            )

        relationship_set = {_ref_key(ref) for ref in scene.relationship_refs}
        for ref in value.relationship_refs:
            if _ref_key(ref) not in relationship_set:
                raise ScreenplayRealizationGateBlocked(
                    "DialogueIntent RelationshipState must be declared by Scene"
                )
            relationship = await self._load(
                ref,
                RelationshipState,
                "RelationshipState",
            )
            if relationship.project_id != value.project_id:
                raise ScreenplayRealizationGateBlocked(
                    "DialogueIntent RelationshipState belongs to different project"
                )
            if not any(
                participant.logical_id
                == value.speaker_character_ref.logical_id
                for participant in relationship.participant_refs
            ):
                raise ScreenplayRealizationGateBlocked(
                    "DialogueIntent relationship must include speaker"
                )

        knowledge_by_key = {item.claim_key: item for item in knowledge.items}
        for claim_key in (
            *value.disclosed_claim_keys,
            *value.withheld_claim_keys,
        ):
            item = knowledge_by_key.get(claim_key)
            if item is None:
                raise ScreenplayRealizationGateBlocked(
                    f"DialogueIntent claim not present in exact knowledge state: {claim_key}"
                )
            if item.character_state is CharacterEpistemicState.UNKNOWN:
                raise ScreenplayRealizationGateBlocked(
                    f"DialogueIntent cannot use unknown character knowledge: {claim_key}"
                )

    async def _assert_setup_payoff_inputs(
        self,
        value: SetupPayoffLink,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.story_graph_ref,
            "CausalStoryGraph",
            {LifecycleState.APPROVED},
        )
        await self._assert_current(
            value.setup_ref,
            "setup narrative endpoint",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        if value.payoff_ref is not None:
            await self._assert_current(
                value.payoff_ref,
                "payoff narrative endpoint",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        graph = await self._load(
            value.story_graph_ref,
            CausalStoryGraph,
            "CausalStoryGraph",
        )
        if graph.active_profile_ref != value.active_profile_ref:
            raise ScreenplayRealizationGateBlocked(
                "SetupPayoffLink StoryGraph profile lineage mismatch"
            )

        nodes = {node.node_id: node for node in graph.nodes}
        setup_node = nodes.get(value.setup_graph_node_id)
        if setup_node is None or setup_node.kind is not StoryGraphNodeKind.SETUP:
            raise ScreenplayRealizationGateBlocked(
                "SetupPayoffLink setup_graph_node_id must reference StoryGraph SETUP node"
            )

        if value.payoff_graph_node_id is not None:
            payoff_node = nodes.get(value.payoff_graph_node_id)
            if payoff_node is None or payoff_node.kind is not StoryGraphNodeKind.PAYOFF:
                raise ScreenplayRealizationGateBlocked(
                    "SetupPayoffLink payoff_graph_node_id must reference StoryGraph PAYOFF node"
                )
            has_payoff_edge = any(
                edge.source_node_id == value.setup_graph_node_id
                and edge.target_node_id == value.payoff_graph_node_id
                and edge.kind is StoryGraphEdgeKind.PAYS_OFF
                for edge in graph.edges
            )
            if (
                value.status is not SetupPayoffStatus.BROKEN
                and not has_payoff_edge
            ):
                raise ScreenplayRealizationGateBlocked(
                    "SetupPayoffLink payoff must trace to setup through StoryGraph PAYS_OFF edge"
                )

        await self._load_narrative_endpoint(value.setup_ref, "setup")
        if value.payoff_ref is not None:
            await self._load_narrative_endpoint(value.payoff_ref, "payoff")

    async def _assert_screenplay_scene_inputs(
        self,
        value: ScreenplayScene,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.scene_ref,
            "Scene",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        await self._assert_current(
            value.scene_breakdown_manifest_ref,
            "SceneBreakdownManifest",
            {LifecycleState.APPROVED, LifecycleState.LOCKED},
        )
        for ref in value.scene_dramatic_beat_refs:
            await self._assert_current(
                ref,
                "SceneDramaticBeat",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.dialogue_intent_refs:
            await self._assert_current(
                ref,
                "DialogueIntent",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.setup_payoff_refs:
            await self._assert_current(
                ref,
                "SetupPayoffLink",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        scene = await self._load(value.scene_ref, CanonicalScene, "Scene")
        breakdown = await self._load(
            value.scene_breakdown_manifest_ref,
            SceneBreakdownManifest,
            "SceneBreakdownManifest",
        )
        if scene.active_profile_ref != value.active_profile_ref:
            raise ScreenplayRealizationGateBlocked(
                "ScreenplayScene Scene profile lineage mismatch"
            )
        if (
            breakdown.active_profile_ref != value.active_profile_ref
            or breakdown.scene_ref != value.scene_ref
        ):
            raise ScreenplayRealizationGateBlocked(
                "ScreenplayScene breakdown manifest lineage mismatch"
            )
        expected_beats = tuple(
            entry.scene_dramatic_beat_ref for entry in breakdown.entries
        )
        if value.scene_dramatic_beat_refs != expected_beats:
            raise ScreenplayRealizationGateBlocked(
                "ScreenplayScene must realize exact SceneBreakdownManifest beat order"
            )

        beat_keys = {_ref_key(ref) for ref in value.scene_dramatic_beat_refs}
        for ref in value.scene_dramatic_beat_refs:
            beat = await self._load(ref, SceneDramaticBeat, "SceneDramaticBeat")
            if beat.scene_ref != value.scene_ref:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene beat belongs to different Scene"
                )

        intent_by_ref: dict[tuple[str, str], DialogueIntent] = {}
        for ref in value.dialogue_intent_refs:
            artifact = await self.get_dialogue_intent(ref)
            if artifact is None:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene DialogueIntent not found"
                )
            intent = artifact.value
            assert isinstance(intent, DialogueIntent)
            if intent.scene_ref != value.scene_ref:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene DialogueIntent belongs to different Scene"
                )
            if _ref_key(intent.scene_dramatic_beat_ref) not in beat_keys:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene DialogueIntent beat is not declared"
                )
            intent_by_ref[_ref_key(ref)] = intent

        for line in value.dialogue_lines:
            intent = intent_by_ref[_ref_key(line.dialogue_intent_ref)]
            if line.speaker_character_ref != intent.speaker_character_ref:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayDialogueLine speaker conflicts with DialogueIntent"
                )
            allowed_claims = set(intent.disclosed_claim_keys)
            if not set(line.realized_claim_keys).issubset(allowed_claims):
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayDialogueLine realizes claim not disclosed by DialogueIntent"
                )

        scope_refs = {_ref_key(value.scene_ref), *beat_keys}
        for ref in value.setup_payoff_refs:
            artifact = await self.get_setup_payoff_link(ref)
            if artifact is None:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene SetupPayoffLink not found"
                )
            link = artifact.value
            assert isinstance(link, SetupPayoffLink)
            if link.status is SetupPayoffStatus.BROKEN:
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene cannot accept BROKEN SetupPayoffLink"
                )
            endpoint_keys = {_ref_key(link.setup_ref)}
            if link.payoff_ref is not None:
                endpoint_keys.add(_ref_key(link.payoff_ref))
            if not endpoint_keys.intersection(scope_refs):
                raise ScreenplayRealizationGateBlocked(
                    "ScreenplayScene SetupPayoffLink does not touch this Scene"
                )

    async def _assert_full_screenplay_inputs(
        self,
        value: FullScreenplay,
    ) -> None:
        await self._assert_all_sources_exist(value)
        await self._assert_current(
            value.active_profile_ref,
            "ActiveProductionProfile",
            {LifecycleState.LOCKED},
        )
        for entry in value.entries:
            await self._assert_current(
                entry.scene_ref,
                "Scene",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
            await self._assert_current(
                entry.screenplay_scene_ref,
                "ScreenplayScene",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )
        for ref in value.setup_payoff_refs:
            await self._assert_current(
                ref,
                "SetupPayoffLink",
                {LifecycleState.APPROVED, LifecycleState.LOCKED},
            )

        canonical_scene_keys: set[tuple[str, str]] = set()
        covered_links: set[tuple[str, str]] = set()
        for entry in value.entries:
            await self._load(entry.scene_ref, CanonicalScene, "Scene")
            artifact = await self.get_screenplay_scene(
                entry.screenplay_scene_ref
            )
            if artifact is None:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay ScreenplayScene not found"
                )
            scene_realization = artifact.value
            assert isinstance(scene_realization, ScreenplayScene)
            if scene_realization.active_profile_ref != value.active_profile_ref:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay ScreenplayScene profile lineage mismatch"
                )
            if scene_realization.scene_ref != entry.scene_ref:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay entry canonical Scene does not match ScreenplayScene realization"
                )
            scene_key = _ref_key(entry.scene_ref)
            if scene_key in canonical_scene_keys:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay cannot realize the same canonical Scene twice"
                )
            canonical_scene_keys.add(scene_key)
            covered_links.update(
                _ref_key(ref) for ref in scene_realization.setup_payoff_refs
            )

        full_link_keys = {_ref_key(ref) for ref in value.setup_payoff_refs}
        if covered_links != full_link_keys:
            raise ScreenplayRealizationGateBlocked(
                "FullScreenplay setup/payoff refs must exactly match links used by its scenes"
            )

        for ref in value.setup_payoff_refs:
            artifact = await self.get_setup_payoff_link(ref)
            if artifact is None:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay SetupPayoffLink not found"
                )
            link = artifact.value
            assert isinstance(link, SetupPayoffLink)
            if link.status is SetupPayoffStatus.BROKEN:
                raise ScreenplayRealizationGateBlocked(
                    "FullScreenplay cannot pass with BROKEN SetupPayoffLink"
                )

    async def _load_narrative_endpoint(self, ref: VersionRef, label: str):
        root = ref.logical_id.root
        if root.startswith("scene-dramatic-beat:"):
            beat = await self._load(ref, SceneDramaticBeat, "SceneDramaticBeat")
            if beat.project_id is None:
                raise ScreenplayRealizationGateBlocked(
                    f"{label} endpoint missing project"
                )
            return beat
        if root.startswith("scene:"):
            scene = await self._load(ref, CanonicalScene, "Scene")
            if scene.project_id is None:
                raise ScreenplayRealizationGateBlocked(
                    f"{label} endpoint missing project"
                )
            return scene
        raise ScreenplayRealizationGateBlocked(
            f"{label} endpoint is not canonical Scene/SceneDramaticBeat"
        )

    async def _assert_all_sources_exist(
        self,
        value: ScreenplayValue,
    ) -> None:
        for binding in value.source_bindings():
            if await self.versions.get_version(binding.source) is None:
                raise ScreenplayRealizationGateBlocked(
                    f"missing exact source {binding.role}="
                    f"{binding.source.logical_id.root}/"
                    f"{binding.source.version_id.root}"
                )

    async def _assert_current(
        self,
        ref: VersionRef,
        label: str,
        allowed: set[LifecycleState],
    ) -> CurrentVersionPointer:
        try:
            pointer = await self.versions.get_current(ref.logical_id)
        except CurrentPointerNotFound as exc:
            raise ScreenplayRealizationGateBlocked(
                f"{label} has no current version"
            ) from exc
        if pointer.version_id != ref.version_id or pointer.status not in allowed:
            raise ScreenplayRealizationGateBlocked(
                f"{label} is not exact current accepted version"
            )
        return pointer

    async def _load(self, ref: VersionRef, model, label: str):
        stored = await self.versions.get_version(ref)
        if stored is None:
            raise ScreenplayRealizationGateBlocked(
                f"{label} exact version not found"
            )
        try:
            return model.model_validate(stored.payload)
        except ValidationError as exc:
            raise ScreenplayRealizationGateBlocked(
                f"{label} payload is not canonical {model.__name__}"
            ) from exc

    @staticmethod
    def _assert_provenance(
        value: ScreenplayValue,
        provenance: Provenance,
    ) -> None:
        if provenance.source_versions != value.source_bindings():
            raise ScreenplayRealizationIdentityError(
                "screenplay provenance must exactly match declared source bindings"
            )
        if provenance.rule_version != value.active_profile_ref:
            raise ScreenplayRealizationIdentityError(
                "screenplay provenance rule_version must pin ActiveProductionProfile"
            )

    @staticmethod
    def _artifact(
        value: ScreenplayValue,
        provenance: Provenance,
        created_at: datetime,
        predecessor: VersionRef | None,
    ) -> ScreenplayArtifact:
        return ScreenplayArtifact(
            metadata=SemanticRecordMetadata(
                logical_id=value.logical_id,
                version_id=value.version_id,
                predecessor=predecessor,
                provenance=provenance,
                created_at=created_at,
            ),
            value=value,
        )

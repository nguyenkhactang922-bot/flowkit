"""IMP-080 legacy import anti-corruption boundary.

This module classifies legacy FlowKit rows into bounded migration evidence.  It
never turns operational Scene rows, prompt prose, media IDs, or provider output
into canonical Story/Scene/Shot truth.  Canonical targets are accepted only
when explicit proof already exists in the owning Studio repository.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from .generation_job import GenerationJobRepository
from .invalidation import DependencyGraphRepository, InvalidationRepository
from .primitives import (
    FindingSeverity,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)
from .shot_planning import ShotPlanningRepository
from .versioning import VersionRepository


_ACCEPTED = {LifecycleState.APPROVED, LifecycleState.LOCKED}
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}$")
_RULE_VERSION = "legacy-import-v1"
_PROMPT_FIELDS = (
    "prompt",
    "image_prompt",
    "video_prompt",
    "transition_prompt",
    "narrator_text",
)
_MEDIA_FIELDS = (
    "media_id",
    "reference_image_url",
    "vertical_image_url",
    "vertical_image_media_id",
    "vertical_video_url",
    "vertical_video_media_id",
    "vertical_upscale_url",
    "vertical_upscale_media_id",
    "horizontal_image_url",
    "horizontal_image_media_id",
    "horizontal_video_url",
    "horizontal_video_media_id",
    "horizontal_upscale_url",
    "horizontal_upscale_media_id",
    "vertical_end_scene_media_id",
    "horizontal_end_scene_media_id",
)
_CHAIN_FIELDS = ("display_order", "parent_scene_id", "chain_type", "source")


class LegacyImportError(RuntimeError):
    """Base IMP-080 legacy import error."""


class LegacyImportIdentityError(LegacyImportError):
    """Raised when persisted mapping identity/evidence conflicts."""


class LegacySourceKind(str, Enum):
    PROJECT = "PROJECT"
    ENTITY = "ENTITY"
    OPERATIONAL_SCENE = "OPERATIONAL_SCENE"
    REQUEST = "REQUEST"
    MEDIA = "MEDIA"


class LegacyImportDisposition(str, Enum):
    SEED_ONLY = "SEED_ONLY"
    DELEGATE_EXISTING_ADAPTER = "DELEGATE_EXISTING_ADAPTER"
    COMPATIBILITY_MAPPED = "COMPATIBILITY_MAPPED"
    LINEAGE_ONLY = "LINEAGE_ONLY"
    NOT_PROVABLE = "NOT_PROVABLE"


class LegacyImportFindingCode(str, Enum):
    PROJECT_STORY_SEED_ONLY = "PROJECT_STORY_SEED_ONLY"
    ENTITY_ADAPTER_REQUIRED = "ENTITY_ADAPTER_REQUIRED"
    OPERATIONAL_SCENE_NOT_CANONICAL_SCENE = "OPERATIONAL_SCENE_NOT_CANONICAL_SCENE"
    PROMPT_PROSE_DERIVATIVE_ONLY = "PROMPT_PROSE_DERIVATIVE_ONLY"
    MEDIA_EXTERNAL_LINEAGE_ONLY = "MEDIA_EXTERNAL_LINEAGE_ONLY"
    EXPLICIT_TARGET_PROOF_REQUIRED = "EXPLICIT_TARGET_PROOF_REQUIRED"
    FORBIDDEN_CANONICAL_TARGET = "FORBIDDEN_CANONICAL_TARGET"
    TARGET_VERSION_MISSING = "TARGET_VERSION_MISSING"
    TARGET_VERSION_NOT_CURRENT_ACCEPTED = "TARGET_VERSION_NOT_CURRENT_ACCEPTED"
    TARGET_PROJECT_MISMATCH = "TARGET_PROJECT_MISMATCH"
    GENERATION_JOB_MISSING = "GENERATION_JOB_MISSING"
    GENERATION_JOB_REVISION_MISMATCH = "GENERATION_JOB_REVISION_MISMATCH"
    GENERATION_JOB_PROJECT_MISMATCH = "GENERATION_JOB_PROJECT_MISMATCH"
    SHOT_JOB_LINEAGE_MISMATCH = "SHOT_JOB_LINEAGE_MISMATCH"
    NO_IMPORTABLE_PROOF = "NO_IMPORTABLE_PROOF"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _token(value: str, label: str) -> str:
    value = _trimmed(value, label)
    if not _TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be an opaque 1-128 character token")
    return value


def _row_mapping(row: Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(row, Mapping):
        data = dict(row)
    elif hasattr(row, "model_dump"):
        data = row.model_dump(mode="json")
    elif hasattr(row, "__dict__"):
        data = dict(vars(row))
    else:
        raise TypeError("legacy row must be mapping/Pydantic/dataclass-like")
    try:
        # Round-trip to reject unserializable opaque runtime objects and produce
        # deterministic source evidence.  The raw payload is intentionally not
        # persisted in canonical Studio storage.
        return json.loads(json.dumps(data, sort_keys=True, ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("legacy row must be deterministically JSON serializable") from exc


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def legacy_import_mapping_logical_id(
    migration_run_id: str,
    source_kind: LegacySourceKind,
    source_id: str,
) -> LogicalId:
    raw = json.dumps(
        {
            "migration_run_id": _token(migration_run_id, "migration_run_id"),
            "source_kind": source_kind.value,
            "source_id": _trimmed(source_id, "source_id"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return LogicalId("legacy-import-mapping:" + hashlib.sha256(raw).hexdigest()[:40])


class LegacySourceEvidence(BaseModel):
    """Redacted/digested evidence for one legacy row; raw prose is not truth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_kind: LegacySourceKind
    source_table: str
    source_id: str
    source_schema_version: str
    payload_sha256: str
    observed_fields: tuple[str, ...]
    has_story_text: bool = False
    has_prompt_prose: bool = False
    has_media_lineage: bool = False
    has_chain_lineage: bool = False

    @field_validator("source_table", "source_id", "source_schema_version")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("payload_sha256")
    @classmethod
    def validate_digest(cls, value: str) -> str:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise ValueError("payload_sha256 must be sha256:<64 lowercase hex>")
        return value

    @field_validator("observed_fields")
    @classmethod
    def validate_observed_fields(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "observed field") for value in values)
        if normalized != tuple(sorted(set(normalized))):
            raise ValueError("observed_fields must be sorted and unique")
        return normalized

    @classmethod
    def from_legacy(
        cls,
        row: Mapping[str, Any] | Any,
        *,
        source_kind: LegacySourceKind,
        source_table: str,
        source_id: str,
        source_schema_version: str,
    ) -> "LegacySourceEvidence":
        data = _row_mapping(row)
        encoded = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        observed = tuple(sorted(key for key, value in data.items() if _present(value)))
        return cls(
            source_kind=source_kind,
            source_table=source_table,
            source_id=source_id,
            source_schema_version=source_schema_version,
            payload_sha256="sha256:" + hashlib.sha256(encoded).hexdigest(),
            observed_fields=observed,
            has_story_text=_present(data.get("story")),
            has_prompt_prose=any(_present(data.get(key)) for key in _PROMPT_FIELDS),
            has_media_lineage=any(_present(data.get(key)) for key in _MEDIA_FIELDS),
            has_chain_lineage=any(_present(data.get(key)) for key in _CHAIN_FIELDS),
        )


class LegacyImportFinding(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: LegacyImportFindingCode
    severity: FindingSeverity
    summary: str
    evidence_fields: tuple[str, ...] = ()

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, value: str) -> str:
        return _trimmed(value, "summary")

    @field_validator("evidence_fields")
    @classmethod
    def validate_fields(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "evidence field") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_fields must not contain duplicates")
        return normalized


class LegacyImportRequest(BaseModel):
    """Ephemeral classification request; legacy raw payload stays outside output."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    migration_run_id: str
    target_schema_version: str
    record_version_id: VersionId
    source: LegacySourceEvidence
    canonical_project_id: LogicalId | None = None
    explicit_target_refs: tuple[VersionRef, ...] = ()
    generation_job_id: LogicalId | None = None
    generation_job_revision: int | None = Field(default=None, ge=0)
    actor_ref: str
    reason: str
    recorded_at: AwareDatetime
    correlation_id: str | None = None
    evidence_refs: tuple[str, ...] = ()
    rule_version: str = _RULE_VERSION

    @field_validator("migration_run_id", "target_schema_version", "rule_version")
    @classmethod
    def validate_tokens(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @field_validator("actor_ref", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "evidence_ref") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_refs must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_targets(self) -> "LegacyImportRequest":
        keys = [(ref.logical_id.root, ref.version_id.root) for ref in self.explicit_target_refs]
        if len(keys) != len(set(keys)):
            raise ValueError("explicit_target_refs must not contain duplicates")
        if (self.generation_job_id is None) != (self.generation_job_revision is None):
            raise ValueError("generation_job_id and generation_job_revision must be supplied together")
        return self


class LegacyImportMappingRecord(BaseModel):
    """Immutable audit evidence for one bounded legacy import classification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mapping_id: LogicalId
    version_id: VersionId
    migration_run_id: str
    target_schema_version: str
    rule_version: str
    source: LegacySourceEvidence
    canonical_project_id: LogicalId | None = None
    disposition: LegacyImportDisposition
    target_refs: tuple[VersionRef, ...] = ()
    generation_job_id: LogicalId | None = None
    generation_job_revision: int | None = Field(default=None, ge=0)
    findings: tuple[LegacyImportFinding, ...] = ()

    @field_validator("migration_run_id", "target_schema_version", "rule_version")
    @classmethod
    def validate_tokens(cls, value: str, info) -> str:
        return _token(value, info.field_name)

    @model_validator(mode="after")
    def validate_mapping(self) -> "LegacyImportMappingRecord":
        expected = legacy_import_mapping_logical_id(
            self.migration_run_id,
            self.source.source_kind,
            self.source.source_id,
        )
        if self.mapping_id != expected:
            raise ValueError("mapping_id does not match migration/source identity")
        target_keys = [(ref.logical_id.root, ref.version_id.root) for ref in self.target_refs]
        if len(target_keys) != len(set(target_keys)):
            raise ValueError("target_refs must not contain duplicates")
        if any(not ref.logical_id.root.startswith("shot-list-item:") for ref in self.target_refs):
            raise ValueError("persisted semantic compatibility targets must be ShotListItem refs")
        if (self.generation_job_id is None) != (self.generation_job_revision is None):
            raise ValueError("persisted GenerationJob proof requires identity + revision")
        has_target = bool(self.target_refs) or self.generation_job_id is not None
        if self.disposition is LegacyImportDisposition.COMPATIBILITY_MAPPED and not has_target:
            raise ValueError("COMPATIBILITY_MAPPED requires explicit canonical/execution proof")
        if self.disposition is LegacyImportDisposition.NOT_PROVABLE:
            if has_target:
                raise ValueError("NOT_PROVABLE cannot persist an accepted target")
            if not self.findings:
                raise ValueError("NOT_PROVABLE requires at least one finding")
        if self.disposition is LegacyImportDisposition.SEED_ONLY:
            if self.source.source_kind is not LegacySourceKind.PROJECT or has_target:
                raise ValueError("SEED_ONLY is project-only and cannot carry target refs")
        if self.disposition is LegacyImportDisposition.DELEGATE_EXISTING_ADAPTER:
            if self.source.source_kind is not LegacySourceKind.ENTITY or has_target:
                raise ValueError("DELEGATE_EXISTING_ADAPTER is entity-only")
        if self.disposition is LegacyImportDisposition.LINEAGE_ONLY and has_target:
            raise ValueError("LINEAGE_ONLY cannot claim canonical target ownership")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.mapping_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        return tuple(
            SourceVersionBinding(role=f"compatibility_shot_{index:03d}", source=ref)
            for index, ref in enumerate(self.target_refs)
        )


class LegacyImportArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: LegacyImportMappingRecord

    @model_validator(mode="after")
    def validate_artifact(self) -> "LegacyImportArtifact":
        if self.metadata.logical_id != self.value.mapping_id:
            raise ValueError("legacy import metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("legacy import metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("legacy import provenance must exactly bind accepted semantic targets")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class LegacyImportAssessment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: LegacyImportArtifact
    invalidation_count: int = Field(default=0, ge=0)


def _finding(
    code: LegacyImportFindingCode,
    severity: FindingSeverity,
    summary: str,
    *fields: str,
) -> LegacyImportFinding:
    return LegacyImportFinding(
        code=code,
        severity=severity,
        summary=summary,
        evidence_fields=tuple(fields),
    )


class LegacyImportAntiCorruptionService:
    """Bounded legacy classifier/persistence boundary; never creates creative truth."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.jobs = GenerationJobRepository(writer)
        self.shots = ShotPlanningRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def assess(self, request: LegacyImportRequest) -> LegacyImportAssessment:
        value = await self._classify(request)
        provenance = self._provenance(request, value)
        artifact, invalidation_count = await self._persist(value, provenance, request.recorded_at)
        return LegacyImportAssessment(
            artifact=artifact,
            invalidation_count=invalidation_count,
        )

    async def get_mapping(self, ref: VersionRef) -> LegacyImportArtifact | None:
        if not ref.logical_id.root.startswith("legacy-import-mapping:"):
            raise LegacyImportIdentityError("expected legacy-import-mapping reference")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = LegacyImportMappingRecord.model_validate(stored.payload)
        return LegacyImportArtifact(metadata=stored.metadata, value=value)

    async def _classify(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        kind = request.source.source_kind
        if kind is LegacySourceKind.PROJECT:
            return self._classify_project(request)
        if kind is LegacySourceKind.ENTITY:
            return self._classify_entity(request)
        if kind is LegacySourceKind.MEDIA:
            return self._classify_media(request)
        if kind is LegacySourceKind.REQUEST:
            return await self._classify_request(request)
        if kind is LegacySourceKind.OPERATIONAL_SCENE:
            return await self._classify_scene(request)
        raise AssertionError(f"unhandled legacy source kind: {kind}")

    def _base(self, request: LegacyImportRequest, **updates: Any) -> LegacyImportMappingRecord:
        return LegacyImportMappingRecord(
            mapping_id=legacy_import_mapping_logical_id(
                request.migration_run_id,
                request.source.source_kind,
                request.source.source_id,
            ),
            version_id=request.record_version_id,
            migration_run_id=request.migration_run_id,
            target_schema_version=request.target_schema_version,
            rule_version=request.rule_version,
            source=request.source,
            canonical_project_id=request.canonical_project_id,
            disposition=updates.pop("disposition"),
            **updates,
        )

    def _classify_project(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        if request.explicit_target_refs or request.generation_job_id is not None:
            return self._not_provable(
                request,
                _finding(
                    LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET,
                    FindingSeverity.BLOCKER,
                    "legacy Project rows cannot directly claim canonical creative targets",
                ),
            )
        if request.source.has_story_text:
            return self._base(
                request,
                disposition=LegacyImportDisposition.SEED_ONLY,
                findings=(
                    _finding(
                        LegacyImportFindingCode.PROJECT_STORY_SEED_ONLY,
                        FindingSeverity.NOTE,
                        "legacy project.story may be retained only as story import/seed evidence",
                        "story",
                    ),
                ),
            )
        return self._not_provable(
            request,
            _finding(
                LegacyImportFindingCode.NO_IMPORTABLE_PROOF,
                FindingSeverity.MAJOR,
                "legacy Project row contains no bounded import proof",
            ),
        )

    def _classify_entity(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        if request.explicit_target_refs or request.generation_job_id is not None:
            return self._not_provable(
                request,
                _finding(
                    LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET,
                    FindingSeverity.BLOCKER,
                    "IMP-080 cannot bypass the existing canonical Entity adapter",
                ),
            )
        return self._base(
            request,
            disposition=LegacyImportDisposition.DELEGATE_EXISTING_ADAPTER,
            findings=(
                _finding(
                    LegacyImportFindingCode.ENTITY_ADAPTER_REQUIRED,
                    FindingSeverity.NOTE,
                    "legacy Entity rows must be imported through the IMP-040 Entity adapter",
                ),
            ),
        )

    def _classify_media(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        if request.explicit_target_refs or request.generation_job_id is not None:
            return self._not_provable(
                request,
                _finding(
                    LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET,
                    FindingSeverity.BLOCKER,
                    "legacy media cannot claim semantic/creative ownership through IMP-080",
                ),
            )
        return self._base(
            request,
            disposition=LegacyImportDisposition.LINEAGE_ONLY,
            findings=(
                _finding(
                    LegacyImportFindingCode.MEDIA_EXTERNAL_LINEAGE_ONLY,
                    FindingSeverity.NOTE,
                    "legacy media/provider identifiers remain external lineage only",
                ),
            ),
        )

    async def _classify_request(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        if request.explicit_target_refs:
            return self._not_provable(
                request,
                _finding(
                    LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET,
                    FindingSeverity.BLOCKER,
                    "legacy request payloads cannot claim semantic Shot/Story targets",
                ),
            )
        job, job_findings = await self._validate_generation_job(request)
        if job is None:
            return self._not_provable(
                request,
                *(job_findings or (
                    _finding(
                        LegacyImportFindingCode.EXPLICIT_TARGET_PROOF_REQUIRED,
                        FindingSeverity.MAJOR,
                        "legacy request requires explicit GenerationJob identity/revision proof",
                    ),
                )),
            )
        return self._base(
            request,
            disposition=LegacyImportDisposition.COMPATIBILITY_MAPPED,
            generation_job_id=job.generation_job_id,
            generation_job_revision=job.revision,
            findings=(),
        )

    async def _classify_scene(self, request: LegacyImportRequest) -> LegacyImportMappingRecord:
        findings: list[LegacyImportFinding] = [
            _finding(
                LegacyImportFindingCode.OPERATIONAL_SCENE_NOT_CANONICAL_SCENE,
                FindingSeverity.NOTE,
                "legacy operational Scene is execution compatibility data, not cinematic Scene truth",
            )
        ]
        if request.source.has_prompt_prose:
            prompt_fields = tuple(field for field in _PROMPT_FIELDS if field in request.source.observed_fields)
            findings.append(
                _finding(
                    LegacyImportFindingCode.PROMPT_PROSE_DERIVATIVE_ONLY,
                    FindingSeverity.NOTE,
                    "legacy prompt prose is derivative evidence and cannot mint narrative/shot-spec truth",
                    *prompt_fields,
                )
            )

        shot_refs, shot_findings = await self._validate_shot_targets(request)
        findings.extend(shot_findings)
        job, job_findings = await self._validate_generation_job(request)
        findings.extend(job_findings)

        if shot_findings or job_findings:
            return self._not_provable(request, *findings)
        if not shot_refs and job is None:
            findings.append(
                _finding(
                    LegacyImportFindingCode.EXPLICIT_TARGET_PROOF_REQUIRED,
                    FindingSeverity.MAJOR,
                    "operational Scene requires explicit existing ShotListItem and/or GenerationJob proof",
                )
            )
            return self._not_provable(request, *findings)
        if job is not None and shot_refs and job.shot_id not in {ref.logical_id for ref in shot_refs}:
            findings.append(
                _finding(
                    LegacyImportFindingCode.SHOT_JOB_LINEAGE_MISMATCH,
                    FindingSeverity.BLOCKER,
                    "GenerationJob shot_id does not match any explicitly mapped ShotListItem",
                )
            )
            return self._not_provable(request, *findings)

        return self._base(
            request,
            disposition=LegacyImportDisposition.COMPATIBILITY_MAPPED,
            target_refs=shot_refs,
            generation_job_id=None if job is None else job.generation_job_id,
            generation_job_revision=None if job is None else job.revision,
            findings=tuple(findings),
        )

    async def _validate_shot_targets(
        self,
        request: LegacyImportRequest,
    ) -> tuple[tuple[VersionRef, ...], tuple[LegacyImportFinding, ...]]:
        if not request.explicit_target_refs:
            return (), ()
        accepted: list[VersionRef] = []
        findings: list[LegacyImportFinding] = []
        for ref in request.explicit_target_refs:
            if not ref.logical_id.root.startswith("shot-list-item:"):
                findings.append(
                    _finding(
                        LegacyImportFindingCode.FORBIDDEN_CANONICAL_TARGET,
                        FindingSeverity.BLOCKER,
                        "legacy mapping may not target cinematic Scene/Beat/FullShotSpec/ShotIR or other creative truth",
                    )
                )
                continue
            try:
                shot_artifact = await self.shots.get_shot_list_item(ref)
            except (ValidationError, ValueError, TypeError):
                shot_artifact = None
            if shot_artifact is None:
                findings.append(
                    _finding(
                        LegacyImportFindingCode.TARGET_VERSION_MISSING,
                        FindingSeverity.BLOCKER,
                        "explicit target is not a valid canonical ShotListItem exact version: "
                        f"{ref.logical_id.root}/{ref.version_id.root}",
                    )
                )
                continue
            pointer = await self.versions.get_current(ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != ref.version_id
                or pointer.status not in _ACCEPTED
            ):
                findings.append(
                    _finding(
                        LegacyImportFindingCode.TARGET_VERSION_NOT_CURRENT_ACCEPTED,
                        FindingSeverity.BLOCKER,
                        "explicit ShotListItem proof must be exact-current and accepted",
                    )
                )
                continue
            if request.canonical_project_id is not None:
                if shot_artifact.value.project_id != request.canonical_project_id:
                    findings.append(
                        _finding(
                            LegacyImportFindingCode.TARGET_PROJECT_MISMATCH,
                            FindingSeverity.BLOCKER,
                            "explicit ShotListItem belongs to a different canonical project",
                        )
                    )
                    continue
            accepted.append(ref)
        if findings:
            return (), tuple(findings)
        return tuple(accepted), ()

    async def _validate_generation_job(self, request: LegacyImportRequest):
        if request.generation_job_id is None:
            return None, ()
        job = await self.jobs.get_job(request.generation_job_id)
        if job is None:
            return None, (
                _finding(
                    LegacyImportFindingCode.GENERATION_JOB_MISSING,
                    FindingSeverity.BLOCKER,
                    "explicit GenerationJob proof does not exist",
                ),
            )
        assert request.generation_job_revision is not None
        if job.revision != request.generation_job_revision:
            return None, (
                _finding(
                    LegacyImportFindingCode.GENERATION_JOB_REVISION_MISMATCH,
                    FindingSeverity.BLOCKER,
                    "explicit GenerationJob proof is stale; exact revision is required",
                ),
            )
        if request.canonical_project_id is not None and job.project_id != request.canonical_project_id:
            return None, (
                _finding(
                    LegacyImportFindingCode.GENERATION_JOB_PROJECT_MISMATCH,
                    FindingSeverity.BLOCKER,
                    "explicit GenerationJob belongs to a different canonical project",
                ),
            )
        return job, ()

    def _not_provable(
        self,
        request: LegacyImportRequest,
        *findings: LegacyImportFinding,
    ) -> LegacyImportMappingRecord:
        return self._base(
            request,
            disposition=LegacyImportDisposition.NOT_PROVABLE,
            findings=tuple(findings),
        )

    def _provenance(
        self,
        request: LegacyImportRequest,
        value: LegacyImportMappingRecord,
    ) -> Provenance:
        source_refs = [
            (
                f"legacy:{value.source.source_kind.value.lower()}:"
                f"{value.source.source_table}:{value.source.source_id}"
                f"@{value.source.source_schema_version}"
            ),
            value.source.payload_sha256,
            f"migration-run:{value.migration_run_id}",
            f"migration-rule:{value.rule_version}",
            f"target-schema:{value.target_schema_version}",
        ]
        if value.generation_job_id is not None:
            source_refs.append(
                f"{value.generation_job_id.root}@revision:{value.generation_job_revision}"
            )
        source_refs.extend(
            f"claimed-target:{ref.logical_id.root}@{ref.version_id.root}"
            for ref in request.explicit_target_refs
            if ref not in value.target_refs
        )
        source_refs.extend(request.evidence_refs)
        return Provenance(
            source_versions=value.source_bindings(),
            source_refs=tuple(dict.fromkeys(source_refs)),
            actor_ref=request.actor_ref,
            reason=request.reason,
            recorded_at=request.recorded_at,
            correlation_id=request.correlation_id,
        )

    async def _persist(
        self,
        value: LegacyImportMappingRecord,
        provenance: Provenance,
        created_at: datetime,
    ) -> tuple[LegacyImportArtifact, int]:
        existing = await self.versions.get_version(value.ref)
        if existing is not None:
            materialized = LegacyImportArtifact(
                metadata=existing.metadata,
                value=LegacyImportMappingRecord.model_validate(existing.payload),
            )
            if materialized.value != value or materialized.metadata.provenance != provenance:
                raise LegacyImportIdentityError(
                    "legacy import exact replay conflicts with persisted mapping evidence"
                )
            return materialized, 0

        pointer = await self.versions.get_current(value.mapping_id)
        metadata = SemanticRecordMetadata(
            logical_id=value.mapping_id,
            version_id=value.version_id,
            provenance=provenance,
            created_at=created_at,
            predecessor=None
            if pointer is None
            else VersionRef(logical_id=value.mapping_id, version_id=pointer.version_id),
        )
        status = (
            LifecycleState.APPROVED
            if value.disposition is LegacyImportDisposition.COMPATIBILITY_MAPPED
            else LifecycleState.REVIEW
        )
        predecessor_ref: VersionRef | None = None
        if pointer is None:
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                status=status,
            )
        else:
            predecessor_ref = VersionRef(
                logical_id=value.mapping_id,
                version_id=pointer.version_id,
            )
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                supersession_reason=provenance.reason,
            )
            await self.versions.update_current(
                logical_id=value.mapping_id,
                version_id=value.version_id,
                status=status,
                expected_revision=pointer.revision,
            )

        artifact = LegacyImportArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)
        invalidation_count = 0
        if predecessor_ref is not None:
            records = await self.invalidations.create_for_change(
                cause="LegacyImportMapping successor",
                source_old=predecessor_ref,
                source_new=artifact.ref,
                provenance=artifact.metadata.provenance,
                scope="legacy_import_mapping_descendants",
                repair_or_recompute_requirement=(
                    "Re-evaluate only consumers that depended on the superseded legacy mapping evidence."
                ),
            )
            invalidation_count = len(records)
        return artifact, invalidation_count

    async def _register_dependencies(self, artifact: LegacyImportArtifact) -> None:
        for binding in artifact.value.source_bindings():
            await self.graph.create_edge(
                source=binding.source,
                dependent=artifact.ref,
                edge_type="legacy_import_target_proof",
                dependency_reason=f"legacy_import_target_proof:{binding.role}",
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

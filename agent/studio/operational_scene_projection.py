"""IMP-081 operational Scene -> execution compatibility projection.

The legacy FlowKit ``scene`` row remains an execution/runtime concept.  This
module never promotes prompt prose, chain state, or media fields into cinematic
Scene/Shot authority.  It materializes a bounded compatibility read model only
when IMP-080 has already proven exact ShotListItem and/or GenerationJob lineage.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .generation_job import GenerationJob, GenerationJobRepository
from .invalidation import DependencyGraphRepository, InvalidationRepository
from .legacy_import import (
    LegacyImportAntiCorruptionService,
    LegacyImportDisposition,
    LegacyImportMappingRecord,
    LegacySourceEvidence,
    LegacySourceKind,
)
from .primitives import (
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


class OperationalSceneProjectionError(RuntimeError):
    """Base IMP-081 compatibility projection error."""


class OperationalSceneProjectionGateBlocked(OperationalSceneProjectionError):
    """Raised when legacy execution evidence cannot be trusted exactly."""


class OperationalSceneProjectionIdentityError(OperationalSceneProjectionError):
    """Raised when deterministic projection identity conflicts with persisted truth."""


class LegacyOrientation(str, Enum):
    VERTICAL = "VERTICAL"
    HORIZONTAL = "HORIZONTAL"


class LegacyMediaRole(str, Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    UPSCALE = "UPSCALE"
    END_FRAME = "END_FRAME"


def _trimmed(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _optional_trimmed(value: Any, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string when present")
    if not value.strip():
        return None
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    return value


def _ref_key(ref: VersionRef) -> tuple[str, str]:
    return ref.logical_id.root, ref.version_id.root


def operational_scene_projection_logical_id(
    migration_run_id: str,
    legacy_scene_id: str,
) -> LogicalId:
    raw = json.dumps(
        {
            "migration_run_id": _trimmed(migration_run_id, "migration_run_id"),
            "legacy_scene_id": _trimmed(legacy_scene_id, "legacy_scene_id"),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return LogicalId("legacy-scene-execution-projection:" + hashlib.sha256(raw).hexdigest()[:40])


class LegacyMediaBinding(BaseModel):
    """Opaque legacy execution media locator; never semantic/creative authority."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    orientation: LegacyOrientation
    role: LegacyMediaRole
    media_id: str | None = None
    output_url: str | None = None
    status: str | None = None

    @field_validator("media_id", "output_url", "status")
    @classmethod
    def validate_optional_text(cls, value: str | None, info) -> str | None:
        return None if value is None else _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def require_locator(self) -> "LegacyMediaBinding":
        if self.media_id is None and self.output_url is None:
            raise ValueError("legacy media binding requires media_id or output_url")
        return self


class OperationalSceneExecutionProjection(BaseModel):
    """Versioned compatibility read model for one legacy operational Scene."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    projection_id: LogicalId
    version_id: VersionId
    migration_run_id: str
    canonical_project_id: LogicalId
    scene_mapping_ref: VersionRef
    source_payload_sha256: str
    legacy_scene_id: str
    legacy_video_id: str
    display_order: int = Field(ge=0)
    parent_scene_id: str | None = None
    chain_type: str | None = None
    legacy_source: str | None = None
    shot_refs: tuple[VersionRef, ...] = ()
    generation_job_id: LogicalId | None = None
    generation_job_revision: int | None = Field(default=None, ge=0)
    request_mapping_refs: tuple[VersionRef, ...] = ()
    media: tuple[LegacyMediaBinding, ...] = ()

    @field_validator(
        "migration_run_id",
        "source_payload_sha256",
        "legacy_scene_id",
        "legacy_video_id",
    )
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("parent_scene_id", "chain_type", "legacy_source")
    @classmethod
    def validate_optional(cls, value: str | None, info) -> str | None:
        return None if value is None else _trimmed(value, info.field_name)

    @model_validator(mode="after")
    def validate_projection(self) -> "OperationalSceneExecutionProjection":
        expected = operational_scene_projection_logical_id(
            self.migration_run_id,
            self.legacy_scene_id,
        )
        if self.projection_id != expected:
            raise ValueError("projection_id does not match migration/legacy Scene identity")
        if not self.scene_mapping_ref.logical_id.root.startswith("legacy-import-mapping:"):
            raise ValueError("scene_mapping_ref must reference an IMP-080 mapping")
        shot_keys = [_ref_key(ref) for ref in self.shot_refs]
        if len(shot_keys) != len(set(shot_keys)):
            raise ValueError("shot_refs must not contain duplicates")
        if any(not ref.logical_id.root.startswith("shot-list-item:") for ref in self.shot_refs):
            raise ValueError("execution projection may reference only canonical ShotListItem targets")
        request_keys = [_ref_key(ref) for ref in self.request_mapping_refs]
        if len(request_keys) != len(set(request_keys)):
            raise ValueError("request_mapping_refs must not contain duplicates")
        if any(not ref.logical_id.root.startswith("legacy-import-mapping:") for ref in self.request_mapping_refs):
            raise ValueError("request_mapping_refs must reference IMP-080 mappings")
        if (self.generation_job_id is None) != (self.generation_job_revision is None):
            raise ValueError("GenerationJob projection requires identity + exact revision")
        if not self.shot_refs and self.generation_job_id is None:
            raise ValueError("execution projection requires ShotListItem and/or GenerationJob proof")
        media_keys = [(item.orientation.value, item.role.value) for item in self.media]
        if len(media_keys) != len(set(media_keys)):
            raise ValueError("legacy media role/orientation bindings must be unique")
        return self

    @property
    def ref(self) -> VersionRef:
        return VersionRef(logical_id=self.projection_id, version_id=self.version_id)

    def source_bindings(self) -> tuple[SourceVersionBinding, ...]:
        values: list[SourceVersionBinding] = [
            SourceVersionBinding(role="legacy_scene_mapping", source=self.scene_mapping_ref)
        ]
        values.extend(
            SourceVersionBinding(role=f"compatibility_shot_{index:03d}", source=ref)
            for index, ref in enumerate(self.shot_refs)
        )
        values.extend(
            SourceVersionBinding(role=f"legacy_request_mapping_{index:03d}", source=ref)
            for index, ref in enumerate(self.request_mapping_refs)
        )
        return tuple(values)


class OperationalSceneProjectionArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    metadata: SemanticRecordMetadata
    value: OperationalSceneExecutionProjection

    @model_validator(mode="after")
    def validate_artifact(self) -> "OperationalSceneProjectionArtifact":
        if self.metadata.logical_id != self.value.projection_id:
            raise ValueError("projection metadata logical identity mismatch")
        if self.metadata.version_id != self.value.version_id:
            raise ValueError("projection metadata version identity mismatch")
        if self.metadata.provenance.source_versions != self.value.source_bindings():
            raise ValueError("projection provenance must exactly bind declared source versions")
        return self

    @property
    def ref(self) -> VersionRef:
        return self.value.ref


class OperationalSceneProjectionRequest(BaseModel):
    """Ephemeral request. Raw legacy Scene content is verified but never persisted verbatim."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    scene_mapping_ref: VersionRef
    scene_row: Mapping[str, Any]
    result_version_id: VersionId
    request_mapping_refs: tuple[VersionRef, ...] = ()
    actor_ref: str
    reason: str
    recorded_at: AwareDatetime
    correlation_id: str | None = None
    evidence_refs: tuple[str, ...] = ()

    @field_validator("actor_ref", "reason")
    @classmethod
    def validate_text(cls, value: str, info) -> str:
        return _trimmed(value, info.field_name)

    @field_validator("evidence_refs")
    @classmethod
    def validate_evidence(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_trimmed(value, "evidence_ref") for value in values)
        if len(normalized) != len(set(normalized)):
            raise ValueError("evidence_refs must not contain duplicates")
        return normalized

    @model_validator(mode="after")
    def validate_request_refs(self) -> "OperationalSceneProjectionRequest":
        keys = [_ref_key(ref) for ref in self.request_mapping_refs]
        if len(keys) != len(set(keys)):
            raise ValueError("request_mapping_refs must not contain duplicates")
        return self


class OperationalSceneProjectionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact: OperationalSceneProjectionArtifact
    invalidation_count: int = Field(default=0, ge=0)


_MEDIA_SPECS: tuple[tuple[LegacyOrientation, LegacyMediaRole, str, str | None, str | None], ...] = (
    (LegacyOrientation.VERTICAL, LegacyMediaRole.IMAGE, "vertical_image_media_id", "vertical_image_url", "vertical_image_status"),
    (LegacyOrientation.VERTICAL, LegacyMediaRole.VIDEO, "vertical_video_media_id", "vertical_video_url", "vertical_video_status"),
    (LegacyOrientation.VERTICAL, LegacyMediaRole.UPSCALE, "vertical_upscale_media_id", "vertical_upscale_url", "vertical_upscale_status"),
    (LegacyOrientation.VERTICAL, LegacyMediaRole.END_FRAME, "vertical_end_scene_media_id", None, None),
    (LegacyOrientation.HORIZONTAL, LegacyMediaRole.IMAGE, "horizontal_image_media_id", "horizontal_image_url", "horizontal_image_status"),
    (LegacyOrientation.HORIZONTAL, LegacyMediaRole.VIDEO, "horizontal_video_media_id", "horizontal_video_url", "horizontal_video_status"),
    (LegacyOrientation.HORIZONTAL, LegacyMediaRole.UPSCALE, "horizontal_upscale_media_id", "horizontal_upscale_url", "horizontal_upscale_status"),
    (LegacyOrientation.HORIZONTAL, LegacyMediaRole.END_FRAME, "horizontal_end_scene_media_id", None, None),
)


class OperationalSceneExecutionProjectionService:
    """Build/persist bounded execution projections from IMP-080 approved proof."""

    def __init__(self, writer) -> None:
        self.versions = VersionRepository(writer)
        self.imports = LegacyImportAntiCorruptionService(writer)
        self.jobs = GenerationJobRepository(writer)
        self.shots = ShotPlanningRepository(writer)
        self.graph = DependencyGraphRepository(writer)
        self.invalidations = InvalidationRepository(writer, graph=self.graph)

    async def project(
        self,
        request: OperationalSceneProjectionRequest,
    ) -> OperationalSceneProjectionResult:
        mapping = await self._load_scene_mapping(request.scene_mapping_ref)
        self._verify_raw_scene(mapping, request.scene_row)
        await self._assert_shots(mapping)
        job = await self._assert_job(mapping)
        request_mappings = await self._assert_request_mappings(
            mapping,
            request.request_mapping_refs,
        )
        value = self._build_value(request, mapping, job, request_mappings)
        provenance = self._provenance(request, value)
        artifact, invalidation_count = await self._persist(value, provenance, request.recorded_at)
        return OperationalSceneProjectionResult(
            artifact=artifact,
            invalidation_count=invalidation_count,
        )

    async def get_projection(self, ref: VersionRef) -> OperationalSceneProjectionArtifact | None:
        if not ref.logical_id.root.startswith("legacy-scene-execution-projection:"):
            raise OperationalSceneProjectionIdentityError("expected legacy execution projection reference")
        stored = await self.versions.get_version(ref)
        if stored is None:
            return None
        value = OperationalSceneExecutionProjection.model_validate(stored.payload)
        return OperationalSceneProjectionArtifact(metadata=stored.metadata, value=value)

    async def _load_scene_mapping(self, ref: VersionRef) -> LegacyImportMappingRecord:
        artifact = await self.imports.get_mapping(ref)
        if artifact is None:
            raise OperationalSceneProjectionGateBlocked("scene mapping exact version not found")
        pointer = await self.versions.get_current(ref.logical_id)
        if (
            pointer is None
            or pointer.version_id != ref.version_id
            or pointer.status is not LifecycleState.APPROVED
        ):
            raise OperationalSceneProjectionGateBlocked(
                "scene mapping must be exact-current APPROVED IMP-080 evidence"
            )
        value = artifact.value
        if value.source.source_kind is not LegacySourceKind.OPERATIONAL_SCENE:
            raise OperationalSceneProjectionGateBlocked(
                "projection source must be an IMP-080 OPERATIONAL_SCENE mapping"
            )
        if value.disposition is not LegacyImportDisposition.COMPATIBILITY_MAPPED:
            raise OperationalSceneProjectionGateBlocked(
                "operational Scene mapping must be COMPATIBILITY_MAPPED"
            )
        if value.canonical_project_id is None:
            raise OperationalSceneProjectionGateBlocked(
                "operational Scene mapping requires canonical project proof"
            )
        return value

    def _verify_raw_scene(
        self,
        mapping: LegacyImportMappingRecord,
        row: Mapping[str, Any],
    ) -> None:
        source = LegacySourceEvidence.from_legacy(
            row,
            source_kind=LegacySourceKind.OPERATIONAL_SCENE,
            source_table=mapping.source.source_table,
            source_id=mapping.source.source_id,
            source_schema_version=mapping.source.source_schema_version,
        )
        if source != mapping.source:
            raise OperationalSceneProjectionGateBlocked(
                "raw operational Scene no longer matches exact IMP-080 source evidence"
            )
        scene_id = _optional_trimmed(row.get("id"), "scene.id")
        if scene_id != mapping.source.source_id:
            raise OperationalSceneProjectionGateBlocked(
                "raw operational Scene id does not match mapping source identity"
            )

    async def _assert_shots(self, mapping: LegacyImportMappingRecord) -> None:
        assert mapping.canonical_project_id is not None
        for ref in mapping.target_refs:
            artifact = await self.shots.get_shot_list_item(ref)
            if artifact is None:
                raise OperationalSceneProjectionGateBlocked(
                    "mapped ShotListItem exact version no longer exists"
                )
            pointer = await self.versions.get_current(ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != ref.version_id
                or pointer.status not in _ACCEPTED
            ):
                raise OperationalSceneProjectionGateBlocked(
                    "mapped ShotListItem proof is stale or no longer accepted"
                )
            if artifact.value.project_id != mapping.canonical_project_id:
                raise OperationalSceneProjectionGateBlocked(
                    "mapped ShotListItem belongs to another canonical project"
                )

    async def _assert_job(self, mapping: LegacyImportMappingRecord) -> GenerationJob | None:
        if mapping.generation_job_id is None:
            return None
        assert mapping.generation_job_revision is not None
        assert mapping.canonical_project_id is not None
        job = await self.jobs.get_job(mapping.generation_job_id)
        if job is None:
            raise OperationalSceneProjectionGateBlocked("mapped GenerationJob no longer exists")
        if job.revision != mapping.generation_job_revision:
            raise OperationalSceneProjectionGateBlocked(
                "mapped GenerationJob revision is stale; projection requires exact runtime revision"
            )
        if job.project_id != mapping.canonical_project_id:
            raise OperationalSceneProjectionGateBlocked(
                "mapped GenerationJob belongs to another canonical project"
            )
        if mapping.target_refs and job.shot_id not in {ref.logical_id for ref in mapping.target_refs}:
            raise OperationalSceneProjectionGateBlocked(
                "mapped GenerationJob shot_id no longer matches mapped ShotListItem proof"
            )
        return job

    async def _assert_request_mappings(
        self,
        scene_mapping: LegacyImportMappingRecord,
        refs: tuple[VersionRef, ...],
    ) -> tuple[LegacyImportMappingRecord, ...]:
        loaded: list[LegacyImportMappingRecord] = []
        for ref in refs:
            artifact = await self.imports.get_mapping(ref)
            if artifact is None:
                raise OperationalSceneProjectionGateBlocked(
                    "request mapping exact version not found"
                )
            pointer = await self.versions.get_current(ref.logical_id)
            if (
                pointer is None
                or pointer.version_id != ref.version_id
                or pointer.status is not LifecycleState.APPROVED
            ):
                raise OperationalSceneProjectionGateBlocked(
                    "request mapping must be exact-current APPROVED IMP-080 evidence"
                )
            value = artifact.value
            if (
                value.source.source_kind is not LegacySourceKind.REQUEST
                or value.disposition is not LegacyImportDisposition.COMPATIBILITY_MAPPED
            ):
                raise OperationalSceneProjectionGateBlocked(
                    "request_mapping_refs must be COMPATIBILITY_MAPPED REQUEST evidence"
                )
            if scene_mapping.generation_job_id is None:
                raise OperationalSceneProjectionGateBlocked(
                    "request mapping requires a scene mapping with GenerationJob proof"
                )
            if (
                value.generation_job_id != scene_mapping.generation_job_id
                or value.generation_job_revision != scene_mapping.generation_job_revision
            ):
                raise OperationalSceneProjectionGateBlocked(
                    "request mapping must bind the same exact GenerationJob revision as the scene"
                )
            if value.canonical_project_id != scene_mapping.canonical_project_id:
                raise OperationalSceneProjectionGateBlocked(
                    "request mapping canonical project does not match scene mapping"
                )
            loaded.append(value)
        return tuple(loaded)

    def _build_value(
        self,
        request: OperationalSceneProjectionRequest,
        mapping: LegacyImportMappingRecord,
        job: GenerationJob | None,
        request_mappings: tuple[LegacyImportMappingRecord, ...],
    ) -> OperationalSceneExecutionProjection:
        row = request.scene_row
        scene_id = _trimmed(str(row.get("id")), "scene.id")
        video_id = _optional_trimmed(row.get("video_id"), "scene.video_id")
        if video_id is None:
            raise OperationalSceneProjectionGateBlocked(
                "legacy operational Scene requires video_id for execution projection"
            )
        raw_order = row.get("display_order", 0)
        if isinstance(raw_order, bool) or not isinstance(raw_order, int) or raw_order < 0:
            raise OperationalSceneProjectionGateBlocked(
                "legacy operational Scene display_order must be a non-negative integer"
            )
        media = self._media_bindings(row)
        assert mapping.canonical_project_id is not None
        return OperationalSceneExecutionProjection(
            projection_id=operational_scene_projection_logical_id(
                mapping.migration_run_id,
                scene_id,
            ),
            version_id=request.result_version_id,
            migration_run_id=mapping.migration_run_id,
            canonical_project_id=mapping.canonical_project_id,
            scene_mapping_ref=mapping.ref,
            source_payload_sha256=mapping.source.payload_sha256,
            legacy_scene_id=scene_id,
            legacy_video_id=video_id,
            display_order=raw_order,
            parent_scene_id=_optional_trimmed(row.get("parent_scene_id"), "parent_scene_id"),
            chain_type=_optional_trimmed(row.get("chain_type"), "chain_type"),
            legacy_source=_optional_trimmed(row.get("source"), "source"),
            shot_refs=mapping.target_refs,
            generation_job_id=None if job is None else job.generation_job_id,
            generation_job_revision=None if job is None else job.revision,
            request_mapping_refs=tuple(value.ref for value in request_mappings),
            media=media,
        )

    def _media_bindings(self, row: Mapping[str, Any]) -> tuple[LegacyMediaBinding, ...]:
        result: list[LegacyMediaBinding] = []
        for orientation, role, media_field, url_field, status_field in _MEDIA_SPECS:
            media_id = _optional_trimmed(row.get(media_field), media_field)
            output_url = None if url_field is None else _optional_trimmed(row.get(url_field), url_field)
            if media_id is None and output_url is None:
                continue
            status = None if status_field is None else _optional_trimmed(row.get(status_field), status_field)
            result.append(
                LegacyMediaBinding(
                    orientation=orientation,
                    role=role,
                    media_id=media_id,
                    output_url=output_url,
                    status=status,
                )
            )
        return tuple(result)

    def _provenance(
        self,
        request: OperationalSceneProjectionRequest,
        value: OperationalSceneExecutionProjection,
    ) -> Provenance:
        source_refs: list[str] = [
            f"legacy-scene:{value.legacy_scene_id}",
            value.source_payload_sha256,
            f"legacy-video:{value.legacy_video_id}",
        ]
        if value.generation_job_id is not None:
            source_refs.append(
                f"{value.generation_job_id.root}@revision:{value.generation_job_revision}"
            )
        for media in value.media:
            prefix = f"legacy-media:{media.orientation.value.lower()}:{media.role.value.lower()}"
            if media.media_id is not None:
                source_refs.append(f"{prefix}:id:{media.media_id}")
            if media.output_url is not None:
                url_digest = hashlib.sha256(media.output_url.encode("utf-8")).hexdigest()
                source_refs.append(f"{prefix}:url-sha256:{url_digest}")
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
        value: OperationalSceneExecutionProjection,
        provenance: Provenance,
        created_at: datetime,
    ) -> tuple[OperationalSceneProjectionArtifact, int]:
        existing = await self.versions.get_version(value.ref)
        if existing is not None:
            materialized = OperationalSceneProjectionArtifact(
                metadata=existing.metadata,
                value=OperationalSceneExecutionProjection.model_validate(existing.payload),
            )
            if materialized.value != value or materialized.metadata.provenance != provenance:
                raise OperationalSceneProjectionIdentityError(
                    "projection exact replay conflicts with persisted execution evidence"
                )
            return materialized, 0

        pointer = await self.versions.get_current(value.projection_id)
        predecessor_ref: VersionRef | None = None
        metadata = SemanticRecordMetadata(
            logical_id=value.projection_id,
            version_id=value.version_id,
            provenance=provenance,
            created_at=created_at,
            predecessor=None
            if pointer is None
            else VersionRef(logical_id=value.projection_id, version_id=pointer.version_id),
        )
        if pointer is None:
            stored = await self.versions.create_initial(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                status=LifecycleState.APPROVED,
            )
        else:
            predecessor_ref = VersionRef(
                logical_id=value.projection_id,
                version_id=pointer.version_id,
            )
            stored = await self.versions.create_successor(
                metadata=metadata,
                payload=value.model_dump(mode="json"),
                supersession_reason=provenance.reason,
            )
            await self.versions.update_current(
                logical_id=value.projection_id,
                version_id=value.version_id,
                status=LifecycleState.APPROVED,
                expected_revision=pointer.revision,
            )
        artifact = OperationalSceneProjectionArtifact(metadata=stored.metadata, value=value)
        await self._register_dependencies(artifact)

        invalidation_count = 0
        if predecessor_ref is not None:
            records = await self.invalidations.create_for_change(
                cause="OperationalSceneExecutionProjection successor",
                source_old=predecessor_ref,
                source_new=artifact.ref,
                provenance=artifact.metadata.provenance,
                scope="legacy_execution_projection_descendants",
                repair_or_recompute_requirement=(
                    "Rebind only compatibility consumers that depended on the superseded execution projection."
                ),
            )
            invalidation_count = len(records)
        return artifact, invalidation_count

    async def _register_dependencies(
        self,
        artifact: OperationalSceneProjectionArtifact,
    ) -> None:
        grouped: dict[tuple[str, str], list[str]] = {}
        refs: dict[tuple[str, str], VersionRef] = {}
        for binding in artifact.value.source_bindings():
            key = _ref_key(binding.source)
            refs[key] = binding.source
            grouped.setdefault(key, []).append(binding.role)
        for key in sorted(grouped):
            await self.graph.create_edge(
                source=refs[key],
                dependent=artifact.ref,
                edge_type="legacy_execution_projection_source",
                dependency_reason=" + ".join(sorted(set(grouped[key]))),
                provenance=artifact.metadata.provenance,
                created_at=artifact.metadata.created_at,
            )

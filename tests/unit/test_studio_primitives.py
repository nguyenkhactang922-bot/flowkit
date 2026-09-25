"""Tests for provider-neutral canonical Studio primitives."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent.studio import (
    FindingSeverity,
    GateVerdict,
    LifecycleState,
    LogicalId,
    Provenance,
    SemanticRecordMetadata,
    SourceVersionBinding,
    VersionId,
    VersionRef,
)

NOW = datetime(2026, 9, 25, 8, 0, tzinfo=timezone.utc)


def _source(role: str = "story_core") -> SourceVersionBinding:
    return SourceVersionBinding(
        role=role,
        source=VersionRef(
            logical_id=LogicalId("story-core:001"),
            version_id=VersionId("v3"),
        ),
    )


def _provenance() -> Provenance:
    return Provenance(
        source_versions=(_source(),),
        source_refs=("evidence:research-17",),
        actor_ref="studio:story-engine",
        reason="derive successor from accepted story core",
        recorded_at=NOW,
        correlation_id="run:abc-123",
    )


def test_version_ref_serialization_and_equality_round_trip():
    ref = VersionRef(
        logical_id=LogicalId("shot:0042"),
        version_id=VersionId("v7"),
    )

    payload = ref.model_dump(mode="json")
    restored = VersionRef.model_validate(payload)

    assert payload == {"logical_id": "shot:0042", "version_id": "v7"}
    assert restored == ref


@pytest.mark.parametrize(
    "primitive,value",
    [
        (LogicalId, ""),
        (LogicalId, " story:1"),
        (LogicalId, "story id"),
        (LogicalId, "story?1"),
        (VersionId, ""),
        (VersionId, " v1"),
        (VersionId, "version one"),
    ],
)
def test_invalid_logical_id_and_version_are_rejected(primitive, value):
    with pytest.raises(ValidationError):
        primitive(value)


def test_source_version_binding_serializes_exact_source_pair():
    binding = _source("accepted_story_core")

    assert binding.model_dump(mode="json") == {
        "role": "accepted_story_core",
        "source": {
            "logical_id": "story-core:001",
            "version_id": "v3",
        },
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "source_versions": (),
            "source_refs": (),
            "actor_ref": "studio:engine",
            "reason": "rootless",
            "recorded_at": NOW,
        },
        {
            "source_versions": (_source(),),
            "source_refs": (),
            "actor_ref": "",
            "reason": "derive",
            "recorded_at": NOW,
        },
        {
            "source_versions": (_source(), _source()),
            "source_refs": (),
            "actor_ref": "studio:engine",
            "reason": "derive",
            "recorded_at": NOW,
        },
        {
            "source_versions": (_source(),),
            "source_refs": (" evidence:1",),
            "actor_ref": "studio:engine",
            "reason": "derive",
            "recorded_at": NOW,
        },
        {
            "source_versions": (_source(),),
            "source_refs": (),
            "actor_ref": "studio:engine",
            "reason": "derive",
            "recorded_at": datetime(2026, 9, 25, 8, 0),
        },
    ],
)
def test_invalid_provenance_is_rejected(kwargs):
    with pytest.raises(ValidationError):
        Provenance(**kwargs)


def test_semantic_record_metadata_round_trip_and_immutability():
    metadata = SemanticRecordMetadata(
        logical_id=LogicalId("scene:0007"),
        version_id=VersionId("v2"),
        predecessor=VersionRef(
            logical_id=LogicalId("scene:0007"),
            version_id=VersionId("v1"),
        ),
        provenance=_provenance(),
        created_at=NOW,
        content_hash="sha256:" + ("a" * 64),
    )

    serialized = metadata.model_dump_json()
    restored = SemanticRecordMetadata.model_validate_json(serialized)

    assert restored == metadata
    assert restored.logical_id == LogicalId("scene:0007")
    with pytest.raises(ValidationError):
        metadata.version_id = VersionId("v3")


def test_semantic_record_rejects_cross_identity_or_self_predecessor():
    base = dict(
        logical_id=LogicalId("scene:0007"),
        version_id=VersionId("v2"),
        provenance=_provenance(),
        created_at=NOW,
    )

    with pytest.raises(ValidationError, match="same logical ID"):
        SemanticRecordMetadata(
            **base,
            predecessor=VersionRef(
                logical_id=LogicalId("scene:9999"),
                version_id=VersionId("v1"),
            ),
        )

    with pytest.raises(ValidationError, match="must differ"):
        SemanticRecordMetadata(
            **base,
            predecessor=VersionRef(
                logical_id=LogicalId("scene:0007"),
                version_id=VersionId("v2"),
            ),
        )


def test_lifecycle_gate_and_finding_values_are_explicit_strings():
    assert LifecycleState.APPROVED.value == "APPROVED"
    assert GateVerdict.OPEN.value == "OPEN"
    assert GateVerdict.NEEDS_HUMAN_REVIEW.value == "NEEDS_HUMAN_REVIEW"
    assert FindingSeverity.BLOCKER.value == "BLOCKER"


def test_canonical_primitive_schemas_have_no_provider_fields():
    forbidden = {
        "provider",
        "provider_id",
        "provider_name",
        "model",
        "model_id",
        "model_key",
        "flow_project_id",
        "google_project_id",
        "request_id",
        "remote_job_id",
    }

    models = (
        VersionRef,
        SourceVersionBinding,
        Provenance,
        SemanticRecordMetadata,
    )

    field_names = set()
    for model in models:
        stack = [model.model_json_schema()]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                properties = node.get("properties", {})
                field_names.update(properties.keys())
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)

    assert field_names.isdisjoint(forbidden)


def test_canonical_primitives_reject_provider_transport_fields():
    with pytest.raises(ValidationError):
        VersionRef(
            logical_id=LogicalId("shot:0042"),
            version_id=VersionId("v7"),
            provider="google-flow",
        )

    with pytest.raises(ValidationError):
        Provenance(
            source_versions=(_source(),),
            source_refs=(),
            actor_ref="studio:engine",
            reason="derive",
            recorded_at=NOW,
            provider_id="remote-provider",
        )

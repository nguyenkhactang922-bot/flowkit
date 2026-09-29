# IMP-040 — Canonical Entity Versioning Adapter Evidence

## Claim

Task: IMP-040 Canonical Entity Versioning Adapter

Authority:
- frozen Master SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- `docs/architecture/IMPLEMENTATION_DEPENDENCY_GRAPH_V1.md`
- `tasks/IMPLEMENTATION_TASK_DECOMPOSITION_V1.md`
- frozen Master §56 Entity System.

Branch:
`chatgpt/IMP-040-canonical-entity-versioning`

## Implemented scope

- Added provider-neutral `EntityVersion` canonical semantic contract.
- Added deterministic stable mapping `legacy character/entity id -> entity:<legacy-id>`.
- Added `LegacyEntitySnapshot` anti-corruption input for current FlowKit character/entity records.
- Added `LegacyEntityBinding` compatibility projection so current media/reference fields stay usable without becoming canonical Entity truth.
- Added `CanonicalEntityAdapter`.
- Added `CanonicalEntityRepository` backed by the shared immutable `VersionRepository`; no parallel entity semantic table/store was introduced.
- Added successor version creation, exact predecessor validation, current-pointer promotion and readback.
- Preserved legacy project linkage as canonical entity metadata while keeping reference media and provider-facing image prompts outside Entity semantic identity.
- Exported IMP-040 contracts through `agent.studio`.

## Acceptance evidence

### Frozen baseline guard

Command:

`python tools/frozen_master_guard.py --repo-root .`

Result:

```
FROZEN_MASTER_GUARD=PASS
MASTER=docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1.md
SHA256=1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
NEWLINE_NORMALIZED=CRLF_TO_LF
```

Frozen semantic SHA remains unchanged.

### Targeted IMP-040

Command:

`PYTHONUTF8=1 uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_entity.py -q`

Result:

```
7 passed
```

Covered:
- stable logical ID across semantic successors;
- mapping from current legacy Character/entity;
- reference media / provider prompt excluded from Entity semantic truth;
- compatibility binding preserves legacy media integration;
- shared VersionRepository persistence;
- no `studio_entity*` shadow semantic table;
- old semantic version preserved across successor;
- cross-entity predecessor rejected;
- project link dedupe without identity mutation;
- shadow canonical identity mapping rejected.

### Related regression cluster

Command:

`python -m pytest tests/unit/test_studio_entity.py tests/unit/test_studio_versioning.py tests/unit/test_studio_invalidation.py tests/unit/test_frozen_master_guard.py -q`

Result:

```
35 passed
```

### Full Windows unit regression

Unfiltered result:

```
527 passed, 3 failed
```

The three failures are the exact pre-existing Windows/POSIX path assertions in `tests/unit/test_cli_providers.py`:
- two parameter cases expect `/tmp` but Windows resolves `\\tmp`;
- one single-sheet wording assertion expects `/tmp/sheet_00.jpg` but Windows resolves `\\tmp\\sheet_00.jpg`.

IMP-040 does not modify those surfaces.

Largest unaffected regression command excluded only those exact known platform-specific cases.

Result:

```
527 passed, 3 deselected
```

### Static checks

```
python -m compileall -q agent/studio/entity.py
PASS

git diff --check
PASS
```

## Authority checks

- Entity semantic identity is `entity_id + entity_version`.
- Canonical Entity Registry semantics use the existing immutable VersionRepository.
- Current `character` table remains compatibility/execution data; it does not become a competing canonical Entity store.
- Reference `media_id`, `reference_image_url`, and `image_prompt` are not stored in canonical `EntityVersion`.
- Semantic change creates a successor version; accepted prior semantic versions are preserved.
- Reference generation/provider work is outside canonical entity persistence transactions.

## Local verdict

`IMP-040 = LOCAL VERIFIED`

Remote PR/CI/exact-head review/merge/main verification remain required before `MAIN VERIFIED`.

# IMP-013 — ActiveProductionProfile Evidence

## Task

IMP-013 — ActiveProductionProfile

Branch:
`chatgpt/IMP-013-active-production-profile`

Base:
`8942b06a2ebf9b67392a95222fe452ceaea12572`

Depends:
- `IMP-012 = MAIN VERIFIED`
- `IMP-005 = MAIN VERIFIED`

Frozen Master SHA:
`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Implemented scope

Canonical snapshot:
- `ActiveProductionProfile` is an immutable pinned effective-policy snapshot.
- Identity is stable per project: `active-profile:<project_id>` + immutable `profile_version`.
- Snapshot binds exact ProfileResolution, Project, Topic, Domain, Resolver and effective BrainPack versions.
- Every effective policy path stores canonical JSON value bytes/hash and exact winning provenance.
- Effective-policy and resolution-trace hashes are verified.

Persistence:
- `ActiveProductionProfileRepository` persists through the immutable `VersionRepository`.
- Initial and successor versions are immutable and LOCKED.
- Semantic re-resolution creates a successor version; no in-place profile mutation.
- Current pointer changes remain an explicit CAS operation.

Downstream binding:
- `ActiveProductionProfileBinding` exposes exact profile version only.
- `ActiveProductionProfileDependencyBinder` creates exact profile-version dependency edges.
- Consumers may bind one exact policy path or wildcard `*`.
- Unknown path binding fails closed.
- No BrainPack registry/resolver authority is exposed downstream.

Change/invalidation:
- deterministic `ProfileChangeSet`;
- added/removed/value-changed/provenance-changed path groups;
- changed-path union is sorted and unique;
- only direct profile edges bound to changed paths or wildcard are selected;
- descendants of selected direct dependents are invalidated transitively;
- unrelated profile-path branches are preserved;
- no effective-path change creates no invalidation record.

## Review finding repaired before commit

Review found that the new generic selective `reachable=` extension on
`InvalidationRepository.create_for_change` originally validated only the final
edge against the affected object. A forged internal reachability plan could have
referenced a durable edge unrelated to `source_old` and caused over-invalidation.

Repair:
- supplied selective reachability is now validated as a full durable graph path;
- `depth == len(path_edge_ids)` is required;
- first edge must originate at exact `source_old`;
- every edge must continue the prior dependent version;
- final path target must equal the affected exact version;
- terminal `via_edge_id/type/reason` must match durable graph truth;
- DB write still revalidates terminal edge truth inside the transaction.

New forged-plan test:
- **1/1 PASS**
- no invalidation record is written for a forged unrelated path.

## Local verification

Python 3.13 isolated environment.

Before review repair, full unfiltered Windows suite:
- **493 PASS / 3 FAIL**
- failures were the exact pre-existing Windows/POSIX `/tmp` assertions.

After review repair:
- targeted IMP-013: **10/10 PASS**
- frozen Master guard: **PASS**
- exact-head clean regression excluding exactly those three known platform cases:
  **494 PASS / 3 deselected**
- provider-specific canonical field scan: **clean**
- `git diff --check`: **PASS**

No IMP-013 failure remains.

## Local verdict

**IMP-013 = LOCAL VERIFIED**

Remote push/PR/Ubuntu CI/exact-head review/merge/main verification remain pending.

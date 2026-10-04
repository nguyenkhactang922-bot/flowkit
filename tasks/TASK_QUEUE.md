# Task Queue

## Pending

- Repository discovery and audit.
- Design work is intentionally not started yet.


---

## Discovery / Design Queue ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â 2026-09-22

### Verified discovery completed

- [x] Read governance/bootstrap files.
- [x] Map current repository topology and manifests.
- [x] Audit current Entity / Reference / Continuity / Story / Scene / Beat / Shot / Prompt subsystems.
- [x] Audit Generation / Provider / Queue / Retry / Resume / Persistence / QA / Repair subsystems.
- [x] Create current-state architecture audit.
- [x] Create FlowKit-to-target-Studio gap matrix.

### Pending design/discovery only

- [ ] Import canonical Studio design documents supplied/approved for this project.
- [ ] Build a Design Authority Map: concept ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ authoritative document ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ owner ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ version ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ lock state.
- [ ] Build terminology map between current FlowKit concepts and target Studio concepts.
- [ ] Resolve canonical hierarchy: Story ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ MacroStoryBeat ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Sequence ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Scene ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ SceneDramaticBeat ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ Shot.
- [ ] Resolve current Scene migration role without changing feature code.
- [ ] Define conceptual boundaries for Entity / Reference / State / Continuity.
- [ ] Define authority precedence for FIXED / INHERITED / VARIABLE production truth.
- [ ] Define conceptual Shot IR and Compiler responsibility boundaries.
- [ ] Define Provider Capability / Router responsibility boundaries.
- [ ] Define Orchestrator / ProductionRun / PlanNode / Attempt / Artifact conceptual boundaries.
- [ ] Define QA Finding / Evidence / Gate and Targeted Repair conceptual boundaries.
- [ ] Produce architecture/dependency diagrams after authority conflicts are resolved.
- [ ] Only after design authority is locked, derive implementation tasks in a later phase.

No feature implementation tasks are authorized in this queue section.


---

## Pre-Master Authority Resolution Queue ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â 2026-09-22

### Completed design/discovery work

- [x] Read and hash-inventory V0.1 through V0.16 expanded corpus.
- [x] Evaluate three post-V0.16 design patches independently.
- [x] Evaluate standalone frozen architecture and FlowKit production audit.
- [x] Build file-level historical inventory.
- [x] Build evidence-based supersession graph.
- [x] Build domain authority map.
- [x] Build canonical merge candidate set.
- [x] Build pre-Master contradiction register.
- [x] Run pre-Master authority coverage audit.

### Blocking design decisions ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â resolve before Master

- [x] Resolve credential-broker/secret-storage authority status ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ADR-0016.
- [x] Resolve one universal BrainPack registry + ActiveProductionProfile ownership/precedence ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ADR-0017.
- [x] Resolve Narrative Expansion artifact identities and canonical hierarchy ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ADR-0018.
- [x] Resolve MacroStoryBeat/SceneDramaticBeat and DramaticÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢Camera authority ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ADR-0018 + ADR-0019.
- [x] Resolve Shot identity / ShotListManifest / FullShotSpec / ShotIR boundary ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ADR-0020.

### After blockers reach zero ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â still design only

- [x] Update contradiction register statuses with exact ADR decisions.
- [x] Update authority map so blocker domains have one conflict-free primary owner.
- [x] Re-run PRE_MASTER_AUTHORITY_COVERAGE_AUDIT ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â V2 PASS, blocking conflicts = 0.
- [ ] Only then authorize canonical Master consolidation in a later step.
- [ ] During later Master consolidation, add one Compiler responsibility section and one Sequence QA contract section.

No feature implementation, coding, build, dependency installation, test execution, task decomposition for code, or commit is authorized by this queue section.



---

## Master Consolidation Design Queue ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â 2026-09-22

Authority gate:
- [x] Blocking authority conflicts resolved.
- [x] PRE_MASTER_AUTHORITY_COVERAGE_AUDIT_V2 PASS.
- [x] Blocking conflicts = 0.

Next design-only action:
- [x] Consolidate accepted canonical sources into Master Implementation Baseline candidate.
- [x] Resolve PM-014 in Master ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§64 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â one Production Compiler boundary.
- [x] Resolve PM-020 in Master ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§77 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â one Sequence QA contract.
- [x] Run MASTER_CONSOLIDATION_SELF_AUDIT_V1 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â PASS; unresolved=0, blocking=0.
- [ ] Freeze Master only after zero blocking contradiction is verified.

No feature coding, build/test, dependency installation, implementation task decomposition or commit is authorized by this queue section.



---

## Independent Final Master Audit Queue ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â 2026-09-22

Completed:
- [x] Canonical Master candidate consolidated.
- [x] PM-014 Compiler responsibility resolved in Master ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§64.
- [x] PM-020 Sequence QA resolved in Master ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â§77.
- [x] Requirement traceability repaired so every historical requirement ID is explicitly represented.
- [x] MASTER_CONSOLIDATION_SELF_AUDIT_V1 PASS.
- [x] Unresolved conflicts = 0.
- [x] Blocking conflicts = 0.

Next design-only gate:
- [x] Run independent final Master audit ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â FAIL: BLOCKER=0, MAJOR=8, MINOR=0, NOTE=2.
- [ ] Freeze is BLOCKED until all FINAL_MASTER_INDEPENDENT_AUDIT_V1 MAJOR findings are repaired and independently re-audited.
- [ ] Do not create dependency graph/task decomposition until the freeze step explicitly authorizes it.

No feature coding, build/test, dependency installation or commit is authorized by this queue section.



---

## Final Master Audit Repair Queue ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â 2026-09-22

Design-document repair only. No implementation tasks are authorized.

- [x] FM-001 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â restore MacroBeatSheet / SceneListManifest / SceneBreakdownManifest projection contracts without creating second truth stores.
- [x] FM-002 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â make Story/Pre-production component lifecycle contracts explicit at component level.
- [x] FM-003 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â restore JOB_STATE_MODEL_V0_13 exact state enums/transition ownership into Master.
- [x] FM-004 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â restore explicit Electron hardening flags and IPC/navigation security baseline.
- [x] FM-005 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â add durable InvalidationRecord ownership/persistence/version semantics and explicit Reference invalidation.
- [x] FM-006 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â allocate non-colliding requirement IDs for accepted post-V0.16 obligations and complete bidirectional traceability.
- [x] FM-007 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â make ApprovedEndState identity boundary explicit with StateSnapshot authority and no shadow state.
- [x] FM-008 ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â add ShotEligibilityGate identity/version and invalidation/re-evaluation semantics.
- [ ] Re-run FINAL MASTER INDEPENDENT AUDIT after exact repairs - NEXT_EXACT_ACTION; intentionally not run in this repair turn.
- [ ] Freeze only after independent re-audit returns BLOCKER=0 and MAJOR=0.

Do not create dependency graph, implementation task decomposition, feature code, build/test runtime, dependency install or commit before the freeze gate authorizes them.


Repair completion:
- [x] FM-001 through FM-008 local repair = 8/8 REPAIRED.
- [x] FINAL_MASTER_REPAIR_FM001_FM008_V1.md created.
- [x] Master remains candidate and unfrozen.
- [ ] Independent re-audit required next.
- [ ] Freeze remains blocked until independent re-audit returns BLOCKER=0 and MAJOR=0.

No feature code, build/test runtime, dependency installation, commit, dependency graph or coding task decomposition is authorized by this repair completion.

---

## Independent Final Master Audit V2 Queue - 2026-09-22

Design-document repair only. No implementation/coding tasks are authorized.

- [x] Run FINAL_MASTER_INDEPENDENT_AUDIT_V2 - FAIL: BLOCKER=0, MAJOR=6, MINOR=1, NOTE=1.
- [x] FM2-001 - restore explicit accepted contracts/mappings for SequencePlan, DurationBudget, SceneBudget, NarrativeTrace and ShotExpansion.
- [x] FM2-002 - freeze complete legal GenerationJob per-axis transition contract with guards/evidence.
- [x] FM2-003 - satisfy Ã‚Â§01 canonical component-contract completeness outside Ã‚Â§06-Ã‚Â§41.
- [x] FM2-004 - remove/resolve Topic Intelligence -> Profile Resolver bootstrap cycle.
- [x] FM2-005 - remove/resolve StoryCore <-> StoryGraph authority/order cycle.
- [x] FM2-006 - restore required Narrative Expansion defect-code registry and QA/repair/test mapping.
- [x] FM2-007 - repair malformed literal \n separators in Ã‚Â§102 traceability rows without semantic change.
- [x] FM2-008 - update stale Ã‚Â§100 self-status wording after scoped repair.
- [x] Run Independent Final Master Audit V3 after exact FM2-001 through FM2-008 repairs - NEXT_EXACT_ACTION; intentionally not run in this repair turn.
- [ ] Freeze remains blocked until independent audit returns BLOCKER=0 and MAJOR=0.

No feature code, runtime build/test, dependency installation, commit, dependency graph, implementation task decomposition or coding task is authorized by this queue section.

Repair completion:
- [x] FM2-001 through FM2-008 local repair = 8/8 REPAIRED.
- [x] FINAL_MASTER_REPAIR_FM2_001_FM2_008_V1.md created.
- [x] Contract completeness = 62/62; incomplete = 0.
- [x] Design dependency cycle count = 0.
- [x] Requirement registry = 112/112 independent valid rows.
- [x] Narrative Expansion defect registry = 36/36 exact source-required codes.
- [x] Repair regression self-check = 20/20 PASS.
- [x] Master remains candidate and unfrozen.
- [x] Independent Final Master Audit V3 completed - FAIL: BLOCKER=0, MAJOR=2, MINOR=0, NOTE=0.
- [ ] Freeze remains blocked until an independent audit returns BLOCKER=0 and MAJOR=0.

No feature code, runtime build/test, dependency installation, commit, implementation dependency graph, implementation task decomposition or coding task is authorized by this repair completion.

---

## Independent Final Master Audit V3 Queue - 2026-09-23

Design-document repair only. No implementation/coding tasks are authorized.

- [x] Run FINAL_MASTER_INDEPENDENT_AUDIT_V3 - FAIL: BLOCKER=0, MAJOR=2, MINOR=0, NOTE=0.
- [x] Verify FM2-001 - VERIFIED CLOSED.
- [x] Verify FM2-002 - REGRESSED under FM3-002.
- [x] Verify FM2-003 - NOT CLOSED under FM3-001/FM3-002.
- [x] Verify FM2-004 - VERIFIED CLOSED.
- [x] Verify FM2-005 - VERIFIED CLOSED.
- [x] Verify FM2-006 - VERIFIED CLOSED.
- [x] Verify FM2-007 - VERIFIED CLOSED.
- [x] Verify FM2-008 - VERIFIED CLOSED.
- [ ] FM3-001 - repair exact parent-only/nested-only component contract completeness findings.
- [ ] FM3-002 - separate immutable semantic/version data from mutable coordination state/status semantics in §63/§68/§69/§71.
- [ ] Re-run independent final Master audit only after FM3 findings are repaired.
- [ ] Freeze remains blocked until an independent audit returns BLOCKER=0 and MAJOR=0.

No feature code, runtime build/test, dependency installation, commit, implementation dependency graph, implementation task decomposition or coding task is authorized by this audit result.

Repair claim:
- [>] FM3-001 / FM3-002 = ACTIVE.
- [ ] Local self-audit after repair.
- [ ] Independent final audit after local self-audit.
- [ ] Freeze only if independent final audit returns BLOCKER=0 and MAJOR=0.

Repair claim:
- [>] FM3-001 / FM3-002 = ACTIVE.
- [ ] Local self-audit after repair.
- [ ] Independent final audit after local self-audit.
- [ ] Freeze only if independent final audit returns BLOCKER=0 and MAJOR=0.

FM3 repair completion:
- [x] FM3-001 local repair complete.
- [x] FM3-002 local repair complete.
- [x] Local self-audit complete: 101/101 component contracts.
- [ ] Run Independent Final Master Audit V4.
- [ ] Freeze only if V4 returns BLOCKER=0 and MAJOR=0.

---

## Frozen Baseline V1 Gate - 2026-09-25

- [x] FM3-001 repaired and independently verified.
- [x] FM3-002 repaired and independently verified.
- [x] FINAL_MASTER_INDEPENDENT_AUDIT_V4 = PASS.
- [x] Frozen status mutation completed.
- [x] FROZEN_MASTER_INDEPENDENT_AUDIT_V5 = PASS.
- [x] Freeze manifest created.
- [x] Frozen SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287.
- [x] Master implementation-design baseline V1 = FROZEN.
- [ ] Build implementation dependency graph from frozen Master.
- [ ] Decompose implementation into dependency-ordered tasks with acceptance/evidence gates.
- [ ] Only then claim first implementation task.

Implementation work is now design-authorized but must follow frozen authority, dependency order, per-task verification, evidence, review and MAIN VERIFIED lifecycle.

---

## IMP-001 - Frozen Baseline Guard

- [>] CLAIMED / ACTIVE on chatgpt/IMP-001-frozen-baseline-guard.
- [ ] Implement durable guard.
- [ ] Add fail-closed unit tests.
- [ ] Integrate guard into CI.
- [ ] Run targeted test.
- [ ] Run full unit regression.
- [ ] Capture evidence and verify frozen Master SHA.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.

IMP-001 verification:
- [x] Implement durable guard.
- [x] Add fail-closed unit tests.
- [x] Integrate guard into CI.
- [x] Targeted Python 3.13: 9/9 PASS.
- [x] Local unaffected regression: 371 PASS / 3 exact Windows-only path cases deselected.
- [x] Evidence captured.
- [x] Frozen Master SHA unchanged.
- [ ] Commit.
- [ ] Push branch.
- [ ] Open PR.
- [ ] Ubuntu CI full unit suite.
- [ ] Review exact PR head.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.

---

## IMP-001 Final Verification - 2026-09-25

- [x] Implement durable frozen baseline guard.
- [x] Add fail-closed unit tests.
- [x] Integrate guard into CI.
- [x] Commit initial implementation: efb3f280b4a91cde4de557283c65ecb52bac9b2b.
- [x] Push to writable fork.
- [x] Fork PR #1 opened and exact-head reviewed.
- [x] Fork PR #1 Ubuntu CI Python 3.10/3.13 PASS.
- [x] Fork PR #1 merged.
- [x] Post-merge Windows main verification executed.
- [x] Detected CRLF portability defect before false MAIN VERIFIED claim.
- [x] Repair exact CRLF-only normalization semantics.
- [x] Targeted repair tests 12/12 PASS.
- [x] Fork PR #2 exact-head review PASS.
- [x] Fork PR #2 Ubuntu CI Python 3.10/3.13 PASS.
- [x] Fork PR #2 merged to main at bca229eee5a159a59cc880f48a0d62f1ac78fcc5.
- [x] Windows main frozen guard PASS.
- [x] Fork main push workflow run 36112979014 PASS.
- [x] IMP-001 = MAIN VERIFIED on nguyenkhactang922-bot/flowkit:main.
- [ ] Upstream crisng95/flowkit PR #65 maintainer workflow approval/merge - EXTERNAL PENDING, not claimed complete.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-002 - Canonical Contract Primitives.

---

## IMP-002 - Canonical Contract Primitives

- [>] CLAIMED on chatgpt/IMP-002-canonical-contract-primitives.
- [ ] Implement provider-neutral agent/studio package.
- [ ] Implement logical ID/version/source-version/provenance primitives.
- [ ] Implement lifecycle/gate/finding-severity value objects.
- [ ] Implement immutable semantic record metadata.
- [ ] Add serialization/equality/validation/provider-neutrality tests.
- [ ] Run targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.

IMP-002 local verification:
- [x] Implement provider-neutral agent/studio package.
- [x] Implement logical ID/version/source-version/provenance primitives.
- [x] Implement lifecycle/gate/finding-severity value objects.
- [x] Implement immutable semantic record metadata.
- [x] Add serialization/equality/validation/provider-neutrality tests.
- [x] Targeted tests: 19/19 PASS.
- [x] Full Windows unit suite observed: 407 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 407 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-002 Final Verification - 2026-09-25

- [x] Canonical provider-neutral primitives implemented.
- [x] Targeted exact-head tests: 19/19 PASS.
- [x] Windows unaffected regression: 407 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #4 exact-head reviewed.
- [x] PR #4 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #4 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36117340581 PASS.
- [x] IMP-002 = MAIN VERIFIED at 49a5352fc29c096802ba1d088c5c9739c6be48c3.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-003 - One-Writer Persistence / Migration Foundation.


---

## IMP-003 - One-Writer Persistence / Migration Foundation

- [>] CLAIMED on chatgpt/IMP-003-one-writer-persistence.
- [ ] Add canonical SQLite write-owner foundation.
- [ ] Add bounded write queue.
- [ ] Add transaction + no-network guard.
- [ ] Add CAS/revision helper.
- [ ] Add migration table/version compatibility gate.
- [ ] Enforce WAL/FULL/foreign_keys pragmas.
- [ ] Add separate read path.
- [ ] Add serialized-write/CAS/pressure/migration/FK/PRAGMA tests.
- [ ] Run targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-003 local verification:
- [x] Add canonical SQLite write-owner foundation.
- [x] Add bounded write queue.
- [x] Add transaction + no-network guard.
- [x] Add CAS/revision helper.
- [x] Add migration table/version compatibility gate.
- [x] Enforce WAL/FULL/foreign_keys pragmas.
- [x] Add separate query-only read path.
- [x] Targeted Studio tests: 31/31 PASS.
- [x] IMP-003 persistence tests: 12/12 PASS.
- [x] Full Windows unit suite: 420 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 420 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-003 Final Verification - 2026-09-25

- [x] Canonical one-writer persistence foundation implemented.
- [x] Targeted Studio tests: 31/31 PASS.
- [x] IMP-003 persistence tests: 12/12 PASS.
- [x] Windows unaffected regression: 420 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #6 exact-head reviewed.
- [x] PR #6 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #6 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36122334589 PASS.
- [x] IMP-003 = MAIN VERIFIED at 661fdba57520cf25106d644cd143e82936b0451c.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-004 - Version / Provenance Repository Primitives.


---

## IMP-004 - Version / Provenance Repository Primitives

- [>] CLAIMED on chatgpt/IMP-004-version-provenance-repository.
- [ ] Add Studio schema migration V2 for version/provenance repository.
- [ ] Add immutable semantic version records.
- [ ] Add successor + supersession history.
- [ ] Add mutable current pointer/status separation.
- [ ] Add pointer/status CAS update.
- [ ] Add provenance persistence/readback.
- [ ] Add restart/readback tests.
- [ ] Run targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-004 local verification:
- [x] Add Studio schema migration V2.
- [x] Add immutable semantic version records.
- [x] Add successor + supersession history.
- [x] Add mutable current pointer/status separation.
- [x] Add pointer/status CAS update.
- [x] Add provenance persistence/readback.
- [x] Add restart/readback tests.
- [x] Targeted Studio tests: 39/39 PASS.
- [x] IMP-004 versioning tests: 8/8 PASS.
- [x] Full Windows unit suite: 428 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 428 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-004 Final Verification - 2026-09-25

- [x] Version/provenance repository implemented.
- [x] Targeted Studio tests: 39/39 PASS.
- [x] IMP-004 versioning tests: 8/8 PASS.
- [x] Windows unaffected regression: 428 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #8 exact-head reviewed.
- [x] PR #8 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #8 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36163372531 PASS.
- [x] IMP-004 = MAIN VERIFIED at a5299e88195f8feaf94c1ddf9016ea31af01b84f.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-005 - DependencyGraph + Durable InvalidationRecord.


---

## IMP-005 - DependencyGraph + Durable InvalidationRecord

- [>] CLAIMED on chatgpt/IMP-005-dependency-invalidation.
- [ ] Add Studio schema migration V3.
- [ ] Add typed dependency edge repository.
- [ ] Add direct/transitive forward/reverse reachability.
- [ ] Add durable InvalidationRecord repository.
- [ ] Add deterministic dedupe/idempotency.
- [ ] Add unresolved → resolved CAS lifecycle.
- [ ] Add restart replay of unresolved invalidations.
- [ ] Add selectivity/preserved-unrelated tests.
- [ ] Run targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-005 local verification:
- [x] Add Studio schema migration V3.
- [x] Add typed exact-version dependency edge repository.
- [x] Add forward/reverse reachability.
- [x] Add selective descendant invalidation.
- [x] Add durable InvalidationRecord.
- [x] Add deterministic dedupe/idempotency.
- [x] Add unresolved → resolved CAS lifecycle.
- [x] Add durable transition history.
- [x] Add restart replay.
- [x] Targeted IMP-003/004/005: 28/28 PASS.
- [x] Full Windows unit suite: 436 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 436 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-005 Final Verification - 2026-09-25

- [x] DependencyGraph + durable invalidation implemented.
- [x] Targeted IMP-003/004/005: 28/28 PASS.
- [x] IMP-005 targeted on main: 8/8 PASS.
- [x] Windows unaffected regression: 436 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #10 exact-head reviewed.
- [x] PR #10 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #10 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36166182569 PASS.
- [x] IMP-005 = MAIN VERIFIED at 8e07bb1066b0d0b75b5050c005a443ea71b5ee10.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-006 - Observability / Error / Evidence Core.


---

## IMP-005 Final Verification - 2026-09-25

- [x] DependencyGraph + durable invalidation implemented.
- [x] Targeted IMP-003/004/005: 28/28 PASS.
- [x] IMP-005 targeted on main: 8/8 PASS.
- [x] Windows unaffected regression: 436 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #10 exact-head reviewed.
- [x] PR #10 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #10 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36166182569 PASS.
- [x] IMP-005 = MAIN VERIFIED at 8e07bb1066b0d0b75b5050c005a443ea71b5ee10.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-006 - Observability / Error / Evidence Core.


---

## IMP-006 - Observability / Error / Evidence Core

- [>] CLAIMED on chatgpt/IMP-006-observability-error-evidence.
- [ ] Read exact frozen authority for observability/error/evidence.
- [ ] Audit current logging/error/event surfaces for reuse.
- [ ] Implement typed correlation/evidence/error primitives.
- [ ] Implement deterministic secret redaction.
- [ ] Implement structured decision/failure evidence events.
- [ ] Prove event-vs-current-state separation.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-006 local verification:
- [x] Read frozen observability/error/evidence authority.
- [x] Audit current logging/error/event surfaces.
- [x] Add typed correlation identity + propagation.
- [x] Add exact ErrorClass taxonomy + retry disposition.
- [x] Add provider ambiguity reconciliation invariant.
- [x] Add EvidenceReference + structured DECISION/FAILURE events.
- [x] Add deterministic recursive secret redaction.
- [x] Add append-only evidence event repository.
- [x] Add Studio schema migration V4.
- [x] Prove event-vs-current-state separation.
- [x] Targeted IMP-006: 10/10 PASS.
- [x] Studio V1→V4 cluster: 57/57 PASS.
- [x] Full Windows unit suite: 446 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 446 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-006 Final Verification - 2026-09-26

- [x] Typed correlation/evidence/error core implemented.
- [x] Exact ErrorClass taxonomy + provider ambiguity semantics verified.
- [x] Recursive secret redaction verified, including X-API-Key/X-Access-Token repair.
- [x] Append-only evidence-event persistence verified.
- [x] Event != current-state authority verified.
- [x] Targeted IMP-006: 10/10 PASS.
- [x] Studio V1→V4 cluster: 57/57 PASS.
- [x] Windows unaffected regression: 446 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #12 exact-head reviewed.
- [x] PR #12 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #12 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36211125971 PASS.
- [x] IMP-006 = MAIN VERIFIED at 9aaa98e757adbb5f30deea502c6a1f5cce9e06e1.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-010 - Project / Topic / Domain Resolution.


---

## IMP-010 - Project / Topic / Domain Resolution

- [>] CLAIMED on chatgpt/IMP-010-project-topic-domain.
- [ ] Add ProjectBootstrapInput provider-neutral boundary.
- [ ] Add TopicResolution typed contract.
- [ ] Add Domain/Niche/Genre Resolution typed contract.
- [ ] Add exact-version provenance builders.
- [ ] Add hard-constraint enforcement.
- [ ] Add explicit ambiguity/unknown-niche representation.
- [ ] Add VersionRepository persistence adapter.
- [ ] Prove no ActiveProductionProfile/ProfileResolver dependency.
- [ ] Prove provider-specific legacy fields cannot enter canonical contracts.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-010 local verification:
- [x] Add ProjectBootstrapInput provider-neutral boundary.
- [x] Add TopicResolution typed contract.
- [x] Add Domain/Niche/Genre Resolution typed contract.
- [x] Add exact-version provenance builders.
- [x] Add hard-constraint enforcement.
- [x] Add explicit ambiguity/unknown/hybrid representation.
- [x] Add VersionRepository persistence adapter.
- [x] Prove no ActiveProductionProfile/ProfileResolver dependency.
- [x] Prove provider-specific legacy fields cannot enter canonical contracts.
- [x] Targeted IMP-010: 12/12 PASS.
- [x] Full Windows unit suite: 458 PASS / 3 exact known POSIX-path failures.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-010 Final Verification - 2026-09-26

- [x] ProjectBootstrapInput provider-neutral boundary implemented.
- [x] TopicResolution + service implemented.
- [x] Domain/Niche/Genre Resolution + service implemented.
- [x] Exact-version provenance verified.
- [x] Hard constraints override soft classifier preferences.
- [x] Explicit ambiguity/unknown/hybrid niche semantics verified.
- [x] No ActiveProductionProfile/ProfileResolver dependency in Topic contracts.
- [x] No provider-specific canonical fields.
- [x] VersionRepository persistence round-trip verified.
- [x] Targeted IMP-010: 12/12 PASS.
- [x] PR #14 exact-head reviewed.
- [x] PR #14 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #14 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36225238363 PASS.
- [x] IMP-010 = MAIN VERIFIED at ed5fb0ff0aff746b3991c52f32b282fdec7e444a.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-011 - BrainPack Registry.


---

## IMP-011 - BrainPack Registry

- [>] CLAIMED on chatgpt/IMP-011-brainpack-registry.
- [ ] Audit current VersionRepository/lifecycle storage reuse.
- [ ] Add BrainPack schema + canonical families.
- [ ] Add Story specialization in same registry.
- [ ] Add exact-version parent/applicability contracts.
- [ ] Add registry lifecycle storage.
- [ ] Add provenance/license/source validation.
- [ ] Add inheritance cycle detection.
- [ ] Prove registry definitions != effective resolved policy.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-011 local verification:
- [x] Audit VersionRepository/lifecycle storage reuse.
- [x] Add BrainPack schema + canonical families.
- [x] Add Story specialization in same registry.
- [x] Add exact-version parent/applicability contracts.
- [x] Add registry-specific lifecycle storage/history.
- [x] Add provenance/license/source validation.
- [x] Add donor adaptation/validation gate.
- [x] Add inheritance cycle detection.
- [x] Prove registry definitions != effective resolved policy.
- [x] Add schema V5 migration.
- [x] Targeted IMP-011: 11/11 PASS.
- [x] Targeted cluster: 33/33 PASS.
- [x] Full Windows unit suite: 469 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 469 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-011 Final Verification - 2026-09-26

- [x] One canonical BrainPack registry implemented.
- [x] Canonical families + typed Other family implemented.
- [x] Story specialization stored in same registry.
- [x] Exact parent refs + cycle rejection verified.
- [x] Source/license/donor adaptation validation verified.
- [x] Registry lifecycle DRAFT/VALIDATED/FROZEN/DEPRECATED verified.
- [x] Lifecycle CAS/history/DB guards verified.
- [x] Registry != effective resolved project policy verified.
- [x] Targeted IMP-011: 11/11 PASS.
- [x] Windows unaffected regression: 469 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #16 exact-head reviewed.
- [x] PR #16 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #16 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36227414264 PASS.
- [x] IMP-011 = MAIN VERIFIED at e9347bf7b7b8d34418e268d3bdd11538345c172d.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-012 - Profile Resolver.


---

## IMP-012 - Profile Resolver

- [>] CLAIMED on chatgpt/IMP-012-profile-resolver.
- [ ] Read exact frozen Profile Resolver authority.
- [ ] Audit Topic/Domain/BrainPack contracts for exact inputs.
- [ ] Add typed resolver input contract.
- [ ] Add precedence/conflict/override engine.
- [ ] Add allowlisted project override gate.
- [ ] Add immutable ResolutionTrace with per-field provenance.
- [ ] Add hard-hard conflict fail-closed behavior.
- [ ] Add deterministic/reproducibility tests.
- [ ] Prove downstream cannot independently re-resolve packs.
- [ ] Persist resolver output through immutable VersionRepository.
- [ ] Run targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-012 local verification:
- [x] Read exact frozen Profile Resolver authority.
- [x] Audit Topic/Domain/BrainPack exact input contracts.
- [x] Add typed resolver input contract.
- [x] Add precedence/conflict/override engine.
- [x] Add allowlisted project override gate.
- [x] Add allowlisted local-intent gate.
- [x] Add immutable ResolutionTrace with per-field provenance.
- [x] Add hard-hard conflict fail-closed behavior.
- [x] Add exact pack applicability/inheritance/FROZEN gates.
- [x] Add deterministic resolver-version-sensitive identity.
- [x] Bind all consumed exact sources in persistence provenance.
- [x] Persist resolver output via immutable VersionRepository.
- [x] Prove IMP-012 does not define ActiveProductionProfile.
- [x] Targeted IMP-012: 15/15 PASS.
- [x] Full Windows unit suite: 484 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 484 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-012 Final Verification - 2026-09-26

- [x] Single canonical Profile Resolver implemented.
- [x] Exact Project/Topic/Domain/BrainPack version inputs verified.
- [x] Canonical precedence ladder verified.
- [x] Equal-rank/hard-hard conflicts fail closed.
- [x] Allowlisted project/local override gates verified.
- [x] Immutable ResolutionTrace provenance verified.
- [x] Deterministic resolver-version-sensitive identity verified.
- [x] Persistence through immutable VersionRepository verified.
- [x] No ActiveProductionProfile authority leakage.
- [x] Targeted IMP-012: 15/15 PASS.
- [x] Windows unaffected regression: 484 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #18 exact-head reviewed.
- [x] PR #18 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #18 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36234468266 PASS.
- [x] IMP-012 = MAIN VERIFIED at 99e50aa186222d8ecaefc1db479b15d3343af1b2.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-013 - ActiveProductionProfile.


---

## IMP-013 - ActiveProductionProfile

- [>] CLAIMED on chatgpt/IMP-013-active-production-profile.
- [ ] Read exact frozen ActiveProductionProfile authority.
- [ ] Audit ProfileResolution + DependencyGraph/Invalidation contracts.
- [ ] Add immutable ActiveProductionProfile contract.
- [ ] Add exact profile identity/version persistence.
- [ ] Add per-effective-path provenance snapshot.
- [ ] Add deterministic changed-path delta.
- [ ] Add successor version creation on re-resolution.
- [ ] Add selective dependency-aware invalidation.
- [ ] Prove downstream exact profile binding and no re-resolution.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-013 local verification:
- [x] Read exact ActiveProductionProfile authority.
- [x] Audit ProfileResolution + DependencyGraph/Invalidation contracts.
- [x] Add immutable ActiveProductionProfile contract.
- [x] Add exact profile identity/version persistence.
- [x] Add per-effective-path provenance snapshot.
- [x] Add deterministic changed-path delta.
- [x] Add successor version creation on re-resolution.
- [x] Add selective dependency-aware invalidation.
- [x] Add forged selective-reachability fail-closed validation.
- [x] Prove unrelated profile path remains valid.
- [x] Prove downstream exact profile binding/no re-resolution.
- [x] Targeted IMP-013: 10/10 PASS.
- [x] Exact-head unaffected regression: 494 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-013 Final Verification - 2026-09-26

- [x] Immutable pinned ActiveProductionProfile implemented.
- [x] Exact identity/version/source provenance verified.
- [x] Successor versioning verified.
- [x] Changed-path delta verified.
- [x] Selective invalidation preserves unrelated branches.
- [x] Forged selective reachability fails closed.
- [x] Downstream exact profile binding/no re-resolution verified.
- [x] Targeted IMP-013: 10/10 PASS.
- [x] Exact-head unaffected regression: 494 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #20 exact-head reviewed.
- [x] PR #20 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #20 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36237749060 PASS.
- [x] IMP-013 = MAIN VERIFIED at 62d4efccbaf940e1b18016d39014ba13ec648e96.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-020 - Idea / Logline / Premise / Angle / Theme.


---

## IMP-020 - Idea / Logline / Premise / Angle / Theme

- [>] CLAIMED on chatgpt/IMP-020-story-intake-core.
- [ ] Read exact frozen story-intake authority.
- [ ] Audit current project.story / story-generation surfaces.
- [ ] Add typed Idea/Logline/Premise/Angle/Theme contracts.
- [ ] Add immutable persistence/versioning adapters.
- [ ] Add stage-local blocking gates.
- [ ] Bind exact ActiveProductionProfile where policy is consumed.
- [ ] Prove no project.story shadow canonical authority.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-020 local verification:
- [x] Read exact frozen story-intake authority.
- [x] Audit current project.story / story-generation surfaces.
- [x] Add typed Idea/Logline/Premise/Angle/Theme contracts.
- [x] Add immutable persistence/versioning adapters.
- [x] Add stage-local blocking gates.
- [x] Bind exact ActiveProductionProfile where policy is consumed.
- [x] Prove no project.story shadow canonical authority.
- [x] Add targeted tests.
- [x] Targeted IMP-020: 13/13 PASS.
- [x] Full Windows unit suite: 507 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 507 PASS / 3 deselected.
- [x] Frozen Master guard PASS; SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-020 Final Verification - 2026-09-26

- [x] Canonical Idea implemented.
- [x] Canonical Logline implemented.
- [x] Canonical Premise implemented.
- [x] Canonical Angle implemented.
- [x] Canonical Theme implemented.
- [x] Exact ActiveProductionProfile/source-version provenance verified.
- [x] Stage-local blocking gates verified.
- [x] Stale parent/profile inputs fail closed.
- [x] Immutable successor/current-authority behavior verified.
- [x] Legacy project.story compatibility-only boundary verified.
- [x] Targeted IMP-020: 13/13 PASS.
- [x] Windows unaffected regression: 507 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #22 exact-head reviewed.
- [x] PR #22 Ubuntu CI Python 3.10/3.13 PASS.
- [x] PR #22 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36257937119 PASS.
- [x] IMP-020 = MAIN VERIFIED at 1ea70be1a6a284009f7c399299c4eab027858d21.

NEXT DEPENDENCY-READY TASK:
- [ ] Read TASK_QUEUE / IMPLEMENTATION_TASK_DECOMPOSITION and claim next story task.


---

## IMP-021 - Research Intelligence + StoryMaterial

- [>] CLAIMED on chatgpt/IMP-021-research-story-material.
- [ ] Read exact frozen Research Intelligence / StoryMaterial authority.
- [ ] Audit current research/factuality/story-material surfaces.
- [ ] Add typed ResearchBrief contract.
- [ ] Add typed EvidenceClaim contract with exact provenance.
- [ ] Add explicit certainty/dispute/contradiction semantics.
- [ ] Add typed StoryMaterial transformation contract.
- [ ] Reject unsupported synthesis.
- [ ] Add immutable persistence/versioning adapters.
- [ ] Bind exact ActiveProductionProfile where policy is consumed.
- [ ] Add targeted tests.
- [ ] Run full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / review / merge / MAIN VERIFIED.


IMP-021 local verification:
- [x] Read exact frozen Research Intelligence / StoryMaterial authority.
- [x] Audit current research/factuality/story-material surfaces.
- [x] Add typed ResearchBrief contract.
- [x] Add typed EvidenceClaim contract with exact provenance.
- [x] Add explicit certainty/dispute/contradiction semantics.
- [x] Add typed StoryMaterial transformation contract.
- [x] Reject unsupported synthesis.
- [x] Add immutable persistence/versioning adapters.
- [x] Bind exact ActiveProductionProfile where policy is consumed.
- [x] Add targeted tests.
- [x] Targeted IMP-021: 10/10 PASS.
- [x] Full Windows unit suite: 517 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 517 PASS / 3 deselected.
- [x] Frozen Master guard PASS; canonical SHA unchanged.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


IMP-021 exact-head review repair:
- [x] Review exact PR head a6b6ec56a63082e4ed74e8db7f1b33f0421a224a.
- [x] Find authority gap: ResearchBrief did not enforce canonical/current TopicResolution + DomainResolution.
- [x] Correct DomainResolution logical ID to niche-resolution:<project>.
- [x] Reject cross-project/noncanonical Topic/Domain refs.
- [x] Reject stale Topic/Domain versions at promotion.
- [x] Post-repair targeted IMP-021: 13/13 PASS.
- [x] Post-repair full Windows unit suite: 520 PASS / 3 exact known POSIX-path failures.
- [x] Post-repair unaffected regression: 520 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [ ] Commit review repair.
- [ ] Push updated PR #24.
- [ ] Updated-head Ubuntu CI Python 3.10/3.13.
- [ ] Updated-head exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


---

## IMP-021 Final Verification - 2026-09-29

- [x] Canonical ResearchBrief implemented.
- [x] Canonical EvidenceClaim implemented with exact source/version provenance.
- [x] Supported/disputed/unsupported certainty semantics verified.
- [x] Exact contradiction refs verified.
- [x] Canonical StoryMaterial transformation preserves evidence truth.
- [x] Unsupported synthesis fails closed.
- [x] Canonical/current TopicResolution and DomainResolution gates verified.
- [x] Exact pinned ActiveProductionProfile gate verified.
- [x] Immutable successor/history behavior verified.
- [x] Targeted IMP-021 = 13/13 PASS.
- [x] Windows unaffected regression = 520 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #24 updated exact head = 9e39583e8d5b794c30880f69c1d01ecbcf0499ee.
- [x] PR #24 Ubuntu CI Python 3.10/3.13 PASS.
- [x] Exact-head review PASS after authority repair.
- [x] PR #24 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36544062680 PASS.
- [x] IMP-021 = MAIN VERIFIED at 6370e1174b111a69c08f842224f335db42d160ad.

NEXT DEPENDENCY-READY TASK:
- [ ] Recompute from frozen implementation dependency graph.


---

## IMP-040 - Canonical Entity Versioning Adapter - 2026-09-29

- [x] Claim dependency-ready IMP-040 from frozen DAG.
- [x] Read frozen §56 Entity authority and legacy Character/entity surfaces.
- [x] Add canonical EntityVersion contract.
- [x] Add stable legacy entity -> canonical logical-ID mapping.
- [x] Add legacy anti-corruption snapshot and compatibility binding.
- [x] Reuse shared VersionRepository; do not create second canonical Entity store.
- [x] Preserve project linkage.
- [x] Keep reference media/provider prompt outside canonical Entity truth.
- [x] Add successor/current-pointer behavior.
- [x] Add targeted tests: 7/7 PASS.
- [x] Related regression cluster: 35/35 PASS.
- [x] Full Windows unit suite observed: 527 PASS / 3 exact known POSIX-path failures.
- [x] Unaffected regression: 527 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [x] git diff --check PASS.
- [x] Evidence captured.
- [ ] Commit intentional IMP-040 files.
- [ ] Push branch.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge fork main.
- [ ] Verify fork main and mark MAIN VERIFIED.

NEXT_EXACT_ACTION:
- [ ] Complete IMP-040 remote lifecycle; only then claim IMP-022 critical-path story task.


---

## IMP-040 Final Verification - 2026-09-29

- [x] Canonical EntityVersion implemented.
- [x] Stable legacy entity -> canonical logical-ID mapping verified.
- [x] Legacy anti-corruption snapshot/binding verified.
- [x] Shared VersionRepository reused; no shadow canonical Entity store.
- [x] Reference media/provider prompt excluded from Entity semantic truth.
- [x] Successor/current-pointer semantics verified.
- [x] Targeted IMP-040 = 7/7 PASS.
- [x] Related regression cluster = 35/35 PASS.
- [x] Windows unaffected regression = 527 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] PR #25 exact head = ed33a8bb7e2052c765d669d43008df3483d7b448.
- [x] PR #25 Ubuntu CI Python 3.10/3.13 PASS.
- [x] Exact-head review PASS.
- [x] PR #25 merged.
- [x] Local main targeted verification PASS.
- [x] Main push workflow run 36552171606 PASS.
- [x] IMP-040 = MAIN VERIFIED at 01830d2a90f37ab4cac86f360798611940c07065.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-022 - Character Psychology / Relationship / Knowledge.


---

## IMP-022 - Character Psychology / Relationship / Knowledge

- [>] CLAIMED on chatgpt/IMP-022-character-state.
- [x] Read frozen §§18-20 and FR-039/FR-040 authority.
- [x] Read historical CharacterModelVersion / CharacterKnowledgeState / RelationshipState canonical contracts.
- [x] Audit current canonical EntityVersion + VersionRepository / invalidation primitives.
- [ ] Add CharacterModelVersion typed contract and repository.
- [ ] Add RelationshipState typed contract with chronology/cause rules.
- [ ] Add CharacterKnowledgeState typed contract with objective-vs-belief separation.
- [ ] Add exact current-input gates and immutable successor behavior.
- [ ] Add impossible-knowledge / chronology / stale-input tests.
- [ ] Run targeted tests.
- [ ] Run affected regression and full unit regression.
- [ ] Capture evidence + frozen SHA verification.
- [ ] Commit / push / PR / CI / exact-head review / merge / MAIN VERIFIED.


IMP-022 local verification:
- [x] Add CharacterModelVersion typed contract and repository.
- [x] Add RelationshipState typed contract with chronology/cause rules.
- [x] Add CharacterKnowledgeState typed contract with objective-vs-belief separation.
- [x] Add exact current-input gates and immutable successor behavior.
- [x] Register exact source dependencies in durable DependencyGraph.
- [x] Add impossible-knowledge / chronology / stale-input / invalidation tests.
- [x] Targeted IMP-022: 11/11 PASS.
- [x] Affected regression cluster: 60/60 PASS.
- [x] Largest valid unaffected regression: 509 PASS / 3 deselected.
- [x] Record full local suite environment blockers: missing ffmpeg + 3 known Windows/POSIX assertions.
- [x] Frozen Master guard PASS; canonical SHA unchanged.
- [x] Compile + git diff --check PASS.
- [x] Evidence captured.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13 full suite.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main and mark MAIN VERIFIED.


IMP-022 exact-head review repair:
- [x] Review merged PR #27 exact head 3d14a9d1a4d47e73a311630f5c23d390a7514854.
- [x] Reverify initial head already exact-current gates objective/acquisition/inference evidence.
- [x] Require EntityKind.CHARACTER for psychology/knowledge.
- [x] Preflight all exact source versions before semantic persistence.
- [x] Add non-character EntityKind rejection test.
- [x] Add missing-source-before-persistence test.
- [x] Post-repair targeted IMP-022: 13/13 PASS.
- [x] Post-repair affected regression: 74/74 PASS.
- [x] Post-repair unaffected regression: 511 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [x] Post-merge repair committed on dedicated branch.
- [ ] Push repair branch.
- [ ] Open separate repair PR.
- [ ] Repair PR Ubuntu CI Python 3.10/3.13.
- [ ] Final exact-head review.
- [ ] Merge repair to main.
- [ ] Verify main and mark IMP-022 MAIN VERIFIED.

IMP-022 post-merge repair routing:
- [x] Recheck PR #27 before retrying side effects.
- [x] Detect PR #27 already merged; no duplicate update/retry.
- [x] Verify original PR #27 CI SUCCESS.
- [x] Verify original main push workflow 36597573229 SUCCESS.
- [x] Preserve review hardening in separate branch chatgpt/IMP-022-postmerge-review-repair.
- [ ] Push repair branch.
- [ ] Open separate repair PR.
- [ ] Repair PR Ubuntu CI Python 3.10/3.13.
- [ ] Final exact-head review.
- [ ] Merge repair to main.
- [ ] Verify main and mark IMP-022 MAIN VERIFIED.


---

## IMP-022 Final Verification - 2026-09-29

- [x] CharacterModelVersion canonical psychology contract.
- [x] RelationshipState causal chronology.
- [x] CharacterKnowledgeState objective-vs-belief/knowledge separation.
- [x] Exact-version provenance and durable dependency edges.
- [x] Impossible-knowledge fail-closed.
- [x] EntityKind.CHARACTER hardening for psychology/knowledge.
- [x] Missing-source preflight before semantic persistence.
- [x] Targeted final main IMP-022 = 13/13 PASS.
- [x] PR #27 Python 3.10/3.13 CI PASS.
- [x] Post-merge review identified hardening gaps without retrying merged PR.
- [x] PR #28 exact head = 7be73ce6f455056fd92e8f1b93e82f3aab6d7e01.
- [x] PR #28 Python 3.10/3.13 CI PASS.
- [x] Final exact-head review PASS.
- [x] PR #28 merged.
- [x] Local final main frozen guard PASS.
- [x] Local final main targeted IMP-022 = 13/13 PASS.
- [x] Main push workflow 36599591595 PASS.
- [x] IMP-022 = MAIN VERIFIED at 3bde9b95f3da641c89c7d140d9e261780ad63191.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-023 - StoryCore + CausalStoryGraph + Lock.

---

## IMP-023 ACTIVE - 2026-09-30

- [x] CLAIM branch chatgpt/IMP-023-storycore-causal-lock from 0bc64459a5cb3a7e084e8e825381d98ba21b7875.
- [x] Verify worktree: only pre-existing untracked _incoming/.
- [x] Read Frozen Master StoryCore/Conflict-Stakes/StoryGraph/Lock authority.
- [x] Read implementation decomposition and existing Version/Dependency/Invalidation patterns.
- [ ] Implement typed StoryCore + ConflictModel/StakesModel + StoryGraph + causal validation + lock.
- [ ] Targeted IMP-023 tests.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + diff check.
- [ ] Commit → push → PR → CI → exact-head review → merge main → verify main.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-023 CONTRACTS/REPOSITORIES/GATES + TARGETED TESTS"

- [x] Targeted IMP-023 tests = 9/9 PASS (exit 0).
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + diff check.
- [ ] Commit → push → PR → CI → exact-head review → merge main → verify main.

NEXT_EXACT_ACTION = "RUN IMP-023 AFFECTED REGRESSION"

---

## IMP-023 LOCAL VERIFIED - 2026-09-30

- [x] Implement StoryCore + ConflictModel/StakesModel + CausalStoryGraph + causal validation + lock.
- [x] Authority hardening review + 3 negative repair tests.
- [x] Targeted IMP-023 = 12/12 PASS.
- [x] Affected regression = 77/77 PASS.
- [x] Largest valid Windows regression = 523 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] Evidence recorded.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open/reuse PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD → COMMIT IMP-023"


---

## IMP-023 PR #30 REVIEW REPAIR - 2026-09-30

- [x] Pre-repair exact-head CI run 36669953970 PASS on 98225f121d71145327ec1fe3fb7a1866b5df87aa.
- [x] Exact-head review found stale predecessor branching + cross-project lock-manifest schema gaps.
- [x] Repair implementation complete.
- [x] Targeted IMP-023 = 17/17 PASS.
- [x] Affected regression = 82/82 PASS.
- [x] Largest valid Windows regression = 528 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [ ] Commit repair.
- [ ] Push repair to PR #30.
- [ ] New exact-head Ubuntu CI Python 3.10/3.13.
- [ ] Final exact-head review PASS.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "COMMIT EXACT-HEAD REVIEW REPAIR -> PUSH TO PR #30"


---

## IMP-023 MAIN VERIFIED - 2026-09-30

- [x] StoryCore + ConflictModel/StakesModel + CausalStoryGraph + causal validation + lock implemented.
- [x] Targeted final = 17/17 PASS.
- [x] Affected regression final = 82/82 PASS.
- [x] Frozen Master guard PASS.
- [x] PR #30 final exact-head CI run 36670609338 PASS on 83bcc387bcd7116b8312a54e763f2ce745c52d88.
- [x] Final exact-head review PASS.
- [x] PR #30 merged.
- [x] Main = b0a1663ef5155e7a98711cfddfb5bef264962269.
- [x] Local main targeted + affected + frozen guard PASS.
- [x] Main push run 36670754503 PASS for Python 3.10 + 3.13.
- [x] IMP-023 = MAIN VERIFIED.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-024 - StructureProfile / MacroBeatSheet / DurationBudget.

NEXT_EXACT_ACTION = "CLAIM IMP-024 STRUCTUREPROFILE / MACROBEATSHEET / DURATIONBUDGET"


---

## IMP-024 ACTIVE - 2026-09-30

- [x] Existing branch recovered: chatgpt/IMP-024-structure-profile-budget.
- [x] Base verified: 066ce0f2f0c53943fab2e5147ba8d05f48a02cde.
- [x] Worktree verified: only pre-existing untracked _incoming/.
- [x] Side-effect guard: no remote IMP-024 branch, no PR.
- [x] Dependencies verified: IMP-023 + IMP-013 MAIN VERIFIED.
- [ ] Read full StructureProfile / MacroBeatSheet / DurationBudget frozen authority.
- [ ] Audit current structure/planning implementation and shared persistence/invalidation patterns.
- [ ] Implement IMP-024.
- [ ] Targeted + negative tests.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "READ FULL IMP-024 FROZEN AUTHORITY + AUDIT CURRENT STRUCTURE/PLANNING CODE SURFACE"


- [x] Targeted IMP-024 = 10/10 PASS (exit 0).
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "RUN IMP-024 AFFECTED REGRESSION"


---

## IMP-024 LOCAL VERIFIED - 2026-09-30

- [x] StructureProfile immutable range policy.
- [x] ProjectBootstrapInput / DomainResolution authority binding.
- [x] DurationBudget hierarchy + tolerance reconciliation.
- [x] MacroBeatSheet ordered reference projection with no MacroStoryBeat truth duplication.
- [x] exact-version/current gates + stale predecessor fail-closed.
- [x] durable dependency edges + invalidation.
- [x] Targeted IMP-024 = 12/12 PASS.
- [x] Affected regression = 67/67 PASS.
- [x] Largest valid Windows regression = 540 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] Evidence recorded.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-024"


---

## IMP-024 PR #32 REVIEW REPAIR - 2026-09-30

- [x] Pre-repair PR #32 CI PASS on head 9da1b2cf344b85d20d4c7abdf4544a8e8b843199.
- [x] Exact-head review found project-prefix collision, stale project/domain source, topic-lineage, and zero-count range bypass gaps.
- [x] Repair implementation complete.
- [x] Targeted IMP-024 = 16/16 PASS.
- [x] Affected regression = 71/71 PASS.
- [x] Largest valid Windows regression = 544 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] git diff --check PASS.
- [ ] Commit repair.
- [ ] Push repair to PR #32.
- [ ] New exact-head Ubuntu CI Python 3.10/3.13.
- [ ] Final exact-head review PASS.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "COMMIT IMP-024 REVIEW REPAIR -> PUSH PR #32"


---

## IMP-024 FINAL VERIFICATION - 2026-09-30

- [x] StructureProfile immutable range policy.
- [x] DurationBudget typed hierarchical runtime allocation.
- [x] MacroBeatSheet projection-only authority.
- [x] Project/Domain/Topic exact lineage hardening.
- [x] Prefix-collision same-project hardening.
- [x] Missing-level zero-count range bypass removed.
- [x] Targeted final IMP-024 = 16/16 PASS.
- [x] Affected regression final = 71/71 PASS.
- [x] Frozen Master guard PASS.
- [x] PR #32 final exact-head CI run 36685639854 PASS on b610f2a2231b2d214932fc652df8d8329f328060.
- [x] Final exact-head review PASS.
- [x] PR #32 merged.
- [x] Feature main = 1f2d13385c80738177263f84c94c66d220f45be9.
- [x] Local main targeted + affected + frozen guard PASS.
- [x] Main push run 36685898846 PASS for Python 3.10 + 3.13.
- [x] IMP-024 = MAIN VERIFIED.
- [ ] Governance state sync commit / PR / merge.
- [ ] CLAIM IMP-025 after governance sync is on main.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-025 - MacroStoryBeat / SequencePlan / Sequence / SceneBudget / Scene / SceneBreakdown / SceneDramaticBeat.

NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-024 GOVERNANCE SYNC -> CLAIM IMP-025"


---

## IMP-025 ACTIVE - 2026-09-30

- [x] Branch recovered/created: chatgpt/IMP-025-narrative-hierarchy.
- [x] Base verified: c546378694d97a3b88f8f65bb212548f1040f8fe.
- [x] Worktree verified: only pre-existing untracked _incoming/.
- [x] Dependencies verified: IMP-024 + IMP-005 MAIN VERIFIED.
- [ ] Read full MacroStoryBeat / SequencePlan / Sequence / SceneBudget / Scene / SceneBreakdown / SceneDramaticBeat frozen authority.
- [ ] Audit current narrative hierarchy/planning implementation.
- [ ] Implement IMP-025.
- [ ] Targeted + negative tests.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "READ FULL IMP-025 FROZEN AUTHORITY + AUDIT CURRENT NARRATIVE HIERARCHY / PLANNING SURFACES"


- [x] IMP-025 typed contracts/repository/export/traversal implemented.
- [x] Targeted + negative tests = 11/11 PASS.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head self-review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "RUN IMP-025 AFFECTED REGRESSION"


---

## IMP-025 LOCAL VERIFIED - 2026-09-30

- [x] Frozen authority / ADR-0018 read and reconciled.
- [x] Canonical MacroStoryBeat / Sequence / Scene / SceneDramaticBeat implemented.
- [x] SequencePlan / SceneBudget / SceneListManifest / SceneBreakdownManifest remain planning/projection only.
- [x] Shared immutable versioning + CAS/current gates.
- [x] Shared dependency graph + bidirectional ancestry traversal.
- [x] Shared dependency-reachable invalidation.
- [x] Targeted + negative IMP-025 = 11/11 PASS.
- [x] Affected regression = 95/95 PASS.
- [x] Largest valid Windows regression = 555 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] Exact-head self-review PASS.
- [x] Evidence recorded.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-025"


---

## IMP-025 FINAL VERIFICATION - 2026-09-30

- [x] Canonical MacroStoryBeat / Sequence / Scene / SceneDramaticBeat implemented.
- [x] Planning/projection artifacts remain non-authoritative.
- [x] Targeted final IMP-025 = 11/11 PASS.
- [x] Affected regression final = 95/95 PASS.
- [x] Frozen Master guard PASS.
- [x] PR #34 exact-head CI run 36695592106 PASS on 0582bf9d075008ee54fb7a78c1689eb115447e02.
- [x] Final exact-head review PASS.
- [x] PR #34 merged.
- [x] Feature main = ce2108a72c2e198ef7a73ef8317195b5f1950b32.
- [x] Local main targeted + affected + frozen guard PASS.
- [x] Main push run 36695853857 PASS for Python 3.10 + 3.13.
- [x] IMP-025 = MAIN VERIFIED.
- [ ] Governance state sync commit / PR / merge.
- [ ] CLAIM IMP-026 after governance sync is on main.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-026 - Dialogue / Setup-Payoff / Screenplay Realization.

NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-025 GOVERNANCE SYNC -> CLAIM IMP-026"


---

## IMP-026 ACTIVE - 2026-09-30

- [x] Branch created: chatgpt/IMP-026-screenplay-realization.
- [x] Base verified: 0672edaac2c8a8ec8bd39e0dd6fffa9cde1f6c5d.
- [x] Worktree verified: only pre-existing untracked _incoming/.
- [x] Dependencies verified: IMP-025 + IMP-022 MAIN VERIFIED.
- [ ] Read full Dialogue / Setup-Payoff / Screenplay frozen authority.
- [ ] Audit current dialogue/screenplay implementation surfaces.
- [ ] Implement IMP-026.
- [ ] Targeted + negative tests.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "READ FULL IMP-026 FROZEN AUTHORITY + AUDIT CURRENT DIALOGUE/SCREENPLAY SURFACES"


- [x] IMP-026 typed contracts/repository/export implemented.
- [x] Authority hardening: graph PAYS_OFF trace, exact SceneBreakdownManifest coverage, direct Scene-realization binding.
- [x] Targeted + negative tests = 11/11 PASS.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head self-review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "RUN IMP-026 AFFECTED REGRESSION"


---

## IMP-026 LOCAL VERIFIED - 2026-09-30

- [x] Frozen Dialogue / Setup-Payoff / Screenplay authority read.
- [x] DialogueIntent / SetupPayoffLink / ScreenplayScene / FullScreenplay implemented.
- [x] Exact speaker EntityVersion + knowledge discipline.
- [x] StoryGraph SETUP/PAYOFF + PAYS_OFF trace hardening.
- [x] Exact SceneBreakdownManifest beat coverage/order.
- [x] Direct canonical Scene + ScreenplayScene realization binding.
- [x] Targeted final = 12/12 PASS.
- [x] Affected regression final = 114/114 PASS.
- [x] Largest valid Windows regression = 567 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] Exact-head self-review PASS.
- [x] Evidence recorded.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-026"


---

## IMP-026 FINAL VERIFICATION - 2026-09-30

- [x] DialogueIntent / SetupPayoffLink / ScreenplayScene / FullScreenplay implemented.
- [x] Targeted final IMP-026 = 12/12 PASS.
- [x] Affected regression final = 114/114 PASS.
- [x] Frozen Master guard PASS.
- [x] PR #36 exact-head CI run 36702830926 PASS on 01443f365114584b4a62a677b2b904695efb7f98.
- [x] Final exact-head review PASS.
- [x] PR #36 merged.
- [x] Feature main = 5e8b20b6a2770488cfbe0f8e0b6cf9c8b6173155.
- [x] Local main targeted + affected + frozen guard PASS.
- [x] Main push run 36703362942 PASS for Python 3.10 + 3.13.
- [x] IMP-026 = MAIN VERIFIED.
- [ ] Governance state sync commit / PR / merge.
- [ ] CLAIM IMP-027 after governance sync is on main.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-027 - Story Critique / Root Cause / Repair / Quality Gate / ScriptLock.

NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-026 GOVERNANCE SYNC -> CLAIM IMP-027"


---

## IMP-027 ACTIVE - 2026-09-30

- [x] Branch created: chatgpt/IMP-027-story-quality-lock.
- [x] Base verified: fd1ef88f42e53ce34e356821eea44ec7fe64b27f.
- [x] Worktree verified: only pre-existing untracked _incoming/.
- [x] Dependencies verified: IMP-026 + IMP-006 MAIN VERIFIED.
- [ ] Read full Story Critique / Root Cause / Story Repair / Quality Gate / ScriptLock authority.
- [ ] Audit current critique/quality/lock implementation surfaces.
- [ ] Implement IMP-027.
- [ ] Targeted + negative tests.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "READ FULL IMP-027 FROZEN AUTHORITY + AUDIT CURRENT CRITIQUE/REPAIR/QUALITY/LOCK SURFACES"


- [x] IMP-027 typed contracts/repository/export implemented.
- [x] Targeted + negative tests = 12/12 PASS.
- [ ] Affected regression.
- [ ] Broader regression.
- [ ] Frozen Master guard.
- [ ] Evidence + exact-head self-review.
- [ ] Commit / push / PR / CI / merge / main verify.

NEXT_EXACT_ACTION = "RUN IMP-027 AFFECTED REGRESSION"


---

## IMP-027 LOCAL VERIFIED - 2026-09-30

- [x] Frozen critique / root-cause / repair / quality / lock authority read.
- [x] CritiqueFinding / RootCauseLocalization / StoryRepairPlan / StoryQualityResult / ScriptLockManifest implemented.
- [x] Targeted final = 13/13 PASS.
- [x] Affected regression final = 127/127 PASS.
- [x] Largest valid Windows regression = 580 PASS / 3 known POSIX-path cases deselected.
- [x] Frozen Master guard PASS.
- [x] Exact-head self-review PASS.
- [x] Evidence recorded.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-027"


---

## IMP-027 FINAL VERIFICATION - 2026-09-30

- [x] CritiqueFinding / RootCauseLocalization / StoryRepairPlan / StoryQualityResult / ScriptLockManifest implemented.
- [x] Targeted final IMP-027 = 13/13 PASS.
- [x] Affected regression final = 127/127 PASS.
- [x] Frozen Master guard PASS.
- [x] PR #38 exact-head CI run 36708712848 PASS on fb607fdaa6ede42e03be3ff4c8bc188542cf2497.
- [x] Final exact-head review PASS.
- [x] PR #38 merged.
- [x] Feature main = 8399fe76a4c7e7dc08010b6f442ef64a0d09bb4c.
- [x] Local main targeted + affected + frozen guard PASS.
- [x] Main push run 36708995131 PASS for Python 3.10 + 3.13.
- [x] IMP-027 = MAIN VERIFIED.
- [ ] Governance state sync commit / PR / merge.
- [ ] CLAIM IMP-028 after governance sync is on main.

NEXT DEPENDENCY-READY TASK:
- [ ] IMP-028 - NarrativeTrace
  - Depends: IMP-025, IMP-027, IMP-005
  - Goal: bidirectional exact-version ancestry
  - Deliverables: trace repo/index, orphan/cycle detection, why-exists traversal

NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-027 GOVERNANCE SYNC -> CLAIM IMP-028"


---

## IMP-028 CLAIMED - 2026-10-03

- [x] Reconcile restored repo with GitHub source of truth.
- [x] Verify PR #39 governance sync already merged; do not retry.
- [x] Verify no active IMP-028 runtime process.
- [x] Verify no pre-existing remote `chatgpt/IMP-028-narrative-trace` branch.
- [x] Claim branch `chatgpt/IMP-028-narrative-trace` from main `229ccfb227e748f594fb1f9e8d53040095910c9e`.
- [ ] Audit VersionRepository / DependencyGraph / NarrativeHierarchy exact-version surfaces.
- [ ] Implement NarrativeTrace repository/index + validation.
- [ ] Add top-down / bottom-up / orphan / missing-parent / cycle / exact-version provenance tests.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "AUDIT SHARED VERSION/DEPENDENCY/NARRATIVE HIERARCHY SURFACES -> IMPLEMENT IMP-028 NARRATIVETRACE + TARGETED TESTS"


---

## IMP-028 LOCAL VERIFIED - 2026-10-03

- [x] Authority / shared VersionRepository / DependencyGraph / NarrativeHierarchy audit.
- [x] NarrativeTrace immutable trace repo/index implemented.
- [x] Exact structural parent/root validation implemented.
- [x] Top-down / bottom-up / why-exists traversal implemented.
- [x] `TRACE_MISSING_PARENT` / `TRACE_ORPHAN_ARTIFACT` / `TRACE_CYCLE` fail-closed tests.
- [x] Exact provenance + source supersession state tests.
- [x] §63 `narrative_trace_source` dependency edges + durable invalidation propagation verified.
- [x] Targeted final = 13/13 PASS.
- [x] Affected regression final = 98/98 PASS.
- [x] Largest valid Windows regression = 580 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [x] compileall + git diff --check PASS.
- [x] Evidence recorded: `evidence/tests/IMP-028_NARRATIVE_TRACE_EVIDENCE.md`.
- [x] Side-effect guard.
- [x] Commit `6764a887f9d8c512b0d3db43ebd6f7fee5312879`.
- [x] Push exact head `6764a887f9d8c512b0d3db43ebd6f7fee5312879`.
- [x] Open PR #40.
- [x] Initial Ubuntu CI Python 3.10/3.13 + frozen guard PASS on `6764a887...`.
- [x] Exact-head review found transitive durable invalidation gap; repair implemented and locally verified.
- [ ] Push review-fix head + rerun Ubuntu CI.
- [ ] Final exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "COMMIT/PUSH PR #40 REVIEW FIX -> RERUN UBUNTU CI -> FINAL EXACT-HEAD REVIEW -> MERGE -> VERIFY MAIN"

- PR #40 exact-head review hardening = transitive durable invalidation gap repaired; post-fix targeted 13/13, affected 98/98, broader 580 PASS / 3 deselected, frozen guard PASS.


---

## IMP-028 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature commit + review-fix pushed.
- [x] PR #40 final head `f18955e68945fe7252443392768233120f129bb9`.
- [x] PR CI Python 3.10 + 3.13 SUCCESS on final head.
- [x] Final exact-head review PASS after transitive invalidation repair.
- [x] PR #40 merged.
- [x] Main merge SHA `32e078c7225b27eb54b3ed4536ec0d792efec98d`.
- [x] Post-merge targeted = 13/13 PASS.
- [x] Post-merge affected = 98/98 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37097099717` SUCCESS on exact merge SHA.
- [x] IMP-028 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-028 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-041 CLAIMED - 2026-10-03

- [x] Verify IMP-028 governance PR #41 merged at `80671b9a46b057285e9c1476ae266990e87be6a4`.
- [x] Verify governance push-main workflow `37097429052` SUCCESS.
- [x] Verify IMP-041 dependencies: IMP-040 + IMP-005 + IMP-013 MAIN VERIFIED.
- [x] Verify no remote/pr duplicate for `chatgpt/IMP-041-reference-asset-resolver`.
- [x] Claim branch from clean main `80671b9a46b057285e9c1476ae266990e87be6a4`.
- [ ] Read frozen ReferenceAsset/Resolver authority.
- [ ] Audit canonical EntityVersion + media/reference reuse + invalidation surfaces.
- [ ] Implement ReferenceAsset/version/hash/role + resolver trace + provider binding projection.
- [ ] Tests: role selection, stale ref invalidation, UUID/media compatibility, no reference-as-state.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-041 FROZEN AUTHORITY + AUDIT ENTITY/MEDIA/REFERENCE/INVALIDATION SURFACES BEFORE CODE"


---

## IMP-041 LOCAL VERIFIED - 2026-10-03

- [x] Resume from materialized draft after stream interruption; no task restart.
- [x] Frozen Reference System / FM-005 authority read.
- [x] Canonical EntityVersion + legacy media/reference + shared invalidation surfaces audited.
- [x] ReferenceAsset/version/hash/role + deterministic project/entity/slot identity implemented.
- [x] Legacy UUID/media compatibility projection implemented without Entity shadow truth.
- [x] Minimal deterministic Reference Resolver + exact resolution trace/provenance implemented.
- [x] Consumer binding exact-version dependency edges + bind-time stale race revalidation implemented.
- [x] FM-005 successor-promotion bypass found in self-review and closed.
- [x] Successor activation durably invalidates old ReferenceVersion consumers before current-pointer move.
- [x] Targeted final = 13/13 PASS.
- [x] Affected regression final = 46/46 PASS.
- [x] Largest valid Windows regression = 593 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [x] compileall + git diff --check PASS.
- [x] Provider/runtime authority leakage scan PASS.
- [x] Evidence recorded: `evidence/tests/IMP-041_REFERENCE_ASSET_RESOLVER_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Commit.
- [ ] Push.
- [ ] Open PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Verify main / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-041 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-041 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature commit `e1425ee94147a93fbfc198c9617e7f66f26e154f`.
- [x] PR #42 exact-head Ubuntu CI Python 3.10/3.13 + frozen guard SUCCESS (`37105500213`).
- [x] Final exact-head review PASS.
- [x] PR #42 merged.
- [x] Main merge SHA `dd5cf60fffdbcb18035271d0441fbc100538aa6a`.
- [x] Post-merge targeted = 13/13 PASS.
- [x] Post-merge affected = 46/46 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37105602945` SUCCESS exact merge SHA.
- [x] IMP-041 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-041 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-042 CLAIMED - 2026-10-03

- [x] Verify IMP-041 feature PR #42 MAIN VERIFIED.
- [x] Verify IMP-041 governance PR #43 merged at `55ba8d747db11c52417d6d9dfe1b67a807de604e`.
- [x] Verify governance push-main workflow `37105880072` SUCCESS.
- [x] Verify IMP-042 dependencies: IMP-041 + IMP-004 + IMP-005 MAIN VERIFIED.
- [x] Verify no remote/pr duplicate for `chatgpt/IMP-042-state-continuity`.
- [x] Claim branch from clean main `55ba8d747db11c52417d6d9dfe1b67a807de604e`.
- [ ] Read frozen StateSnapshot / ContinuityLedger / ApprovedEndState authority.
- [ ] Audit current media-chain continuity + EntityVersion + DependencyGraph/Invalidation surfaces.
- [ ] Implement StateSnapshot + StateDelta + ContinuityLedger + approval designation/reference.
- [ ] Tests: generated artifact != State, only approved/locked snapshot propagates, no duplicate state payload, selective invalidation.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-042 FROZEN STATE/CONTINUITY/APPROVED-END-STATE AUTHORITY + AUDIT MEDIA-CHAIN/ENTITY/INVALIDATION SURFACES BEFORE CODE"


---

## IMP-042 AUTHORITY + SURFACE AUDIT PASS - 2026-10-03

- [x] Verify dependencies IMP-041 + IMP-004 + IMP-005 MAIN VERIFIED.
- [x] Claim branch `chatgpt/IMP-042-state-continuity` from clean main `55ba8d747db11c52417d6d9dfe1b67a807de604e`.
- [x] Read frozen StateSnapshot / ContinuityLedger / ApprovedEndState authority.
- [x] Audit Story-owned character state boundaries and legacy media-chain continuity surfaces.
- [x] Lock StateSnapshot as sole semantic continuity truth; ledger/designation refs-only.
- [x] Lock legacy parent/media chain as execution conditioning only, not State authority.
- [ ] Implement StateSnapshot + state delta + ContinuityLedger + ApprovedEndState designation.
- [ ] Tests: generated artifact != State, only approved/locked snapshot propagates, no duplicate state payload, selective invalidation.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-042 STATE SNAPSHOT + STATE DELTA + CONTINUITY LEDGER + APPROVED-END-STATE DESIGNATION -> TARGETED TESTS"


---

## IMP-042 LOCAL VERIFIED - 2026-10-03

- [x] Frozen StateSnapshot / ContinuityLedger / ApprovedEndState authority read.
- [x] Legacy media-chain / Story-owned character-state / shared invalidation surfaces audited.
- [x] Implement StateSnapshot semantic facts + exact source provenance.
- [x] Implement payload-free StateDelta.
- [x] Implement ApprovedEndState refs-only designation and QA/policy/outcome hard gate.
- [x] Implement ContinuityLedger refs-only constraints/findings + exact fact-key validation.
- [x] Keep legacy parent/media chaining as execution conditioning only; UUID media compatibility guarded.
- [x] State successor selective invalidation; replacement self-invalidation excluded.
- [x] ContinuityLedger successor promotion requires durable invalidation.
- [x] ApprovedEndState revocation creates immutable history + durable descendant invalidation.
- [x] Targeted final 16/16 PASS.
- [x] Affected regression final 65/65 PASS.
- [x] Largest valid Windows regression 609 PASS / 3 deselected.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] compileall + git diff --check + authority leakage/TODO scans PASS.
- [x] IMP-042 = LOCAL VERIFIED.
- [ ] Side-effect guard.
- [ ] Commit/push/PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-042 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-042 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature commit `b0ce693b28ac9e9b00135b3a938ee73852b3f3bf` pushed.
- [x] PR #44 CI Python 3.10 + 3.13 SUCCESS on exact feature head.
- [x] Final exact-head review PASS.
- [x] PR #44 merged.
- [x] Main merge SHA `22c9975f8296bb40d5e82cc3c698a2e7fc38b062`.
- [x] Post-merge targeted = 16/16 PASS.
- [x] Post-merge affected = 65/65 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37108250205` SUCCESS on exact merge SHA.
- [x] IMP-042 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-042 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-042 GOVERNANCE VERIFIED / IMP-030 CLAIMED - 2026-10-03

- [x] IMP-042 feature PR #44 MAIN VERIFIED at `22c9975f8296bb40d5e82cc3c698a2e7fc38b062`.
- [x] IMP-042 governance PR #45 merged at `6ecc99275fe953f65fb1c7f64158e5f438d655a8`.
- [x] Governance push-main workflow `37108600449` SUCCESS exact governance SHA.
- [x] Verify IMP-030 dependencies: IMP-025 + IMP-027 + IMP-028 + IMP-042 + IMP-013 MAIN VERIFIED.
- [x] Verify no remote/pr duplicate for `chatgpt/IMP-030-directing-spatial-cinematography`.
- [x] Claim branch from clean main `6ecc99275fe953f65fb1c7f64158e5f438d655a8`.
- [ ] Read frozen AudienceExperienceTarget / DirectingIntent / SceneSpatialDramaticContract / BlockingPlan / CinematographyObjective authority.
- [ ] Audit current narrative/state/camera surfaces and exact-version dependencies.
- [ ] Implement provider-neutral directing chain with hard-gate bypass prevention.
- [ ] Tests: required dramatic/directing parents, stale exact-version rejection, camera self-author negative paths, deterministic provenance/dependency edges.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-030 FROZEN AUDIENCE/DIRECTING/SPATIAL/BLOCKING/CINEMATOGRAPHY AUTHORITY + AUDIT CURRENT NARRATIVE/STATE/CAMERA SURFACES BEFORE CODE"


---

## IMP-030 AUTHORITY + SURFACE AUDIT PASS - 2026-10-03

- [x] Read frozen Master §§28/30/42-44 and ADR-0019.
- [x] Audit exact current Scene/SceneDramaticBeat, ScriptLock, NarrativeTrace, StateSnapshot/ApprovedEndState and ActiveProductionProfile contracts.
- [x] Audit legacy camera/prompt surfaces; keep them downstream compatibility/runtime only.
- [x] Lock beat-scoped AudienceExperienceTarget / DirectingIntent / BlockingPlan / CinematographyObjective identities and scene-scoped SceneSpatialDramaticContract.
- [x] Lock NarrativeTrace as inherited narrative-context evidence without copied Story/Scene truth.
- [x] Lock approved StateSnapshot + designation as semantic continuity input for spatial/blocking.
- [x] Lock `PROFILE_PATH:*` dependency edge for profile-selective invalidation.
- [x] Lock CinematographyObjective as visual strategy + exact decision-basis refs, never self-originating camera authority.
- [ ] Implement typed contracts + shared VersionRepository/DependencyGraph/Invalidation repository flow.
- [ ] Tests: hard-gate bypass, stale source rejection, profile lineage, approved-state propagation, spatial/blocking ownership, camera decision basis, selective invalidation.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-030 PROVIDER-NEUTRAL AUTHORITY CONTRACTS + REPOSITORY -> TARGETED TESTS"


---

## IMP-030 LOCAL VERIFIED - 2026-10-03

- [x] Authority/surface audit PASS.
- [x] Implement AudienceExperienceTarget / DirectingIntent / SceneSpatialDramaticContract / BlockingPlan / CinematographyObjective.
- [x] Keep provider/runtime camera surfaces downstream-only.
- [x] Enforce CURRENT NarrativeTrace + LOCKED ScriptLock + LOCKED ActiveProductionProfile.
- [x] Enforce approved/propagatable StateSnapshot + exact designation for spatial/blocking.
- [x] Enforce Scene participant authority for directing/performance/spatial participants.
- [x] Enforce Scene-or-approved-State authority for entity-backed spatial anchors.
- [x] Enforce canonical LOCATION kind for location_entity_ref.
- [x] Enforce Blocking entities declared by exact SpatialContract.
- [x] Enforce exact visual decision basis; no self-originating camera authority.
- [x] Exact dependency edges + `PROFILE_PATH:*` + durable selective invalidation.
- [x] Targeted final = 18/18 PASS.
- [x] Affected regression final = 117/117 PASS.
- [x] Broader valid Windows regression = 627 PASS / 3 deselected.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] compileall + diff check + authority leakage/TODO scans PASS.
- [x] IMP-030 = LOCAL VERIFIED.
- [ ] Side-effect guard.
- [ ] Commit/push/PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-030 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-030 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature commit `e6ff93f23550d4f650ac3461410f974e56fdfcc6` pushed.
- [x] PR #46 CI Python 3.10 + 3.13 SUCCESS on exact feature head.
- [x] Final exact-head review PASS.
- [x] PR #46 merged.
- [x] Main merge SHA `3dc15e029d6cfb2e3736ee443a72cbbda504c726`.
- [x] Post-merge targeted = 18/18 PASS.
- [x] Post-merge affected = 117/117 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37111589949` SUCCESS on exact merge SHA.
- [x] IMP-030 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-030 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-031 CLAIMED - 2026-10-03

- [x] IMP-030 + IMP-028 + IMP-024 MAIN VERIFIED.
- [x] Verify no remote/pr duplicate for `chatgpt/IMP-031-shot-expansion`.
- [x] Claim branch from clean main `2da4d431fd52269cd79039a2f9bb6cf0bd940c91`.
- [ ] Read frozen ShotExpansion / ShotListManifest / ShotListItem authority + ADR-0020.
- [ ] Audit CoverageStrategy / budget / Directing chain / NarrativeTrace exact-version surfaces.
- [ ] Implement planning transformation + one ShotListItem shot_id origin + refs-only manifest.
- [ ] Tests: no orphan shot, no duplicate manifest truth, no parallel shot ID, coverage/redundancy/budget.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-031 FROZEN SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM AUTHORITY + ADR-0020 + AUDIT COVERAGE/BUDGET/DIRECTING/NARRATIVE TRACE SURFACES BEFORE CODE"


---

## IMP-031 AUTHORITY + SURFACE AUDIT PASS - 2026-10-03

- [x] Read Frozen Master §§45-48 + ADR-0020.
- [x] Audit current code: no canonical CoverageStrategy / ShotBudget / ShotListItem / ShotListManifest exists.
- [x] Reuse IMP-024 DurationBudget/StructureProfile exact-version planning constraints.
- [x] Reuse IMP-028 NarrativeTrace SHOT_LIST_ITEM parent contract.
- [x] Reuse IMP-030 Directing/Blocking/Cinematography authority; no camera self-author path.
- [x] Lock ShotExpansion as stateless transformation; candidates contain no shot_id.
- [x] Lock ShotListItem as sole shot_id origin; Manifest remains refs-only projection.
- [x] Allocate CoverageStrategy + ShotBudget to same Shot Planning boundary because no separate task owns them and IMP-031 coverage/budget acceptance requires them.
- [x] Lock exact-current + unresolved-invalidation fail-closed consumption.
- [ ] Implement shot_planning contracts/repository/expansion service.
- [ ] Tests: no orphan shot, no duplicate/shadow manifest truth, no parallel shot_id, coverage/redundancy/budget, stale/invalidation, exact NarrativeTrace.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-031 SHOT PLANNING CONTRACTS/REPOSITORY + STATELESS EXPANSION SERVICE -> TARGETED TESTS"


---

## IMP-031 LOCAL VERIFIED - 2026-10-03

- [x] Frozen ShotExpansion / ShotListManifest / ShotListItem authority + ADR-0020 read.
- [x] CoverageStrategy / ShotBudget ownership reconciled inside Shot Planning boundary.
- [x] Implement stateless ShotExpansion candidates with no shot identity.
- [x] Implement CoverageStrategy + exact current SceneDramaticBeat coverage.
- [x] Implement ShotBudget count/duration planning constraints.
- [x] Implement ShotListItem sole shot_id creation boundary.
- [x] Implement mandatory Shot NarrativeTrace creation/revision.
- [x] Implement refs-only ShotListManifest projection.
- [x] Block premature ELIGIBLE state before IMP-032.
- [x] Block stale/unresolved invalidated exact inputs.
- [x] Targeted final 15/15 PASS.
- [x] Affected regression final 128/128 PASS.
- [x] Broader Windows regression 642 PASS / 3 deselected.
- [x] Frozen Master guard + compileall + git diff --check PASS.
- [x] Evidence = `evidence/tests/IMP-031_SHOT_PLANNING_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Commit/push/PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-031 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-031 PR #48 REVIEW-FIX LOCAL VERIFIED - 2026-10-03

- [x] Initial feature commit `243f97e6a207a83b3fb5a041c5744b8b37ac3d16` pushed and PR #48 opened.
- [x] Initial PR CI Python 3.10 / 3.13 PASS on initial head.
- [x] Exact-head review found crash-recovery gap between ShotListItem persistence and NarrativeTrace completion.
- [x] Add idempotent exact-replay repair for missing shot trace; conflicting replay fails closed.
- [x] Require exact CURRENT Shot NarrativeTrace before ShotListItem consumption.
- [x] Add idempotent exact ShotListManifest replay; conflicting replay fails closed.
- [x] Add fault-injection tests for initial-create and revision interruption recovery.
- [x] Review-fix targeted = 17/17 PASS.
- [x] Review-fix affected regression = 130/130 PASS.
- [x] Review-fix broader valid Windows regression = 644 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / diff check / import/TODO scans PASS.
- [ ] Commit review-fix.
- [ ] Push new exact head to PR #48.
- [ ] Wait for fresh Ubuntu CI Python 3.10 / 3.13 on new head.
- [ ] Exact-head merge guard / merge main.
- [ ] Post-merge targeted + affected + frozen guard + push-main workflow.
- [ ] Governance state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "STAGE EXACT REVIEW-FIX SCOPE -> COMMIT REVIEW-FIX -> PUSH NEW HEAD TO PR #48 -> WAIT FRESH CI -> EXACT-HEAD REVIEW/MERGE GUARD -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-031 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature PR #48 merged from exact head `62754bc9655b6732f3fad669c281381ab47ae1ed`.
- [x] Merge SHA `c6913a2f82c85d05c128824b640f5a17bb635bbf`.
- [x] PR CI run `37118314077` SUCCESS Python 3.10 / 3.13.
- [x] Post-merge targeted = 17/17 PASS.
- [x] Post-merge affected = 130/130 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37118410749` SUCCESS exact merge SHA.
- [x] IMP-031 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-031 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-031 GOVERNANCE VERIFIED / IMP-032 CLAIMED - 2026-10-03

- [x] IMP-031 governance PR #49 merged at `f7ec86c9392be24185d23893cd8b513e281f1c52`.
- [x] Governance push-main workflow `37118828928` SUCCESS exact governance SHA.
- [x] Verify IMP-032 dependencies: IMP-031 + IMP-042 + IMP-041 + IMP-013 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-032.
- [x] Claim `chatgpt/IMP-032-shot-eligibility-fullshotspec` from clean governance main.
- [ ] Read frozen ShotEligibilityGate / FullShotSpec L1-L8 / StaticKeyframeSpec / MotionDeltaSpec / ShotDecisionTrace authority.
- [ ] Audit current ShotListItem/NarrativeTrace, StateSnapshot, ReferenceAsset resolver and ActiveProductionProfile surfaces.
- [ ] Implement provider-neutral eligibility/realization boundary without creating a new shot_id.
- [ ] Tests: stale gate rejection, required upstream gates, same shot_id across revisions, L1-L8 only, static/motion delta separation, decision trace exact provenance.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-032 FROZEN SHOT ELIGIBILITY / FULLSHOTSPEC L1-L8 / STATICKEYFRAMESPEC / MOTIONDELTASPEC / SHOTDECISIONTRACE AUTHORITY + AUDIT CURRENT SHOT/STATE/REFERENCE/PROFILE SURFACES BEFORE CODE"


---

## IMP-032 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-03

- [x] Read Frozen Master §§49-54 + L1-L8 policy + ADR-0020.
- [x] Confirm no existing canonical FullShotSpec/StaticKeyframeSpec/MotionDeltaSpec owner in `agent/studio`.
- [x] Reuse IMP-031 ShotListItem + exact current shot NarrativeTrace; no new shot_id origin.
- [x] Reuse IMP-042 StateSnapshot approval/propagation authority.
- [x] Reuse IMP-041 ReferenceAsset/ReferenceResolver exact-current bindings.
- [x] Reuse IMP-013 ActiveProductionProfile exact current LOCKED binding.
- [x] Lock exactly eight semantic layers L1-L8 with field-level FIXED/INHERITED/VARIABLE + source refs; no invented canonical L9-L12.
- [x] Lock StaticKeyframeSpec as static start state only and MotionDeltaSpec as temporal delta only.
- [x] Lock ShotDecisionTrace as explainability evidence, not Shot truth.
- [ ] Implement typed contracts/repository/gates.
- [ ] Tests: stale/rejected gate, same shot_id across spec revisions, L1-L8 only, static/motion separation, exact State/Reference/Profile bindings, decision trace provenance, selective invalidation.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-032 PROVIDER-NEUTRAL REALIZATION CONTRACTS/REPOSITORY + HARD GATES -> TARGETED TESTS"


---

## IMP-032 LOCAL VERIFIED - 2026-10-03

- [x] Read frozen ShotEligibilityGate / FullShotSpec L1-L8 / StaticKeyframeSpec / MotionDeltaSpec / ShotDecisionTrace authority.
- [x] Audit current ShotListItem/NarrativeTrace, StateSnapshot, ReferenceAsset resolver and ActiveProductionProfile surfaces.
- [x] Implement typed provider-neutral ShotEligibilityGate / FullShotSpec / StaticKeyframeSpec / MotionDeltaSpec / ShotDecisionTrace contracts and repository.
- [x] Preserve same canonical shot_id; no parallel/reallocated Shot identity.
- [x] Bind exact current Shot NarrativeTrace / profile / state / directing / spatial / blocking / cinematography authority.
- [x] Bind exact required-reference set + selected ReferenceAssets/content hashes + full ReferenceResolutionTrace hash.
- [x] Bind exact eligibility-rule version and durable dependency invalidation.
- [x] Enforce current ELIGIBLE gate before FullShotSpec.
- [x] Enforce exactly semantic L1-L8 with field-level FIXED/INHERITED/VARIABLE authority.
- [x] Enforce StaticKeyframeSpec static-only and MotionDeltaSpec temporal-delta-only separation.
- [x] Enforce ShotDecisionTrace exact provenance and reject generic `cinematic` rationale.
- [x] Fault-injection recovery: failed ReferenceResolver consumer bind leaves gate DRAFT; exact replay recovers.
- [x] Targeted final = 15/15 PASS.
- [x] Affected direct-authority regression final = 154/154 PASS.
- [x] Broader valid Windows regression final = 659 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / git diff --check / import leakage / TODO scans PASS.
- [x] Evidence = `evidence/tests/IMP-032_SHOT_REALIZATION_EVIDENCE.md`.
- [x] Side-effect guard — PASS: remote branch absent, PR absent, staged index empty, transient `.tmp` removed.
- [ ] Commit exact IMP-032 scope.
- [ ] Push branch / create PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge main verification / push-main workflow.
- [ ] Governance state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "STAGE EXACT IMP-032 VERIFIED SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


### IMP-032 FEATURE COMMIT / PR CHECKPOINT - 2026-10-03

- [x] Side-effect guard PASS.
- [x] Commit exact IMP-032 scope = `6e96978bc9596bc4838492532dacabc7c56f1a53`.
- [x] Push feature branch = SUCCESS.
- [x] Create PR #50 = SUCCESS.
- [ ] Commit/push this docs-only PR checkpoint state.
- [ ] Fresh Ubuntu CI Python 3.10/3.13 + frozen guard on final PR head.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge main verification / push-main workflow.
- [ ] Governance state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH IMP-032 PR CHECKPOINT STATE -> WAIT FRESH CI ON FINAL HEAD -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-032 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

- [x] Feature PR #50 exact final head `78464d03f5dc2a537ddbcce470a59cce71404a1f`.
- [x] PR CI run `37138187600` SUCCESS Python 3.10 / 3.13 + frozen guard.
- [x] Exact-head review / merge guard PASS.
- [x] Merge main = `bd9ac71117912e5f1f4771eaf2cf128dcb5739a8`.
- [x] Post-merge targeted = 15/15 PASS.
- [x] Post-merge affected = 154/154 PASS.
- [x] Post-merge frozen Master guard PASS.
- [x] Main push workflow `37138380626` SUCCESS Python 3.10 / 3.13 exact merge SHA.
- [x] IMP-032 feature implementation = MAIN VERIFIED.
- [ ] Commit governance-only state sync.
- [ ] Push governance branch / create governance PR.
- [ ] Governance PR CI / merge.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-032 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-032 GOVERNANCE VERIFIED / IMP-033 CLAIMED - 2026-10-03

- [x] IMP-032 governance PR #51 merged at `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`.
- [x] Governance push-main workflow `37138826694` SUCCESS Python 3.10 / 3.13 exact governance SHA.
- [x] IMP-032 = MAIN VERIFIED.
- [x] Verify IMP-033 dependency: IMP-032 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-033.
- [x] Claim `chatgpt/IMP-033-shotir-production-compiler` from clean governance main.
- [ ] Read frozen ShotIR / Production Compiler authority and applicable ADRs.
- [ ] Audit current ShotRealization, request compilation, provider-boundary and existing prompt/request surfaces.
- [ ] Implement deterministic provider-neutral ShotIR + compiler provenance without provider-specific authority leakage.
- [ ] Tests: deterministic golden compile, exact input-version bindings, stable hashes/metadata, no provider-specific authority in IR, stale source rejection.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ IMP-033 FROZEN SHOTIR / PRODUCTION COMPILER AUTHORITY + AUDIT CURRENT SHOT REALIZATION / REQUEST / COMPILER / PROVIDER-BOUNDARY SURFACES BEFORE CODE"


---

## IMP-033 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

- [x] Read Frozen Master §55 Shot IR and §64 Production Compiler authority.
- [x] Reconcile ADR-0020 Shot identity/spec/IR boundary.
- [x] Audit current ShotRealization exact-current sources and invalidation path.
- [x] Audit legacy Flow/Omni prompt/request/provider surfaces; classify as compatibility/provider lowering, not canonical authority.
- [x] Confirm no existing canonical ShotIR/CompiledRequest owner under `agent/studio`.
- [x] Keep ProviderProfile/capability/router for IMP-050 and provider adapter anti-corruption for IMP-051.
- [ ] Implement provider-neutral ShotIR + compiler rule/version provenance + diagnostics + deterministic request metadata/hashes.
- [ ] Tests: deterministic golden compile, exact version bindings, stale source rejection, stable hash/metadata, no provider-specific authority leakage.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-033 PROVIDER-NEUTRAL SHOTIR + DETERMINISTIC PRODUCTION COMPILER + PROVENANCE/HASHES -> TARGETED TESTS"


---

## IMP-033 LOCAL VERIFIED - 2026-10-04

- [x] Read Frozen ShotIR / Production Compiler authority + ADR-0020.
- [x] Audit current ShotRealization, compiler/request and provider-boundary surfaces.
- [x] Implement deterministic provider-neutral ShotIR + Production Compiler.
- [x] Preserve same canonical shot_id; no rekey/new Shot identity.
- [x] Bind exact FullShotSpec / eligibility / static / motion / State / profile / ReferenceAsset / compiler-rule versions.
- [x] Enforce stale/unresolved-invalidation fail-closed behavior.
- [x] Enforce provider-specific execution constraint keys/request authority rejection.
- [x] Targeted = 14/14 PASS.
- [x] Affected regression = 169/169 PASS.
- [x] Broader valid Windows regression = 673 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / git diff --check / leakage / TODO scans PASS.
- [x] Evidence = `evidence/tests/IMP-033_SHOTIR_PRODUCTION_COMPILER_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Commit exact IMP-033 scope.
- [ ] Push feature branch / create PR.
- [ ] Ubuntu CI Python 3.10/3.13 + frozen guard.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge verification / push-main workflow.
- [ ] Governance state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-033 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


### IMP-033 FEATURE COMMIT / PR CHECKPOINT - 2026-10-04

- [x] Side-effect guard PASS.
- [x] Commit exact IMP-033 scope = `ee0bd4bc04cf8879746a278538540f996d6cd4d5`.
- [x] Push feature branch = SUCCESS.
- [x] Create PR #52 = SUCCESS.
- [ ] Commit/push this docs-only PR checkpoint state.
- [ ] Fresh Ubuntu CI Python 3.10/3.13 + frozen guard on final PR head.
- [ ] Exact-head review.
- [ ] Merge main.
- [ ] Post-merge verification / push-main workflow.
- [ ] Governance state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH IMP-033 PR CHECKPOINT STATE -> WAIT FRESH CI ON FINAL PR HEAD -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-033 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

- [x] Feature PR #52 exact final head `b1df7a296ac972a5ab92adb5a88cbf7c50623938`.
- [x] PR CI run `37175107218` SUCCESS Python 3.10 / 3.13 + frozen guard.
- [x] Exact-head review / merge guard PASS.
- [x] Merge main = `a914234410edbc2c6bc651a6177806af10a45c48`.
- [x] Post-merge targeted = 14/14 PASS.
- [x] Post-merge affected = 169/169 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37175266699` SUCCESS exact merge SHA.
- [x] IMP-033 feature implementation = MAIN VERIFIED.
- [ ] Commit governance-only state sync.
- [ ] Push governance branch / create governance PR.
- [ ] Governance PR CI / merge.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-033 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-033 GOVERNANCE VERIFIED / IMP-050 CLAIMED - 2026-10-04

- [x] IMP-033 governance PR #53 merged at `9c6c8a68df6eba566e86aea680d6a892a815eb26`.
- [x] Governance push-main workflow `37175814754` SUCCESS exact governance SHA.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Verify IMP-050 dependencies: IMP-033 + IMP-013 + IMP-006 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-050.
- [x] Claim `chatgpt/IMP-050-capability-provider-router` from clean governance main.
- [ ] Read frozen CapabilityRegistry / ProviderProfile / Router authority and applicable ADRs.
- [ ] Audit current Flow/Omni capability/routing/provider surfaces and observability/evidence integration.
- [ ] Implement evidence-versioned provider capabilities + deterministic routing without brand assumptions.
- [ ] Tests: capability constraints, stale profile, unsupported requirement, deterministic selection/evidence.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify.

NEXT_EXACT_ACTION = "READ FROZEN CAPABILITYREGISTRY / PROVIDERPROFILE / ROUTER AUTHORITY + AUDIT CURRENT FLOW/OMNI/CAPABILITY/ROUTING SURFACES BEFORE CODE"


---

## IMP-050 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

- [x] Read Frozen Master Provider Capability Model / Provider Router authority.
- [x] Audit legacy CLI provider config, Flow transport/batch and Omni Flash capability/model/cost surfaces.
- [x] Reuse EvidenceReference, ShotIR, ActiveProductionProfile and shared version/dependency/invalidation owners.
- [x] Lock UNKNOWN-not-guessed, evidence freshness, deterministic ranking, explicit degradation and no-hidden-fallback invariants.
- [x] Keep Flow/Omni adapter lowering out of IMP-050; IMP-051 owns provider anti-corruption.
- [x] Implement initial canonical `provider_routing.py` and harden current-pointer/invalidation + ShotIR constraint-preservation gates.
- [x] py_compile PASS.
- [ ] Export API.
- [ ] Targeted tests: evidence/profile identity/freshness, UNKNOWN/unsupported, deterministic selection, stale profile, constraint weakening, degradation, budget/recovery, invalidation/replay.
- [ ] Affected + broader regression + frozen/static gates.
- [ ] Evidence / state sync / commit / push / PR / CI / exact-head review / merge / main verify / governance.

NEXT_EXACT_ACTION = "EXPORT IMP-050 API -> WRITE REAL SQLITE/SHOTIR TARGETED TESTS -> RUN TARGETED"


---

## IMP-050 LOCAL VERIFIED - 2026-10-04

- [x] Read Frozen Master Provider Capability Model / Provider Router authority.
- [x] Audit current Flow/Omni/capability/routing surfaces.
- [x] Implement evidence-versioned `ProviderProfile` + deterministic provider-neutral Router.
- [x] Enforce UNKNOWN-not-guessed / no hidden fallback / explicit degradation policy.
- [x] Enforce ShotIR constraint preservation + current-pointer/unresolved-invalidation checks.
- [x] Require explicit execution `as_of` timestamp for selected-route freshness validation.
- [x] Targeted = 13/13 PASS.
- [x] Affected regression = 75/75 PASS.
- [x] Broader valid Windows regression = 686 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / diff check / import/TODO scans PASS.
- [x] Evidence = `evidence/tests/IMP-050_PROVIDER_ROUTING_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Stage exact IMP-050 scope.
- [ ] Commit / push / PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.
- [ ] Governance state sync / governance main verify.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-050 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"

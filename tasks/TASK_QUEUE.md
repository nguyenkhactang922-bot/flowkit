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

---

## IMP-050 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

- [x] Feature commit `c0201c0a3795f3ae63c5743a7c73e1c631bd23f0` pushed.
- [x] Feature PR #54 merged.
- [x] Merge SHA `611318236bd57d4abbf193a59fd6276273345d79`.
- [x] PR CI run `37185640898` SUCCESS Python 3.10 / 3.13.
- [x] Post-merge targeted = 13/13 PASS.
- [x] Post-merge affected = 75/75 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37185793951` SUCCESS exact merge SHA.
- [x] IMP-050 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-050 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"

---

## IMP-050 GOVERNANCE VERIFIED / IMP-051 CLAIMED - 2026-10-04

IMP-050_GOVERNANCE_PR = #55
IMP-050_GOVERNANCE_MERGE_SHA = 0f8f1387f5aa9b3aacd5efe3ef240f1666306a98
IMP-050_GOVERNANCE_PUSH_WORKFLOW = 37186570087 SUCCESS Python 3.10 / 3.13 exact governance SHA

ACTIVE_TASK = IMP-051 FLOW / OMNI PROVIDERADAPTER ANTI-CORRUPTION
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-051-provider-adapter-anti-corruption
BASE_HEAD = 0f8f1387f5aa9b3aacd5efe3ef240f1666306a98
DEPENDS = IMP-050 MAIN VERIFIED + IMP-033 MAIN VERIFIED + IMP-013 MAIN VERIFIED + IMP-041 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "READ IMP-051 PROVIDER ADAPTER / ANTI-CORRUPTION AUTHORITY + AUDIT FLOW/OMNI TRANSPORT/REQUEST SURFACES BEFORE CODE"

---

## IMP-051 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

ACTIVE_TASK = IMP-051 FLOW / OMNI PROVIDERADAPTER ANTI-CORRUPTION
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-051-provider-adapter-anti-corruption
BASE_HEAD = 0f8f1387f5aa9b3aacd5efe3ef240f1666306a98

LOCKED IMPLEMENTATION DECISIONS:
- Frozen Master §67 is authoritative: adapter owns provider transport dialect only; it cannot edit canonical Story/Shot/State/ShotIR/Router truth.
- IMP-051 consumes exact-current ShotIR + SELECTED ProviderRoutingDecision/ProviderProfile and emits derivative provider requests plus normalized submit/poll/cancel/reconcile observations.
- IMP-052, not IMP-051, owns GenerationJob four-axis persistence/state transitions/CAS and durable submission-attempt identity.
- Remote calls are outside canonical DB transactions; canonical preflight is complete before transport side effects.
- FlowClient / Flow batch / Omni Flash are compatibility donors behind concrete adapters; agent.studio neutral contracts MUST NOT import agent.services or Flow payload schemas.
- Hidden/degraded legacy fallback is forbidden. Unsupported provider mode returns explicit UNSUPPORTED before transport call.
- Cancel is not synthesized: current Flow/Omni transport has no proven cancel API, so cancel reports UNSUPPORTED unless a real transport implementation proves otherwise.
- Reconcile never resubmits. Existing handle/workflow may be looked up/polled; insufficient proof returns AMBIGUOUS, never fake failure/success.
- Timeout/connection/crash after possible submit is AMBIGUOUS; NO RETRY WITHOUT PROOF.
- Normalized transport observations are evidence/adapter outputs only, not canonical job-state authority.
- Scoped authorization/session metadata is runtime-only; long-lived secrets/raw provider payloads are not persisted into canonical contracts.
- Existing Flow/Omni transport tests remain regression gates.

NEXT_EXACT_ACTION = "IMPLEMENT NEUTRAL PROVIDER ADAPTER CONTRACT/PORT + FLOW/OMNI COMPATIBILITY ADAPTERS -> TARGETED CONTRACT/TRANSPORT TESTS"


---

## IMP-051 LOCAL VERIFIED - 2026-10-04

- [x] Read Frozen Master provider adapter / anti-corruption authority.
- [x] Audit Flow/Omni transport/request compatibility surfaces.
- [x] Implement provider-neutral adapter contract/preflight + Flow/Omni compatibility adapters.
- [x] Enforce exact-current ShotIR/route/profile and exact runtime ReferenceAsset bindings.
- [x] Enforce explicit unsupported modes/model tuples; no hidden fallback/degradation.
- [x] Enforce ambiguous possible-submit semantics / no retry without proof.
- [x] Enforce reconcile-never-resubmit and no fake cancel.
- [x] Targeted = 18/18 PASS.
- [x] Affected regression = 186/186 PASS.
- [x] Broader valid Windows = 659 PASS / 3 deselected.
- [x] Complete valid unit-file coverage = 704 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / diff check / leakage scans PASS.
- [x] Evidence = `evidence/tests/IMP-051_PROVIDER_ADAPTER_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Stage exact IMP-051 scope.
- [ ] Commit / push / PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.
- [ ] Governance state sync / governance main verify.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-051 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-051 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

- [x] Feature PR #56 merged from exact head `ed7aff78e0cb35a7d5a44080777683d204d9d38c`.
- [x] Merge SHA `6f60c32d73ee447f638fd17775382d420807bdb1`.
- [x] PR CI run `37216700657` SUCCESS Python 3.10 / 3.13.
- [x] Post-merge targeted = 18/18 PASS.
- [x] Post-merge affected = 186/186 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37216924329` SUCCESS exact merge SHA.
- [x] IMP-051 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-051 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-051 GOVERNANCE VERIFIED / IMP-052 CLAIMED - 2026-10-04

- [x] IMP-051 governance PR #57 merged at `abbe70693f9282adf7ba2041deb20a09c6687a9c`.
- [x] Governance push-main workflow `37217851883` SUCCESS exact governance SHA.
- [x] Verify IMP-052 dependencies: IMP-003 + IMP-004 + IMP-033 + IMP-051 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-052.
- [x] Claim `chatgpt/IMP-052-generation-job-four-axis` from clean governance main.
- [ ] Read frozen GenerationJob four-axis / exact 62-row transition authority.
- [ ] Audit current job/queue/provider transport surfaces.
- [ ] Implement persisted four axes + closed transition validator + CAS + transition history + generic-status projection.
- [ ] Tests: all states reachable, all 62 legal rows, every unspecified transition rejected, V0.13 fixtures.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-052 FROZEN GENERATIONJOB FOUR-AXIS / EXACT 62-ROW TRANSITION AUTHORITY + AUDIT CURRENT JOB/QUEUE/TRANSPORT SURFACES BEFORE CODE"


---

## IMP-052 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

- [x] Read Frozen Master §68/FM2-002 GenerationJob authority.
- [x] Machine-count exact closed relation: scheduler 15 + provider 19 + artifact 14 + creative 14 = 62 rows.
- [x] Read V0.13 model-check valid/invalid fixtures and all-state reachability evidence.
- [x] Audit current code: no canonical GenerationJob owner; ProviderAdapter observations are evidence-only; legacy request.status is compatibility-only.
- [x] Audit persistence: shared SQLiteWriteOwner/CAS; schema v5 requires GenerationJob migration v6.
- [x] Lock exact ShotIR / ProviderRoutingDecision / ProviderProfile / input fingerprint / submission-attempt identity pins.
- [x] Lock one-axis transition ownership, full-tuple validation, append-only transition history and no-network-in-transaction rule.
- [ ] Implement schema migration v6.
- [ ] Implement typed GenerationJob contracts + exact 62-row validator + repository/CAS/history + derived UI status.
- [ ] Targeted tests: exact 62 rows, reachability, unspecified rejection, V0.13 tuples, CAS, immutable identity, owner guard, recovery/no-blind-resubmit.
- [ ] Affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "IMPLEMENT PERSISTENCE MIGRATION V6 + GENERATIONJOB TYPED CONTRACT/62-ROW VALIDATOR/REPOSITORY/CAS/HISTORY/DERIVED STATUS -> TARGETED TESTS"


---

## IMP-052 LOCAL VERIFIED - 2026-10-05

- [x] Read frozen GenerationJob four-axis / exact 62-row transition authority.
- [x] Audit current job/queue/provider transport surfaces.
- [x] Implement persistence migration v6.
- [x] Implement typed GenerationJob contract + exact 62-row validator + repository/CAS/history + derived UI status.
- [x] Tests: exact 62 rows, reachability, unspecified rejection, V0.13 tuples, CAS, immutable identity, owner guard, recovery/no-blind-resubmit.
- [x] Targeted = 20/20 PASS.
- [x] Affected regression = 77/77 PASS.
- [x] Broader valid Windows = 647 PASS / 3 deselected.
- [x] Complete valid unit-file coverage = 724 PASS / 3 deselected.
- [x] Frozen Master guard / compileall / diff check / leakage scans PASS.
- [x] Evidence = `evidence/tests/IMP-052_GENERATION_JOB_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Stage exact IMP-052 scope.
- [ ] Commit / push / PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification / MAIN VERIFIED.
- [ ] Governance state sync / governance main verify.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-052 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"

---

## IMP-052 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-05

- [x] Feature PR #58 merged from exact head `5e56cb9dffc0ab7239549f6e3ced67bfc77ec57e`.
- [x] Merge SHA `657424f6db4e53ec5fa2d4122efa06aaf47e156f`.
- [x] PR CI run `37223076071` SUCCESS Python 3.10 / 3.13.
- [x] Post-merge local targeted = 20/20 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37223369097` SUCCESS exact merge SHA with full unit tests + frozen guard.
- [x] IMP-052 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-052 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-052 GOVERNANCE VERIFIED / IMP-053 CLAIMED - 2026-10-05

- [x] IMP-052 governance PR #59 merged at `b7a942897cef404cabcda67b7b58737fb7d10b3a`.
- [x] Governance push-main workflow `37260218808` SUCCESS exact governance SHA.
- [x] Verify IMP-053 dependencies: IMP-052 + IMP-005 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-053.
- [x] Claim `chatgpt/IMP-053-scheduler-dag-leases-admission` from clean governance main.
- [ ] Read Frozen Scheduler/Queue/DAG/Lease/Admission authority.
- [ ] Audit current worker priority/concurrency/cooldown/prerequisite logic.
- [ ] Implement durable readiness/checkpoints + lease claim + fairness + admission controls.
- [ ] Tests: lease conflict, starvation, backpressure, dependency gating, restart readiness.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-053 FROZEN SCHEDULER/DAG/LEASE/ADMISSION AUTHORITY + AUDIT CURRENT WORKER PRIORITY/CONCURRENCY/COOLDOWN/PREREQUISITE SURFACES BEFORE CODE"


---

## IMP-053 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-05

- [x] Read Frozen Master section 69/FM2-003 Queue/DAG authority.
- [x] Audit GenerationJob scheduler-axis transition contract from IMP-052.
- [x] Audit legacy worker priority/concurrency/cooldown/prerequisite behavior for KEEP+EXTEND mapping.
- [x] Lock schema v7 shared-writer design: DAG edges, scheduler node metadata, readiness checkpoint/history, lease current/history, admission evidence, fairness cursor.
- [x] Lock ordering = priority -> project fairness -> oldest-ready.
- [x] Lock admission = global/provider/model/operation/local-resource/dependency/budget with evidence-driven cap values.
- [x] Lock no duplicate scheduler-state authority and no blind restart reset.
- [ ] Implement migration v7.
- [ ] Implement typed scheduler contracts/repository/CAS/history/admission/fairness/lease integration.
- [ ] Tests: lease conflict, starvation/fairness, backpressure/admission, dependency gating, restart readiness.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "IMPLEMENT MIGRATION V7 + TYPED SCHEDULER DAG/READINESS/LEASE/ADMISSION/FAIRNESS REPOSITORY + LEGAL GENERATIONJOB TRANSITION INTEGRATION -> TARGETED TESTS"

---

## IMP-053 TARGETED + AFFECTED CHECKPOINT - 2026-10-05

- [x] Migration v7 + typed scheduler/DAG/readiness/lease/admission/fairness implementation materialized.
- [x] Scheduler targeted = 13/13 PASS.
- [x] GenerationJob affected regression = 20/20 PASS.
- [x] Persistence + schema-upgrade migration compatibility = 13/13 PASS.
- [ ] Broader valid Windows regression with established exclusions and affected files excluded.
- [ ] Frozen Master guard + compile/static/diff review.
- [ ] Evidence / LOCAL VERIFIED.
- [ ] Side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN BROADER VALID WINDOWS REGRESSION -> FROZEN/STATIC/DIFF REVIEW -> EVIDENCE"


---

## IMP-053 BROADER REGRESSION RESUME CHECKPOINT - 2026-10-05

- [x] Scheduler targeted 13/13 PASS.
- [x] GenerationJob affected 20/20 PASS.
- [x] Persistence/schema compatibility 13/13 PASS.
- [x] Completed broader modules 466/466 PASS.
- [x] Production compiler 14/14 PASS.
- [ ] Run only missing broader modules: profile_resolver, provider_adapter, provider_routing, reference, research_story_material, screenplay_realization, shot_planning, shot_realization, state_continuity, story_core, story_intake, story_quality, structure_planning, topic_domain, versioning.
- [ ] Frozen Master guard + compile/static/diff review.
- [ ] Evidence / LOCAL VERIFIED.
- [ ] Side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN ONLY MISSING IMP-053 BROADER MODULE BATCHES WITH DURABLE JUNIT/EXIT MARKERS -> FROZEN/STATIC/DIFF REVIEW -> EVIDENCE"


---

## IMP-053 LOCAL VERIFIED - 2026-10-05

- [x] Migration v7 scheduler coordination schema.
- [x] Typed scheduler node / immutable DAG / readiness checkpoint + history.
- [x] Durable admission evidence / lease current+history / fairness cursor.
- [x] Legal GenerationJob scheduler transition integration.
- [x] Hierarchical admission + dependency/budget/backpressure gates.
- [x] Lease conflict / serialized claim / no oversubscription.
- [x] Fairness / no-starvation ordering.
- [x] Restart readiness + expired-lease recovery handoff without blind requeue.
- [x] Scheduler targeted = 13/13 PASS.
- [x] GenerationJob affected = 20/20 PASS.
- [x] Persistence/schema compatibility = 13/13 PASS.
- [x] Broader valid Windows regression = 691/691 PASS.
- [x] Frozen Master guard + compile/static/diff review PASS.
- [x] Evidence = `evidence/tests/IMP-053_SCHEDULER_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Commit / push / PR.
- [ ] CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification / governance sync.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-053 SCOPE EXCLUDING .tmp -> COMMIT -> PUSH -> PR -> CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC -> NEXT TASK"


---

## IMP-053 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-05

- [x] Feature commit `fb50900e0faff6693427afe804b6f38c6f7b7e69`.
- [x] Feature PR #60 CI run `37340246714` SUCCESS Python 3.10 / 3.13.
- [x] Feature PR #60 merged at `ad0ab54d86c9c90817415e1e60defbf357a5c807`.
- [x] Local main fast-forwarded to exact merge SHA.
- [x] Frozen Master guard PASS on local main.
- [x] Main push workflow `37340889716` SUCCESS Python 3.10 / 3.13 exact merge SHA.
- [x] IMP-053 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on main.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-053 GOVERNANCE-ONLY STATE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-053 GOVERNANCE VERIFIED / IMP-054 CLAIMED - 2026-10-05

- [x] IMP-053 governance PR #61 merged at `18d92a82359d559bd2d2f9b9eafbc25e44430253`.
- [x] Governance push-main workflow `37343051638` SUCCESS Python 3.10 / 3.13 exact governance SHA.
- [x] Verify IMP-054 dependencies: IMP-052 + IMP-051 + IMP-006 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-054.
- [x] Claim `chatgpt/IMP-054-retry-resume-remote-ambiguity` from clean governance main.
- [ ] Read frozen retry/resume/remote ambiguity authority.
- [ ] Audit GenerationJob/provider adapter/recovery/observability surfaces.
- [ ] Implement failure taxonomy + RecoveryCoordinator + reconciliation + idempotency/absence evidence + AMBIGUOUS_HOLD.
- [ ] Tests: crash-before-submit, crash-after-possible-submit, timeout, recovered handle, proven absent, still ambiguous, cancellation race.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-054 FROZEN RETRY/RESUME/REMOTE AMBIGUITY AUTHORITY + AUDIT CURRENT GENERATIONJOB/PROVIDER ADAPTER/RECOVERY/OBSERVABILITY SURFACES BEFORE CODE"


---

## IMP-054 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-05

- [x] Read Frozen Master §§70-71 + GenerationJob recovery transition authority.
- [x] Audit GenerationJob four-axis CAS/history owner.
- [x] Audit ProviderAdapterPort/Flow/Omni reconcile behavior.
- [x] Audit ErrorClass/RetryDisposition observability taxonomy.
- [x] Confirm Retry/Resume has no independent state store; RecoveryEvent/attempt identity owns persistence evidence only.
- [x] Confirm no blind retry: only proven absent/no-side-effect or verified same-job idempotency may requeue/resubmit.
- [ ] Add migration v8 durable append-only recovery evidence/proof history.
- [ ] Implement provider-neutral RecoveryCoordinator over existing GenerationJob transitions.
- [ ] Tests: crash-before-submit, crash-after-possible-submit, timeout, recovered handle, proven absent, still ambiguous, cancellation race, restart scan/idempotency.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-054 MIGRATION V8 DURABLE RECOVERY EVIDENCE + PROVIDER-NEUTRAL RECOVERY COORDINATOR -> TARGETED FAULT-INJECTION TESTS"


---

## IMP-054 LOCAL VERIFIED - 2026-10-06

- [x] Add migration v8 durable append-only recovery evidence.
- [x] Implement provider-neutral RecoveryCoordinator over GenerationJob four-axis CAS authority.
- [x] Enforce NO RETRY WITHOUT PROOF.
- [x] Cover pre-dispatch no-side-effect, proven-absent and verified same-job idempotency recovery.
- [x] Cover recovered handle/resume, ambiguous hold, restart scan and cancellation race.
- [x] Recovery targeted = 10/10 PASS.
- [x] Direct/affected latest unique = 73/73 PASS.
- [x] Broader latest unique = 202/202 PASS after exact migration expectation repair.
- [x] Frozen Master guard + py_compile + git diff --check PASS.
- [x] Evidence = `evidence/tests/IMP-054_RECOVERY_RETRY_RESUME_EVIDENCE.md`.
- [ ] Side-effect guard.
- [ ] Stage exact IMP-054 scope / commit.
- [ ] Push / PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification.
- [ ] Governance-only state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-054 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC -> MAIN VERIFIED -> CLAIM NEXT TASK"


---

## IMP-054 PR #62 REVIEW FIX LOCAL VERIFIED - 2026-10-06

- [x] Feature commit `ffe8316295cb06ebe1d4e8855566a5d2a86f30cb` pushed; PR #62 opened.
- [x] Exact-head review found request-id/workflow handle-kind reconstruction gap.
- [x] Repair durable lineage mapping: operation-id -> OPERATION; request-id -> WORKFLOW.
- [x] Focused workflow recovery regression = 1/1 PASS.
- [x] Upstream Omni WORKFLOW reconcile contract = 1/1 PASS.
- [x] py_compile + frozen Master guard + git diff --check PASS.
- [ ] Commit review-fix.
- [ ] Push new exact head to PR #62.
- [ ] Fresh Ubuntu CI Python 3.10 / 3.13 on new head.
- [ ] Final exact-head merge guard / merge main.
- [ ] Post-merge main verification.
- [ ] Governance-only sync / MAIN VERIFIED.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "STAGE EXACT REVIEW-FIX SCOPE -> COMMIT REVIEW-FIX -> PUSH NEW HEAD TO PR #62 -> WAIT FRESH CI PYTHON 3.10/3.13 -> FINAL EXACT-HEAD MERGE GUARD -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC -> MAIN VERIFIED -> CLAIM NEXT TASK"


---

## IMP-054 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-06

- [x] PR #62 merged from exact review-fix head `002a1e3d3ef9836131af5f13600d6bcbc1984aaf`.
- [x] Main merge SHA `eb85285d0196d3bf7ed29f0578f30e8e44a78b26`.
- [x] PR CI run `37428721919` SUCCESS Python 3.10 / 3.13.
- [x] Main push workflow `37429327183` SUCCESS exact merge SHA.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] IMP-054 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge on `main`.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-054 GOVERNANCE-ONLY STATE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-054 GOVERNANCE VERIFIED / IMP-055 CLAIMED - 2026-10-06

- [x] IMP-054 governance PR #63 merged at `ffeecd49eacc4019bbc63f4a5cb45293d9a4e97d`.
- [x] Governance push-main workflow `37431843970` SUCCESS Python 3.10 / 3.13 exact governance SHA.
- [x] Verify IMP-055 dependencies: IMP-052 + IMP-003 + IMP-005 MAIN VERIFIED.
- [x] Verify no remote branch/PR duplicate for IMP-055.
- [x] Claim `chatgpt/IMP-055-artifact-lifecycle-reconciler` from clean governance main.
- [ ] Read frozen artifact lifecycle/store/reconciler authority.
- [ ] Audit current GenerationJob/artifact/media/persistence surfaces.
- [ ] Implement STAGING/READY/STALE_RESULT/QUARANTINED/MISSING/CORRUPT/ARCHIVED lifecycle, immutable hashes and startup reconciliation without creative-approval leakage.
- [ ] Tests: crash at each stage, missing file, orphan final file, corruption, stale result, recovery.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-055 FROZEN ARTIFACT LIFECYCLE/STORE/RECONCILIATION AUTHORITY + AUDIT CURRENT GENERATIONJOB/ARTIFACT/MEDIA/PERSISTENCE SURFACES BEFORE CODE"


---

## IMP-055 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-06

- [x] Read Frozen Master artifact materialization state + exact legal transition table.
- [x] Confirm GenerationJob artifact axis remains sole mutable lifecycle owner.
- [x] Confirm no existing canonical Artifact Store/Reconciler owner in `agent/studio`.
- [x] Confirm persistence currently ends at migration v8; IMP-055 may add metadata/evidence schema only, not shadow status.
- [x] Confirm startup reconciliation must handle staging/final crash windows, orphan final bytes, READY-missing and READY-corrupt cases.
- [ ] Add migration v9 immutable artifact identity + append-only materialization/reconciliation evidence.
- [ ] Implement Artifact Store + startup reconciler over existing GenerationJob CAS artifact transitions.
- [ ] Tests: crash at each stage, missing file, orphan final, corruption, stale result, recovery/archive, creative-axis non-leakage.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "IMPLEMENT MIGRATION V9 IMMUTABLE ARTIFACT IDENTITY + APPEND-ONLY MATERIALIZATION EVIDENCE + ARTIFACT STORE/STARTUP RECONCILER -> TARGETED FAULT-INJECTION TESTS"


---

## IMP-055 TARGETED + RECOVERY CHECKPOINT PASS - 2026-10-06

- [x] IMP-055 targeted artifact lifecycle = 10/10 PASS (`imp055-targeted-a.xml` 5/5 + `imp055-targeted-b-resume.xml` 5/5).
- [x] Affected recovery regression = 11/11 PASS (PTY exit 0).
- [ ] Remaining affected persistence/generation regression.
- [ ] Broader unit regression.
- [ ] Frozen Master guard / semantic SHA unchanged.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN ONLY REMAINING IMP-055 AFFECTED PERSISTENCE/GENERATION REGRESSION -> BROADER UNIT REGRESSION -> FROZEN MASTER GUARD; DO NOT RERUN TARGETED 10/10 OR RECOVERY 11/11"


---

## IMP-055 RESUME CHECKPOINT / BROADER REGRESSION RUNNING - 2026-10-06

- [x] IMP-055 targeted artifact lifecycle = 10/10 PASS.
- [x] IMP-055 recovery affected = 11/11 PASS.
- [x] IMP-055 persistence + GenerationJob affected = 32/32 PASS.
- [x] Frozen Master guard PASS at `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [x] `git diff --check` PASS.
- [ ] Broader regression batch A running under FileMCP PTY, root PID 72412; `active_profile + brainpack + entity + invalidation`; JUnit `.tmp/imp055-broad-a.xml`.
- [ ] Remaining non-overlapping broader regression batches.
- [ ] Static compile/leakage/TODO checks + evidence document.
- [ ] Side-effect guard -> commit/push/PR/CI/exact-head review/merge/main verify/governance sync.

NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER BATCH A PID 72412 / PTY TO EXIT; DO NOT RESTART; VERIFY JUNIT; THEN RUN ONLY REMAINING NON-OVERLAPPING BROADER BATCHES"


---

## IMP-055 AFFECTED CORE PASS - 2026-10-06

- [x] Targeted artifact lifecycle = 10/10 PASS.
- [x] Affected recovery = 11/11 PASS.
- [x] Affected persistence/generation = 32/32 PASS (`.tmp/imp055-affected-core.xml`, errors=0, failures=0).
- [ ] Broader unit regression.
- [ ] Frozen Master guard / semantic SHA unchanged.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN BROADER UNIT REGRESSION ONCE -> FROZEN MASTER GUARD / SEMANTIC SHA CHECK -> EVIDENCE + VERIFY; DO NOT RERUN TARGETED/RECOVERY/AFFECTED CORE"


---

## IMP-055 BROADER A REPAIRED / REMAINING BROADER RUNNING - 2026-10-06

- [x] Broader batch A unaffected cases = 35 PASS.
- [x] Exact batch A failure identified as stale migration-history expectation in `test_studio_brainpack.py`.
- [x] Expectation extended with migration v9 only; failed testcase rerun = 1/1 PASS.
- [ ] Remaining non-overlapping broader regression running under FileMCP PTY, root PID 69624; JUnit `.tmp/imp055-broad-rest.xml`.
- [ ] Static compile/leakage/TODO checks + evidence document.
- [ ] Side-effect guard -> commit/push/PR/CI/exact-head review/merge/main verify/governance sync.

NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER-REST PID 69624 / PTY TO EXIT; DO NOT RESTART; VERIFY JUNIT; IF FAIL FIX ONLY EXACT FAILURES; IF PASS RUN STATIC COMPILE/LEAKAGE/TODO CHECKS -> EVIDENCE -> SIDE-EFFECT GUARD"


---

## IMP-055 BROADER UNIT REGRESSION RUNNING - 2026-10-06

- [x] Targeted artifact lifecycle 10/10 PASS.
- [x] Affected recovery 11/11 PASS.
- [x] Affected persistence/generation 32/32 PASS.
- [~] Broader unit regression RUNNING under root PID 47368; final JUnit pending.
- [ ] Frozen Master guard / semantic SHA unchanged.
- [ ] Evidence / verify / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "IF PID 47368 STILL EXISTS: MONITOR ONLY; DO NOT RESTART. WHEN PROCESS ENDS, READ FINAL JUNIT AND CLASSIFY BROADER PASS/FAIL."


---

## IMP-055 LOCAL VERIFIED / SIDE-EFFECT GUARD NEXT - 2026-10-07

- [x] Frozen artifact lifecycle/store/reconciler authority read and current surfaces audited.
- [x] Migration v9 immutable artifact identity + append-only artifact evidence implemented.
- [x] Artifact Store / startup reconciler implemented over existing GenerationJob artifact axis.
- [x] Targeted artifact lifecycle = 10/10 PASS.
- [x] Affected recovery = 11/11 PASS.
- [x] Affected persistence/generation = 32/32 PASS.
- [x] Broader non-overlapping remainder = 166/166 PASS.
- [x] Schema-v9 stale migration expectation repaired; exact rerun = 1/1 PASS.
- [x] Exact-head review found and repaired crash-after-durable-event / before-state-transition replay defect.
- [x] New crash-window fault-injection = 1/1 PASS.
- [x] Direct post-review affected regression = 5/5 PASS.
- [x] py_compile + compileall + TODO/leakage scan + git diff --check PASS.
- [x] Frozen Master + freeze manifest unchanged; prior frozen guard PASS remains valid.
- [x] Evidence document: `evidence/tests/IMP-055_ARTIFACT_LIFECYCLE_RECONCILER_EVIDENCE.md`.
- [!] Full Windows `tests/unit` execution remains FAIL (803 / 7 failures / 22 errors): one stale-collected migration expectation has exact current-state PASS; 28 remaining failures/errors are unchanged Windows path / UTF-8 setup / ffmpeg-missing surfaces. Do not relabel full suite PASS and do not restart it.
- [ ] Side-effect guard: duplicate commit/push/PR + exact scope.
- [ ] Stage exact IMP-055 scope excluding `.tmp`.
- [ ] Commit.
- [ ] Push / PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification.
- [ ] Governance-only state sync / MAIN VERIFIED.
- [ ] Read DAG/queue and claim next dependency-ready task.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> VERIFY NO DUPLICATE IMP-055 COMMIT/PUSH/PR -> INSPECT/STAGE EXACT SCOPE EXCLUDING .tmp -> COMMIT"


---

## IMP-055 SIDE-EFFECT GUARD PASS - 2026-10-07

- [x] Verify no duplicate local commit since base.
- [x] Verify remote IMP-055 branch absent.
- [x] Verify no upstream branch.
- [x] Verify no existing IMP-055 PR.
- [x] Verify exact scope; `.tmp/` excluded.
- [ ] Stage exact scope.
- [ ] Inspect staged diff/status.
- [ ] Commit.
- [ ] Push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "STAGE EXACT IMP-055 SCOPE EXCLUDING .tmp -> VERIFY STAGED DIFF -> COMMIT"


---

## IMP-055 FEATURE COMMIT CREATED - 2026-10-07

- [x] Exact scope staged and cached diff verified.
- [x] Feature commit `d871abaae8ec8e294274d9c0c44390d95dd0196d` created.
- [ ] Governance-only state sync commit.
- [ ] Push branch.
- [ ] Create PR.
- [ ] Ubuntu CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main.
- [ ] Post-merge main verification.
- [ ] Governance-only MAIN VERIFIED sync.
- [ ] Claim next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT GOVERNANCE-ONLY STATE SYNC -> PUSH BRANCH -> CREATE PR -> VERIFY CI"


---

## IMP-055 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-07

- [x] Feature commit `d871abaae8ec8e294274d9c0c44390d95dd0196d`.
- [x] Feature PR #64 exact head `3b69ebbac571b502c81d85959ed6f7a34bdf0d22`.
- [x] PR CI run `37507839217` SUCCESS Python 3.10 / 3.13 + frozen baseline.
- [x] Final exact-head review PASS.
- [x] PR #64 merged at `7ab973b311a3fa2541194a5034781c115006afd6`.
- [x] Local main fast-forwarded to exact merge SHA.
- [x] Main push workflow `37509449416` SUCCESS Python 3.10 / 3.13 + frozen baseline exact merge SHA.
- [x] IMP-055 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge + push-main CI on exact governance SHA.
- [ ] Mark IMP-055 governance MAIN VERIFIED.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-055 GOVERNANCE-ONLY STATE SYNC -> VERIFY GOVERNANCE MAIN CI -> MARK IMP-055 MAIN VERIFIED -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-055 GOVERNANCE VERIFIED / IMP-060 CLAIMED - 2026-10-07

- [x] IMP-055 governance PR #65 merged at `71e4a36ae79472daf6ceb3faed3a3e248638b510`.
- [x] Governance push-main workflow `37563172738` SUCCESS Python 3.10 / 3.13 exact governance SHA.
- [x] IMP-055 = MAIN VERIFIED.
- [x] Verify IMP-060 dependencies: IMP-032 + IMP-042 + IMP-041 + IMP-055 MAIN VERIFIED.
- [x] Verify no local/remote branch or PR duplicate for `chatgpt/IMP-060-static-qa`.
- [x] Claim `chatgpt/IMP-060-static-qa` from clean governance main `71e4a36ae79472daf6ceb3faed3a3e248638b510`.
- [ ] Read frozen Static QA authority and reviewed policy-spike lineage.
- [ ] Audit current GenerationJob creative axis, READY artifact evidence, FullShotSpec/StaticKeyframeSpec, StateSnapshot, ReferenceAsset and legacy review donor surfaces.
- [ ] Implement provider-neutral Static QA contract/repository/evaluator boundary with exact-version evidence binding.
- [ ] Tests: blocking identity/state defect, evaluator failure -> QA_ERROR, stale/evidence binding, no weighted-average masking.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-060 FROZEN STATIC QA AUTHORITY + AUDIT CURRENT SURFACES -> LOCK CONTRACT/POLICY/EVALUATOR BOUNDARY -> CODE"


---

## IMP-060 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-07

- [x] Read Frozen Master §74 Static QA + local contract completeness.
- [x] Read reviewed Static QA policy-spike lineage; treat it as policy evidence, not vision-calibration proof.
- [x] Audit GenerationJob creative transition authority and READY artifact requirement.
- [x] Audit IMP-055 immutable artifact identity/materialization evidence.
- [x] Audit FullShotSpec/StaticKeyframeSpec exact source bindings.
- [x] Audit StateSnapshot + ReferenceAsset/Resolver exact-version surfaces.
- [x] Audit legacy `video_reviewer.py`; donor only, no provider-specific canonical authority.
- [x] Lock blocking policy: BLOCKING FAIL -> overall FAIL independent of aggregate score.
- [x] Lock failure taxonomy: evaluator failure -> QA_ERROR; artifact defect -> QA_FAILED.
- [ ] Implement provider-neutral Static QA contract/repository/evaluator orchestration.
- [ ] Add targeted tests: blocking identity/state, evaluator error, evidence/stale binding, no average masking.
- [ ] Targeted + affected + broader regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "CODE IMP-060 STATIC QA CONTRACT/REPOSITORY/EVALUATOR BOUNDARY -> RUN TARGETED TESTS"


---

## IMP-060 TARGETED STATIC QA CHECKPOINT - 2026-10-07

- [x] Static QA contract/repository/evaluator orchestration implemented in `agent/studio/static_qa.py` with exports.
- [x] Syntax/import gate PASS.
- [x] No-average masking policy case PASS.
- [x] Shared fixture root cause for initial 4 failures isolated; no product-code root cause.
- [x] Exact failed subset rerun = 4/4 PASS (`.tmp/imp060-failed-rerun.xml`).
- [x] Exact fixture-affected previous PASS subset rerun = 2/2 PASS (`.tmp/imp060-affected2.xml`).
- [x] Effective targeted current checkpoint = 7/7 PASS.
- [ ] Affected existing regression: GenerationJob + artifact lifecycle + shot realization + production compiler + state/reference surfaces.
- [ ] Exact-head review and fault/authority audit.
- [ ] Broader regression + frozen guard.
- [ ] Evidence / verify / side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN AFFECTED EXISTING REGRESSION ONLY -> EXACT-HEAD REVIEW -> FIX ONLY REAL DEFECTS -> BROADER/FROZEN GUARD"


---

## IMP-060 AFFECTED REGRESSION ACTIVE - 2026-10-07

- [x] Targeted effective checkpoint = 7/7 PASS.
- [~] Affected regression RUNNING under PTY `pty_59740a1745254ebfa0f105108b33a3b185b7`, root PID `67100`, pytest PID `58700`.
- [ ] Finalize `.tmp/imp060-affected.xml`; classify PASS/FAIL from durable evidence only.
- [!] Exact-head review finding queued: load/bind actual `ShotIR` and expose `qa_expectations` to evaluator; current subject only exposes `shot_ir_ref` and does not fully satisfy Frozen Master §74 input contract.
- [ ] After affected run exits, repair only this finding and rerun impacted Static QA cases.
- [ ] Continue exact-head review -> broader regression -> frozen guard -> evidence/Git/PR lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED RUN; DO NOT RESTART -> FINAL JUNIT -> FIX SHOTIR EXPECTATION-BINDING GAP -> IMPACTED STATIC QA RERUN"


---

## IMP-060 AFFECTED REGRESSION PASS / REVIEW FIX - 2026-10-07

- [x] Effective targeted checkpoint = 7/7 PASS.
- [x] Affected existing regression = **105/105 PASS**, failures=0, errors=0, skipped=0 (`.tmp/imp060-affected.xml`), PTY exit 0.
- [x] Exact-head review confirms completed StaticQAResult already enforces exactly one finding per 10 canonical dimensions; no repair needed there.
- [!] Review gap: evaluator must receive exact loaded ShotIR + `qa_expectations`, not only ref.
- [!] Review gap: QAResult provenance/dependencies must directly pin ActiveProductionProfile and finding-level canonical source refs.
- [!] Review gap: evaluator id/version response must match evaluator port and evaluator/policy versions must be recorded in provenance evidence.
- [!] Review gap: auto-approval policy default must be fail-closed; automatic approval only when explicit versioned policy enables it.
- [ ] Patch only Static QA new surfaces and rerun impacted targeted cases.
- [ ] Continue exact-head review -> broader valid regression -> frozen guard -> evidence/Git/PR lifecycle.

NEXT_EXACT_ACTION = "PATCH STATIC QA REVIEW GAPS -> PYCOMPILE/IMPORT -> RERUN IMPACTED TARGETED STATIC QA CASES ONLY"


---

## IMP-060 REVIEW-FIX TARGETED PASS - 2026-10-07

- [x] Targeted baseline effective 7/7 PASS.
- [x] Existing affected regression 105/105 PASS; do not rerun.
- [x] Exact-head review repaired ShotIR expectation binding, exact ShotIR/static/full/state/profile/reference lineage, direct ActiveProductionProfile + finding source provenance, evaluator identity/version matching, evaluator/policy/finding evidence, and fail-closed default auto-approval.
- [x] Review-fix targeted 9/9 PASS (`.tmp/imp060-review-targeted.xml`, exit 0).
- [ ] Exact-head static/diff review.
- [ ] Non-overlapping broader valid Windows regression.
- [ ] Frozen Master guard.
- [ ] Evidence / side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "EXACT-HEAD STATIC REVIEW + GIT DIFF CHECK -> RUN NON-OVERLAPPING BROADER VALID WINDOWS REGRESSION (DO NOT RERUN AFFECTED 105/105) -> FROZEN MASTER GUARD -> EVIDENCE/SIDE-EFFECT GUARD"


## IMP-060 BROADER VALID WINDOWS REGRESSION RUNNING - 2026-10-07

- [x] Exact-head static/diff review PASS.
- [~] Non-overlapping broader valid Windows regression RUNNING under PTY `pty_9eda7f0a9e5e1e13e72aa1f4781661c69006`, PID `66700`.
- [ ] Finalize `.tmp/imp060-broader-valid.xml` and classify from final exit/JUnit only.
- [ ] Frozen Master guard.
- [ ] Evidence / side-effect guard / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "MONITOR EXISTING PTY pty_9eda7f0a9e5e1e13e72aa1f4781661c69006; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD"


## IMP-060 BROADER VALID WINDOWS REGRESSION PASS - 2026-10-07

- [x] Exact-head static/diff review PASS.
- [x] Non-overlapping broader valid Windows regression = 654 PASS / 3 deselected (`.tmp/imp060-broader-valid.xml`, exit 0).
- [ ] Frozen Master guard.
- [ ] Evidence / side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD -> VERIFY SEMANTIC SHA/STATIC GATES -> EVIDENCE/SIDE-EFFECT GUARD"


## IMP-060 FROZEN MASTER GUARD PASS - 2026-10-07

- [x] Frozen Master guard PASS.
- [x] Frozen semantic SHA unchanged: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Final static verification.
- [ ] Evidence / side-effect guard / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN FINAL STATIC VERIFICATION WITHOUT RERUNNING TEST STAGES -> WRITE IMP-060 EVIDENCE -> SIDE-EFFECT GUARD"


## IMP-060 LOCAL VERIFIED / SIDE-EFFECT GUARD PASS - 2026-10-07

- [x] Final static verification PASS: py_compile, compileall, import gate, diff-check, leakage scan, TODO scan.
- [x] Evidence = `evidence/tests/IMP-060_STATIC_QA_EVIDENCE.md`.
- [x] Side-effect guard PASS: no existing IMP-060 commit, remote branch or PR; staged index empty; `.tmp` excluded.
- [ ] Stage exact IMP-060 source/test/evidence/state scope.
- [ ] Commit / push / PR.
- [ ] CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main / main verify / governance sync.

NEXT_EXACT_ACTION = "STAGE EXACT IMP-060 SCOPE -> VERIFY INDEX -> COMMIT -> PUSH -> CREATE PR"


## IMP-060 FEATURE COMMIT CREATED - 2026-10-07

- [x] Exact 7-file feature scope committed.
- [x] Feature commit `09529977f51295d7288bacd7443b6c6866894bc7` created.
- [ ] Governance-only state sync commit.
- [ ] Push branch / create PR.
- [ ] CI Python 3.10 / 3.13 + frozen guard.
- [ ] Exact-head review / merge main / main verify / governance sync.

NEXT_EXACT_ACTION = "COMMIT GOVERNANCE-ONLY STATE SYNC -> SIDE-EFFECT GUARD -> PUSH BRANCH -> CREATE PR -> VERIFY CI"


## IMP-060 POST-MERGE MAIN TARGETED RUNNING - 2026-10-07

- [x] PR #66 exact-head CI run `37589325071` SUCCESS Python 3.10 / 3.13 + Frozen guard.
- [x] PR #66 merged to main at `71bde3940e4ea74399669731e071cb02a98a08de`.
- [~] Post-merge Static QA targeted RUNNING under PTY `pty_6084cd9bf86caa5167c5626851cc726086c2`, PID `26916`.
- [ ] Post-merge affected 8-file regression.
- [ ] Frozen Master guard.
- [~] Main push workflow `37590060906` RUNNING on exact merge SHA.
- [ ] Mark feature MAIN VERIFIED -> governance-only state sync -> next dependency-ready task.

NEXT_EXACT_ACTION = "MONITOR EXISTING POST-MERGE TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> AFFECTED 8-FILE MAIN REGRESSION -> FROZEN GUARD -> VERIFY MAIN PUSH CI"


## IMP-060 POST-MERGE MAIN TARGETED PASS / MAIN CI PASS - 2026-10-07

- [x] Post-merge Static QA targeted = 9/9 PASS (`.tmp/imp060-main-targeted.xml`, exit 0).
- [x] Main push workflow `37590060906` SUCCESS on exact merge SHA `71bde3940e4ea74399669731e071cb02a98a08de`.
- [ ] Post-merge affected 8-file regression.
- [ ] Frozen Master guard.
- [ ] Mark IMP-060 feature MAIN VERIFIED -> governance-only state sync -> governance CI/merge/main verify -> next dependency-ready task.

NEXT_EXACT_ACTION = "RUN POST-MERGE AFFECTED 8-FILE REGRESSION ONLY -> FROZEN MASTER GUARD -> MARK IMP-060 FEATURE MAIN VERIFIED"


## IMP-060 POST-MERGE MAIN AFFECTED REGRESSION RUNNING - 2026-10-07

- [x] Post-merge targeted = 9/9 PASS.
- [x] Main push workflow `37590060906` SUCCESS exact merge SHA.
- [~] Post-merge affected 8-file regression RUNNING under PTY `pty_369c47c0e547e5957f27a8bc855916755f47`, PID `66228`.
- [ ] Finalize `.tmp/imp060-main-affected.xml`; classify only from final JUnit/exit.
- [ ] Frozen Master guard.
- [ ] Mark IMP-060 feature MAIN VERIFIED -> governance-only state sync -> governance CI/merge/main verify -> next dependency-ready task.

NEXT_EXACT_ACTION = "MONITOR EXISTING POST-MERGE AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD -> MARK IMP-060 FEATURE MAIN VERIFIED"


## IMP-060 POST-MERGE MAIN AFFECTED PASS - 2026-10-07

- [x] Post-merge targeted = 9/9 PASS.
- [x] Post-merge affected 8-file regression = 105/105 PASS (`.tmp/imp060-main-affected.xml`).
- [x] Main push CI `37590060906` SUCCESS exact merge SHA `71bde3940e4ea74399669731e071cb02a98a08de`.
- [ ] Frozen Master guard on exact main SHA.
- [ ] Mark IMP-060 feature MAIN VERIFIED.
- [ ] Governance-only state sync / PR / CI / merge / governance main verify.
- [ ] Claim next dependency-ready task.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON MAIN -> MARK IMP-060 FEATURE MAIN VERIFIED -> GOVERNANCE-ONLY STATE SYNC"


## IMP-060 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-07

- [x] Feature PR #66 merged at `71bde3940e4ea74399669731e071cb02a98a08de`.
- [x] Post-merge targeted = 9/9 PASS.
- [x] Post-merge affected = 105/105 PASS.
- [x] Frozen Master guard PASS / semantic SHA unchanged.
- [x] Main push workflow `37590060906` SUCCESS exact merge SHA.
- [x] IMP-060 feature implementation = MAIN VERIFIED.
- [ ] Commit/push/PR/merge governance-only state sync.
- [ ] Verify governance merge + push-main CI.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "CREATE GOVERNANCE BRANCH chatgpt/IMP-060-main-verified-state -> COMMIT/PUSH/PR/MERGE STATE-ONLY SYNC -> VERIFY GOVERNANCE MAIN CI -> CLAIM NEXT DEPENDENCY-READY TASK"


## IMP-060 GOVERNANCE VERIFIED / IMP-061 CLAIMED - 2026-10-07

- [x] IMP-060 governance PR #67 merged at `56906ffd2dc4b282a5e8d6802cd939fe1a2b8537`.
- [x] Governance push-main workflow `37596114723` SUCCESS Python 3.10 / 3.13 + Frozen guard exact governance SHA.
- [x] IMP-060 = MAIN VERIFIED.
- [x] Verify IMP-061 dependencies: IMP-032 + IMP-042 + IMP-055 MAIN VERIFIED.
- [x] Verify no local/remote branch or PR duplicate for `chatgpt/IMP-061-motion-video-qa`.
- [x] Claim `chatgpt/IMP-061-motion-video-qa` from clean governance main `56906ffd2dc4b282a5e8d6802cd939fe1a2b8537`.
- [ ] Read Frozen Motion/Video QA authority and audit current donor/canonical surfaces.
- [ ] Implement provider-neutral time-bound Motion/Video QA contract/repository/evaluator orchestration.
- [ ] Tests: provider success != QA pass, time-range findings, evaluator error, evidence binding.
- [ ] Targeted + affected + broader valid regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ IMP-061 FROZEN MOTION/VIDEO QA AUTHORITY + AUDIT VIDEO REVIEW DONOR / GENERATIONJOB / ARTIFACT / SHOTIR / STATE SURFACES -> LOCK CONTRACT -> CODE"


## IMP-061 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-07

- [x] Read Frozen Master §75 Video/Motion QA + FM2-003 local contract completeness.
- [x] Audit legacy `agent/services/video_reviewer.py`; KEEP+EXTEND extraction/time-range donor only, not canonical verdict/provider authority.
- [x] Audit GenerationJob creative transitions and READY artifact gate.
- [x] Audit MotionDeltaSpec/FullShotSpec/StaticKeyframeSpec/ShotIR exact lineage and QA expectations.
- [x] Lock provider-neutral evaluator boundary and exact provenance/dependency bindings.
- [x] Lock failure taxonomy: evaluator/tool failure -> QA_ERROR; artifact defect -> QA_FAILED.
- [x] Lock provider-success invariant: provider success alone cannot imply Motion QA pass.
- [ ] Implement Motion QA contract/service/repository/evaluator orchestration.
- [ ] Add targeted tests: provider success != pass, time-range findings, evaluator error, stale/evidence binding, blocking cannot be averaged away.
- [ ] Targeted + affected + broader valid regression + frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "CODE agent/studio/motion_qa.py + EXPORTS + TARGETED TESTS -> PYCOMPILE/IMPORT -> RUN TARGETED IMP-061"


## IMP-061 TARGETED RUNNING - 2026-10-07

- [x] Authority/surface audit PASS.
- [x] Draft Motion QA contract/service implemented; public export added.
- [x] `py_compile` + public import + `git diff --check` PASS.
- [~] Targeted `tests/unit/test_studio_motion_qa.py` RUNNING under PTY `pty_74534fa4f00996a377efc16c36855a37f27e`, root PID `59116`.
- [ ] Classify `.tmp/imp061-targeted.xml` from final JUnit/exit only.
- [ ] Affected regression / exact-head review / broader valid regression / frozen guard.

NEXT_EXACT_ACTION = "MONITOR EXISTING PTY pty_74534fa4f00996a377efc16c36855a37f27e; DO NOT RESTART -> FINAL JUNIT/EXIT -> FIX/RERUN ONLY FAILING CASES IF ANY"


## IMP-061 TARGETED PASS - 2026-10-07

- [x] Authority/surface audit PASS.
- [x] Motion QA contract/service + public exports + targeted tests implemented.
- [x] py_compile/public import/diff gate PASS.
- [x] Targeted `tests/unit/test_studio_motion_qa.py` = 8/8 PASS (`.tmp/imp061-targeted.xml`).
- [ ] Exact-head review; fix only real defects if any.
- [ ] Affected regression without rerunning targeted 8/8.
- [ ] Broader valid regression + Frozen Master guard.
- [ ] Evidence / verify / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "EXACT-HEAD REVIEW motion_qa.py + exports/tests -> FIX ONLY REAL DEFECTS IF ANY -> RUN AFFECTED REGRESSION WITHOUT TARGETED RERUN"


## IMP-061 REVIEW-FIX TARGETED PASS - 2026-10-07

- [x] Exact-head review found and fixed direct EntityVersion provenance gap for identity-drift authority.
- [x] Review-fix static gate PASS.
- [x] Review-fix targeted = 8/8 PASS, exit 0 (`.tmp/imp061-review-targeted.xml`).
- [x] Preserve original targeted 8/8 evidence; no duplicate rerun after exact-head PASS.
- [ ] Affected authority regression: generation_job + artifact_lifecycle + shot_realization + production_compiler + state_continuity + reference + versioning + invalidation.
- [ ] Broader valid Windows regression excluding known invalid platform cases and all already-PASS targeted/affected files.
- [ ] Frozen Master guard / evidence / verify / commit / push / PR / CI / review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN AFFECTED 8-FILE AUTHORITY REGRESSION WITHOUT test_studio_motion_qa.py -> FINAL JUNIT/EXIT -> BROADER VALID REGRESSION -> FROZEN GUARD"


## IMP-061 AFFECTED REGRESSION RUNNING - 2026-10-07

- [x] Review-fix targeted 8/8 PASS.
- [~] Affected 8-file authority regression RUNNING under PTY `pty_77852684c4110c63d0ca723e89852d24f5f7`, PID `62760`.
- [ ] Finalize `.tmp/imp061-affected.xml` from final JUnit/exit only.
- [ ] Broader valid Windows regression excluding known platform-invalid cases and already-PASS targeted/affected files.
- [ ] Frozen Master guard / evidence / verify / lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> BROADER VALID REGRESSION"


## IMP-061 AFFECTED REGRESSION PASS - 2026-10-07

- [x] Review-fix targeted = 8/8 PASS.
- [x] Affected 8-file authority regression = 105/105 PASS (`.tmp/imp061-affected.xml`, failures=0, errors=0, skipped=0).
- [ ] Non-overlapping broader valid Windows regression with established platform exclusions and current targeted/affected files ignored.
- [ ] Frozen Master guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN NON-OVERLAPPING BROADER VALID WINDOWS REGRESSION -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD"


## IMP-061 BROADER VALID WINDOWS REGRESSION RUNNING - 2026-10-07

- [x] Review-fix targeted 8/8 PASS.
- [x] Affected authority regression 105/105 PASS.
- [~] Non-overlapping broader valid Windows regression RUNNING under PTY `pty_dc88b5d28e4050d8ce7f26a896fef4d437df`, PID `59912`.
- [ ] Finalize `.tmp/imp061-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard / evidence / lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD"


## IMP-061 BROADER VALID WINDOWS REGRESSION PASS - 2026-10-07

- [x] Review-fix targeted 8/8 PASS.
- [x] Affected authority regression 105/105 PASS.
- [x] Non-overlapping broader valid Windows regression = 663 PASS / 3 deselected (`.tmp/imp061-broader-valid.xml`, exit 0).
- [ ] Frozen Master guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD -> VERIFY SEMANTIC SHA / STATIC GATES -> EVIDENCE / SIDE-EFFECT GUARD"


## IMP-061 FROZEN MASTER GUARD PASS - 2026-10-07

- [x] Review-fix targeted 8/8 PASS.
- [x] Affected authority regression 105/105 PASS.
- [x] Non-overlapping broader valid Windows regression 663 PASS / 3 deselected.
- [x] Frozen Master guard PASS; semantic SHA `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287` unchanged.
- [ ] Create evidence and exact-scope/side-effect guard.
- [ ] Commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "CREATE IMP-061 EVIDENCE -> EXACT-SCOPE / SIDE-EFFECT GUARD -> COMMIT IF CLEAN"


## IMP-061 LOCAL VERIFIED - 2026-10-07

- [x] Targeted review-fix 8/8 PASS.
- [x] Affected authority regression 105/105 PASS.
- [x] Broader valid Windows regression 663 PASS / 3 deselected.
- [x] Frozen Master guard PASS.
- [x] Evidence created: `evidence/tests/IMP-061_MOTION_VIDEO_QA_EVIDENCE.md`.
- [x] Side-effect guard PASS: no existing commit/remote branch/upstream/PR.
- [ ] Stage exact 7 files excluding `.tmp`, verify index, commit feature.
- [ ] Push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "STAGE EXACT 7 IMP-061 FILES EXCLUDING .tmp -> VERIFY INDEX -> COMMIT FEATURE"


## IMP-061 LOCAL VERIFIED / COMMIT NEXT - 2026-10-07

- [x] Review-fix targeted 8/8 PASS.
- [x] Affected authority regression 105/105 PASS.
- [x] Broader valid Windows regression 663 PASS / 3 deselected.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Evidence created: `evidence/tests/IMP-061_MOTION_VIDEO_QA_EVIDENCE.md`.
- [x] Exact-scope / side-effect guard PASS: no commit/remote/upstream/PR duplicate; exact non-`.tmp` scope = 7 files.
- [ ] Stage exact 7 files excluding `.tmp`, verify index, commit feature.
- [ ] Push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "STAGE EXACT 7 IMP-061 FILES EXCLUDING .tmp -> VERIFY INDEX / DIFF-CHECK -> COMMIT FEATURE"


## IMP-061 FEATURE COMMIT CREATED - 2026-10-07

- [x] Feature commit created: `4b8c1143792ee2118449799f124dc96c96faac85` (`feat(studio): add motion video qa gate`).
- [x] Worktree clean except untracked `.tmp/` runtime evidence.
- [ ] Governance-only state sync commit.
- [ ] Side-effect guard -> push -> PR -> CI -> exact-head review -> merge -> main verify -> governance sync.

NEXT_EXACT_ACTION = "SYNC EXACT FEATURE COMMIT INTO 3 STATE FILES -> GOVERNANCE-ONLY COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-061 POST-MERGE MAIN TARGETED RUNNING - 2026-10-07

- [x] PR #68 merged to `main` at `74789c209ef57983405726607af4e28c1d3c5ff4` after exact-head CI/review PASS.
- [~] Post-merge Motion QA targeted RUNNING under PTY `pty_db4db4a3fe79b02652c669619e5f76a745ed`, PID `58648`.
- [ ] Finalize `.tmp/imp061-main-targeted.xml` from final JUnit/exit only.
- [ ] Main affected authority regression (only after targeted PASS).
- [ ] Main Frozen Master guard + verify push-main CI `37614346927` exact merge SHA.
- [ ] Mark MAIN VERIFIED -> governance-only sync lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> MAIN AFFECTED IF PASS"


## IMP-061 POST-MERGE MAIN TARGETED PASS - 2026-10-07

- [x] Post-merge Motion QA targeted = 8/8 PASS (`.tmp/imp061-main-targeted.xml`, exit 0).
- [ ] Post-merge affected authority regression (8 existing authority files only).
- [ ] Main Frozen Master guard.
- [ ] Verify push-main CI `37614346927` SUCCESS on exact merge SHA.
- [ ] MAIN VERIFIED -> governance-only sync lifecycle.

NEXT_EXACT_ACTION = "RUN POST-MERGE MAIN AFFECTED 8-FILE AUTHORITY REGRESSION -> FINAL JUNIT/EXIT -> MAIN FROZEN GUARD"


## IMP-061 POST-MERGE MAIN AFFECTED RUNNING - 2026-10-07

- [x] Post-merge Motion QA targeted 8/8 PASS.
- [~] Post-merge affected 8-file authority regression RUNNING under PTY `pty_88b6b2bef57e105af6cb98f4c9d4641e3c27`, PID `63016`; Motion QA targeted excluded.
- [ ] Finalize `.tmp/imp061-main-affected.xml` from final JUnit/exit only.
- [ ] Main Frozen Master guard.
- [ ] Verify push-main CI `37614346927` exact merge SHA SUCCESS.
- [ ] MAIN VERIFIED -> governance-only sync lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> MAIN FROZEN GUARD IF PASS"


## IMP-061 PUSH-MAIN CI PASS / MAIN AFFECTED RUNNING - 2026-10-07

- [x] Push-main CI `37614346927` SUCCESS on exact merge SHA `74789c209ef57983405726607af4e28c1d3c5ff4`; Python 3.10 + 3.13 + Frozen guard PASS.
- [x] Post-merge Motion QA targeted 8/8 PASS.
- [~] Main affected regression continues under PTY `pty_88b6b2bef57e105af6cb98f4c9d4641e3c27`, PID `63016`.
- [ ] Final JUnit/exit -> main Frozen guard -> MAIN VERIFIED.

NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> MAIN FROZEN GUARD"


## IMP-061 POST-MERGE MAIN AFFECTED PASS - 2026-10-07

- [x] Post-merge Motion QA targeted 8/8 PASS.
- [x] Post-merge affected 8-file authority regression = 105/105 PASS (`.tmp/imp061-main-affected.xml`, failures=0, errors=0, skipped=0).
- [x] Push-main CI `37614346927` SUCCESS on exact merge SHA `74789c209ef57983405726607af4e28c1d3c5ff4`.
- [ ] Main Frozen Master guard.
- [ ] Mark IMP-061 feature MAIN VERIFIED -> governance-only sync lifecycle.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT MAIN SHA -> IF PASS MARK IMP-061 FEATURE MAIN VERIFIED -> GOVERNANCE-ONLY STATE SYNC"


## IMP-061 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-07

- [x] Feature PR #68 merged at `74789c209ef57983405726607af4e28c1d3c5ff4`.
- [x] Post-merge targeted = 8/8 PASS.
- [x] Post-merge affected = 105/105 PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Main push workflow `37614346927` SUCCESS Python 3.10 / 3.13 exact merge SHA.
- [x] IMP-061 feature implementation = MAIN VERIFIED.
- [ ] Governance-only state sync.
- [ ] Verify governance merge + push-main CI.
- [ ] Read DAG/queue and CLAIM next dependency-ready task.

NEXT_EXACT_ACTION = "CREATE GOVERNANCE BRANCH chatgpt/IMP-061-main-verified-state -> STATE-ONLY COMMIT -> PUSH/PR/MERGE -> VERIFY GOVERNANCE MAIN CI -> CLAIM NEXT DEPENDENCY-READY TASK"


## IMP-061 GOVERNANCE VERIFIED / IMP-062 CLAIMED - 2026-10-07

- [x] IMP-061 governance PR #69 merged at `742a50a76920003f598207f117b6919606d7c760`.
- [x] Governance push-main CI `37646746349` SUCCESS Python 3.10 / 3.13 + Frozen guard on exact governance SHA.
- [x] IMP-061 = MAIN VERIFIED.
- [x] Verify IMP-062 dependencies: IMP-060 + IMP-061 + IMP-042 + IMP-025 MAIN VERIFIED.
- [x] Verify no local/remote branch or PR duplicate for `chatgpt/IMP-062-continuity-sequence-qa`.
- [x] Claim `chatgpt/IMP-062-continuity-sequence-qa` from clean governance main `742a50a76920003f598207f117b6919606d7c760`.
- [ ] Read Frozen Continuity QA + Sequence QA authority and audit current canonical/donor surfaces.
- [ ] Implement provider-neutral Continuity QA + Sequence QA contracts/services/repositories.
- [ ] Tests: state contradiction over visual similarity; adjacent shot drift; sequence causality/coverage; stale/evaluator failure/provenance.
- [ ] Targeted + affected + broader valid regression + Frozen guard.
- [ ] Evidence / verify / commit / push / PR / CI / exact-head review / merge / main verify / governance sync.

NEXT_EXACT_ACTION = "READ FROZEN MASTER §76 CONTINUITY QA + §77 SEQUENCE QA -> AUDIT STATIC/MOTION QA, STATE CONTINUITY, STORY HIERARCHY, APPROVED ARTIFACT SURFACES -> LOCK CONTRACT -> CODE"


## IMP-062 AUTHORITY AUDIT PASS / CODE NEXT - 2026-10-07

- [x] Read Frozen Master §76 Continuity QA and §77 Sequence QA.
- [x] Audit StaticQA/MotionQA, StateSnapshot/ContinuityLedger, Sequence/Scene, ShotListManifest and SetupPayoffLink authority surfaces.
- [x] Lock reuse strategy = KEEP+EXTEND; no second Story/Shot/State authority; no schema migration.
- [x] Lock hard invariants: canonical state contradiction beats visual similarity; per-shot PASS cannot guarantee Sequence PASS; findings localize exact shot/scene/transition spans; stale exact versions fail closed.
- [ ] Implement provider-neutral Continuity QA + Sequence QA immutable contracts/services/repositories.
- [ ] Targeted tests: contradiction, adjacent drift, sequence causality/coverage, stale input, evaluator error, provenance/dependency binding.
- [ ] Affected/broader regression + Frozen guard -> evidence/verify/Git lifecycle.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-062 CONTINUITY QA + SEQUENCE QA + TARGETED TESTS"


## IMP-062 TARGETED PASS / AFFECTED NEXT - 2026-10-07

- [x] Implementation module + public exports + targeted contract tests added.
- [x] Static compile + `git diff --check` PASS.
- [x] Targeted `tests/unit/test_studio_continuity_sequence_qa.py` = 7/7 PASS (`.tmp/imp062-targeted.xml`, exit 0).
- [ ] Affected 8-file authority regression: static_qa + motion_qa + state_continuity + narrative_hierarchy + shot_planning + screenplay_realization + invalidation + versioning.
- [ ] Broader valid regression + Frozen guard.
- [ ] Evidence / review / Git lifecycle / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN IMP-062 AFFECTED 8-FILE AUTHORITY REGRESSION ONLY -> FINAL JUNIT/EXIT -> BROADER VALID REGRESSION"


## IMP-062 AFFECTED PASS / BROADER NEXT - 2026-10-08

- [x] IMP-062 targeted = 7/7 PASS.
- [x] Affected authority regression = 89/89 PASS (`.tmp/imp062-affected.xml`, failures=0, errors=0, skipped=0).
- [ ] Broader valid Windows regression excluding targeted + affected files and known platform-only exclusions.
- [ ] Frozen Master guard.
- [ ] Evidence / exact-head review / Git lifecycle / main verify / governance sync.

NEXT_EXACT_ACTION = "RUN BROADER VALID WINDOWS REGRESSION -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD"


## IMP-062 BROADER VALID WINDOWS REGRESSION RUNNING - 2026-10-08

- [x] Targeted 7/7 PASS.
- [x] Affected authority regression 89/89 PASS.
- [~] Broader valid Windows regression RUNNING under PTY `pty_6a22c39de77c2170502480d3b8e4d38218ac`, PID `43308`; targeted + affected files excluded.
- [ ] Finalize `.tmp/imp062-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard -> evidence/review/Git lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-062 BROADER PASS / FROZEN GUARD NEXT - 2026-10-08

- [x] Targeted IMP-062 = 7/7 PASS.
- [x] Affected authority regression = 89/89 PASS.
- [x] Broader valid Windows regression = 687/687 PASS / 3 deselected (`.tmp/imp062-broader-valid.xml`, exit 0).
- [ ] Frozen Master guard.
- [ ] Exact-head static/import/diff/leakage review -> evidence/verify/Git lifecycle.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON CURRENT IMP-062 WORKTREE -> STATIC REVIEW -> EVIDENCE / SIDE-EFFECT GUARD"


## IMP-062 EXACT-HEAD REVIEW FIX / REVALIDATION - 2026-10-08

- [x] Exact-head review found policy wiring defect: `not_evaluated_requires_review` ignored.
- [x] Fix verdict aggregation to consume request policy; add policy=false targeted regression.
- [x] Post-fix py_compile/import/diff-check PASS.
- [!] Pre-fix targeted 7/7, affected 89/89, broader 687/687 are historical/stale for modified implementation.
- [ ] Rerun targeted IMP-062 only.
- [ ] If targeted PASS: rerun affected authority regression.
- [ ] If affected PASS: rerun broader valid Windows regression.
- [ ] Frozen guard -> evidence/review/Git lifecycle.

NEXT_EXACT_ACTION = "RUN POST-FIX TARGETED IMP-062 -> AFFECTED -> BROADER -> FROZEN GUARD"


## IMP-062 REVIEW-FIX TARGETED PASS / AFFECTED REVALIDATION NEXT - 2026-10-08

- [x] Review defect fixed: cross-boundary verdict honors `not_evaluated_requires_review` policy.
- [x] Post-fix static/import/diff gate PASS.
- [x] Post-fix targeted IMP-062 = 8/8 PASS (`.tmp/imp062-review-targeted.xml`, exit 0).
- [ ] Rerun affected authority regression on modified exact head.
- [ ] Rerun broader valid Windows regression.
- [ ] Frozen guard -> final evidence/review/Git lifecycle.

NEXT_EXACT_ACTION = "RUN POST-FIX AFFECTED AUTHORITY REGRESSION -> BROADER -> FROZEN GUARD"


## IMP-062 REVIEW-FIX AFFECTED REVALIDATION RUNNING - 2026-10-08

- [x] Post-fix targeted IMP-062 = 8/8 PASS.
- [~] Affected authority regression revalidation RUNNING under PTY `pty_cd1b515d9c6274d55426a4e762d68642c53e`, PID `66836`.
- [ ] Finalize `.tmp/imp062-review-affected.xml` from final JUnit/exit only.
- [ ] Broader revalidation -> Frozen guard -> evidence/Git lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> BROADER REVALIDATION IF PASS"


## IMP-062 REVIEW-FIX AFFECTED PASS / BROADER REVALIDATION NEXT - 2026-10-08

- [x] Post-fix targeted IMP-062 = 8/8 PASS.
- [x] Post-fix affected authority regression = 89/89 PASS (`.tmp/imp062-review-affected.xml`, exit 0).
- [ ] Rerun broader valid Windows regression on modified exact head.
- [ ] Frozen guard -> final static/review gates -> evidence/Git lifecycle.

NEXT_EXACT_ACTION = "RUN POST-FIX BROADER VALID WINDOWS REGRESSION -> FROZEN GUARD -> FINAL REVIEW/EVIDENCE"


## IMP-062 REVIEW-FIX BROADER REVALIDATION PASS / FROZEN GUARD NEXT - 2026-10-08

- [x] Post-fix targeted IMP-062 = 8/8 PASS.
- [x] Post-fix affected authority regression = 89/89 PASS.
- [x] Post-fix broader valid Windows regression = 687/687 PASS (`.tmp/imp062-broader-valid.xml`).
- [ ] Run Frozen Master guard on exact current head.
- [ ] Final static/review/evidence -> commit/PR/merge/main verification.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD -> FINAL REVIEW/EVIDENCE -> GIT LIFECYCLE"


## IMP-062 FROZEN MASTER GUARD PASS / FINAL REVIEW NEXT - 2026-10-08

- [x] Post-fix targeted IMP-062 = 8/8 PASS.
- [x] Post-fix affected authority regression = 89/89 PASS.
- [x] Post-fix broader valid Windows regression = 687/687 PASS.
- [x] Frozen Master guard PASS (`1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`).
- [ ] Final static/import/diff/leakage review -> evidence -> Git lifecycle.

NEXT_EXACT_ACTION = "RUN FINAL STATIC/IMPORT/DIFF/LEAKAGE REVIEW -> EVIDENCE -> SIDE-EFFECT GUARD -> COMMIT/PR"


## IMP-062 FINAL REVIEW TARGETED PASS / AFFECTED REVALIDATION NEXT - 2026-10-08

- [x] Final-review static/diff gate PASS.
- [x] Final-review targeted IMP-062 = 9/9 PASS (`.tmp/imp062-final-review-targeted.xml`, exit 0).
- [ ] Revalidate affected authority regression on final-review exact head.
- [ ] Revalidate broader valid Windows regression.
- [ ] Frozen guard -> final evidence -> Git lifecycle.

NEXT_EXACT_ACTION = "RUN FINAL-REVIEW AFFECTED AUTHORITY REGRESSION -> BROADER -> FROZEN GUARD"


## IMP-062 FINAL REVIEW AFFECTED PASS / BROADER REVALIDATION NEXT - 2026-10-08

- [x] Final-review targeted IMP-062 = 9/9 PASS.
- [x] Final-review affected authority regression = 89/89 PASS (`.tmp/imp062-final-review-affected.xml`).
- [ ] Revalidate broader valid Windows regression on final-review exact head.
- [ ] Frozen guard -> final evidence -> Git lifecycle.

NEXT_EXACT_ACTION = "RUN FINAL-REVIEW BROADER VALID WINDOWS REGRESSION -> FROZEN GUARD -> FINAL EVIDENCE/GIT"


## IMP-062 FINAL REVIEW BROADER REVALIDATION RUNNING - 2026-10-08

- [x] Final-review targeted IMP-062 = 9/9 PASS.
- [x] Final-review affected authority regression = 89/89 PASS.
- [~] Final-review broader valid Windows regression RUNNING under PTY `pty_adf6814d27dd1a18c065fee42ea64390a1a2`, PID `72496`.
- [ ] Finalize `.tmp/imp062-final-review-broader.xml` from final JUnit/exit only.
- [ ] Frozen guard -> final evidence -> Git lifecycle.

NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-062 FINAL REVIEW BROADER PASS / FROZEN GUARD NEXT - 2026-10-08

- [x] Final-review targeted IMP-062 = 9/9 PASS.
- [x] Final-review affected authority regression = 89/89 PASS.
- [x] Final-review broader valid Windows regression = 687/687 PASS, 3 deselected (`.tmp/imp062-final-review-broader.xml`, exit 0).
- [ ] Frozen Master guard -> final static/evidence -> Git lifecycle.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD -> FINAL STATIC/EVIDENCE -> SIDE-EFFECT GUARD/GIT"


## IMP-062 LOCAL VERIFIED / GIT NEXT - 2026-10-08

- [x] Final targeted = 9/9 PASS.
- [x] Final affected authority regression = 89/89 PASS.
- [x] Final broader valid Windows regression = 687/687 PASS, 3 deselected.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Final static/import/diff/leakage gate PASS.
- [x] Evidence written: `evidence/tests/IMP-062_CONTINUITY_SEQUENCE_QA_EVIDENCE.md`.
- [x] Side-effect guard PASS: no duplicate commit/remote branch/PR; `.tmp` untracked only.
- [ ] Exact-scope feature commit -> governance sync -> push/PR/CI/review/merge/main verify.

NEXT_EXACT_ACTION = "STAGE EXACT 7 IMP-062 FILES EXCLUDING .tmp -> VERIFY INDEX -> COMMIT FEATURE"


## IMP-062 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-08

- [x] Feature commit created: `6d4ce9a7abdb6289bad3a7c7e6f8e6fe8b1fd9d5` (`feat(studio): add continuity sequence qa gates`).
- [x] Feature commit contains exact 7-file verified scope; `.tmp` excluded.
- [ ] Governance-only state sync commit.
- [ ] Push / PR / CI / exact-head review / merge / main verification.

NEXT_EXACT_ACTION = "COMMIT GOVERNANCE-ONLY STATE SYNC WITH EXACT FEATURE SHA -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-062 POST-MERGE TARGETED RUNNING - 2026-10-08

- [x] PR #70 merged to main SHA `849b2c993ac1078e0ba162b2de5da369026d9d34`.
- [~] Post-merge targeted IMP-062 running under PTY `pty_ae8149f43ee65bdb6c34ca1084eb12a8e9f2`, PID `79080`.
- [~] Push-main CI run `37749047293` running on exact merge SHA.
- [ ] Finalize `.tmp/imp062-main-targeted.xml` from final JUnit/exit only.
- [ ] Main affected regression -> Frozen guard -> MAIN VERIFIED if push-main CI also PASS.

NEXT_EXACT_ACTION = "MONITOR EXISTING TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> MAIN AFFECTED REGRESSION IF PASS"


## IMP-062 POST-MERGE TARGETED PASS / AFFECTED NEXT - 2026-10-08

- [x] Post-merge targeted IMP-062 = 9/9 PASS (`.tmp/imp062-main-targeted.xml`, exit 0).
- [ ] Post-merge affected 8-file authority regression.
- [ ] Frozen Master guard + push-main CI SUCCESS -> feature MAIN VERIFIED.

NEXT_EXACT_ACTION = "RUN POST-MERGE AFFECTED 8-FILE AUTHORITY REGRESSION -> FROZEN GUARD"


## IMP-062 POST-MERGE AFFECTED RUNNING - 2026-10-08

- [x] Post-merge targeted IMP-062 = 9/9 PASS.
- [~] Post-merge affected 8-file authority regression RUNNING under PTY `pty_acbcee2095fdab51cfe2a9145e6a423fad51`, PID `70836`.
- [ ] Finalize `.tmp/imp062-main-affected.xml` from final JUnit/exit only.
- [ ] Frozen Master guard + push-main CI SUCCESS -> feature MAIN VERIFIED.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-062 PUSH-MAIN CI PASS / AFFECTED RUNNING - 2026-10-08

- [x] Push-main CI run `37749047293` SUCCESS on exact merge SHA; Python 3.10 + 3.13 PASS.
- [x] Post-merge targeted = 9/9 PASS.
- [~] Post-merge affected regression still RUNNING under PTY `pty_acbcee2095fdab51cfe2a9145e6a423fad51`, PID `70836`.
- [ ] Frozen Master guard -> feature MAIN VERIFIED after affected PASS.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-062 POST-MERGE AFFECTED PASS / FROZEN GUARD NEXT - 2026-10-08

- [x] Post-merge targeted IMP-062 = 9/9 PASS.
- [x] Post-merge affected authority regression = 89/89 PASS (`.tmp/imp062-main-affected.xml`, exit 0).
- [x] Push-main CI run `37749047293` SUCCESS on exact merge SHA.
- [ ] Frozen Master guard -> feature MAIN VERIFIED.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT MAIN SHA -> IF PASS MARK FEATURE MAIN VERIFIED"


## IMP-062 FEATURE MAIN VERIFIED / GOVERNANCE SYNC NEXT - 2026-10-08

- [x] PR #70 merged at main SHA `849b2c993ac1078e0ba162b2de5da369026d9d34`.
- [x] Post-merge targeted IMP-062 = 9/9 PASS.
- [x] Post-merge affected authority regression = 89/89 PASS.
- [x] Push-main CI run `37749047293` SUCCESS Python 3.10 + 3.13.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] IMP-062 feature = MAIN VERIFIED.
- [ ] Governance-only MAIN VERIFIED state sync lifecycle.

NEXT_EXACT_ACTION = "GOVERNANCE-ONLY MAIN VERIFIED SYNC -> SIDE-EFFECT GUARD -> BRANCH/COMMIT/PUSH/PR/CI/MERGE -> VERIFY GOVERNANCE MAIN"


## IMP-062 GOVERNANCE VERIFIED / IMP-063 CLAIMED - 2026-10-08

- [x] IMP-062 governance PR #71 merged to main SHA `7e9b30e0d2ab2785279642762feaefa3b2946a19`.
- [x] Governance push-main CI run `37752708366` SUCCESS; Python 3.10 + 3.13 PASS unit tests + Frozen Master guard.
- [x] IMP-063 hard dependencies verified: IMP-060 + IMP-061 + IMP-062 + IMP-005.
- [~] IMP-063 Defect Localization + Targeted Production Repair CLAIMED on `chatgpt/IMP-063-defect-localization-repair`.
- [ ] Read frozen authority/task decomposition and audit current QA/invalidation/repair surfaces.
- [ ] Implement stable defect localization + minimum-scope RepairPlan preserve/patch/invalidate/recheck contracts.
- [ ] Targeted/negative + affected + broader valid regression + Frozen guard -> evidence/Git lifecycle/main verify.

NEXT_EXACT_ACTION = "READ IMP-063 FROZEN AUTHORITY + TASK DECOMPOSITION -> AUDIT CURRENT QA/INVALIDATION/REPAIR SURFACES -> LOCK CONTRACT/TEST PLAN -> IMPLEMENT"


## IMP-063 TARGETED RUNNING - 2026-10-08

- [x] Frozen authority/task decomposition read; current QA/invalidation/story-repair donor surfaces audited.
- [x] Contract locked: evidence-backed earliest responsible layer; stable defect code/version; preserve/patch/invalidate/recheck; provider-neutral/no direct state commit.
- [x] `agent/studio/production_repair.py` implemented and public import/compile PASS.
- [x] `tests/unit/test_studio_production_repair.py` implemented with wrong-layer, preserve-set, mandatory re-QA, stale-QA and positive minimum-scope fixtures.
- [~] Targeted test RUNNING under PTY `pty_57d118ca0b7cf4ee6ae9263e1a860f01305f`, PID `85684`.
- [ ] Finalize `.tmp/imp063-targeted.xml` from final JUnit/exit only.
- [ ] Affected regression only after targeted PASS.

NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-063 TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FIX ONLY TARGETED FAILURES OR RUN AFFECTED IF PASS"


## IMP-063 TARGETED FAIL / FIXED - 2026-10-08

- [x] Targeted first run classified FAIL at collection; zero tests executed.
- [x] Exact root cause: new fixture used positional `VersionRef(...)`; Pydantic requires keyword arguments.
- [x] Fixed only fixture construction; production implementation untouched.
- [ ] Rerun only IMP-063 targeted under standard uv/Python 3.13 runner.

NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RERUN ONLY IMP-063 TARGETED TO `.tmp/imp063-targeted-rerun1.xml`"


## IMP-063 TARGETED RERUN1 RUNNING - 2026-10-08

- [~] Targeted rerun1 RUNNING under PTY `pty_94e351a324408ff3c3593a9b83b092138052`, PID `18176`.
- [ ] Final JUnit `.tmp/imp063-targeted-rerun1.xml` + PTY exit required before classification.

NEXT_EXACT_ACTION = "MONITOR EXISTING TARGETED RERUN1; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-063 TARGETED PASS - 2026-10-08

- [x] Targeted rerun1 final = 7/7 PASS; PTY exit 0; JUnit `.tmp/imp063-targeted-rerun1.xml` has 0 fail/error/skip.
- [x] Wrong-layer, schema layer identity, preserve-set, mandatory originating re-QA, minimum-scope positive path and stale-QA rejection covered.
- [ ] Run affected authority regression only; do not rerun targeted.

NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN AFFECTED AUTHORITY REGRESSION ONLY; DO NOT RERUN TARGETED"


## IMP-063 AFFECTED RUNNING - 2026-10-08

- [x] Targeted checkpoint remains 7/7 PASS and is not rerun.
- [~] Affected authority regression RUNNING under PTY `pty_f8d4e8ca99de6ca0bb1205e115fec3bed64d`, PID `83564`.
- [ ] Final JUnit `.tmp/imp063-affected.xml` + PTY exit required.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-063 AFFECTED PASS / BROADER NEXT - 2026-10-08

- [x] Targeted IMP-063 = 7/7 PASS; locked and must not rerun.
- [x] Affected authority regression = 55/55 PASS (`.tmp/imp063-affected.xml`; 0 fail/error/skip).
- [ ] Broader valid Windows regression excluding IMP-063 targeted + affected files.
- [ ] Frozen Master guard -> final static/import/diff/leakage review -> evidence/Git lifecycle/main verify.

NEXT_EXACT_ACTION = "DERIVE PRIOR BROADER VALID WINDOWS COMMAND -> ANTI-DUPLICATE GUARD -> RUN BROADER REGRESSION EXCLUDING TARGETED+AFFECTED -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD"


## IMP-063 BROADER VALID WINDOWS RUNNING - 2026-10-08

- [x] Targeted IMP-063 = 7/7 PASS; excluded from broader run.
- [x] Affected authority regression = 55/55 PASS; excluded from broader run.
- [~] Broader valid Windows regression RUNNING under PTY `pty_25e864daa1be0743ea7f47e6a211d1dad377`, PID `84456`.
- [ ] Finalize `.tmp/imp063-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard -> final static/import/diff/leakage review -> evidence/Git lifecycle/main verify.

NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-063 BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-063 BROADER VALID WINDOWS PASS / FROZEN GUARD NEXT - 2026-10-08

- [x] IMP-063 targeted rerun1 = 7/7 PASS.
- [x] Affected authority regression = 55/55 PASS.
- [x] Broader valid Windows regression = 730/730 PASS (`.tmp/imp063-broader-valid.xml`; 0 fail/error/skip).
- [ ] Frozen Master guard on exact IMP-063 head.
- [ ] Final static/import/diff/leakage review -> evidence/Git lifecycle/main verify.

NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT IMP-063 HEAD -> FINAL STATIC/IMPORT/DIFF REVIEW -> EVIDENCE/GIT LIFECYCLE"


## IMP-063 FROZEN MASTER GUARD PASS / FINAL REVIEW NEXT - 2026-10-08

- [x] Targeted = 7/7 PASS.
- [x] Affected authority regression = 55/55 PASS.
- [x] Broader valid Windows regression = 730/730 PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Final static/import/diff/leakage review -> evidence -> side-effect guard -> Git lifecycle.

NEXT_EXACT_ACTION = "RUN FINAL STATIC/IMPORT/DIFF/LEAKAGE REVIEW -> CREATE EVIDENCE -> SIDE-EFFECT GUARD -> COMMIT/PUSH/PR"


## IMP-063 FINAL REVIEW FIX / REVALIDATION - 2026-10-08

- [x] Frozen §78-79 review found provenance-version evidence gap before commit.
- [x] Patch: auto-pin defect-registry + detector or repair-planner version markers in provenance; reject missing markers.
- [x] Targeted tests extended to assert persisted markers and fail closed on manual provenance without them.
- [ ] Post-review targeted exact head.
- [ ] Affected authority regression only after targeted PASS.
- [ ] Broader valid Windows + Frozen guard only after affected PASS.

NEXT_EXACT_ACTION = "POST-REVIEW STATIC GATE -> TARGETED ONLY -> AFFECTED IF PASS -> BROADER VALID -> FROZEN GUARD"


## IMP-063 POST-REVIEW TARGETED PASS / AFFECTED NEXT - 2026-10-08

- [x] Review-fix static/import/leakage gate PASS.
- [x] Exact review head targeted = 8/8 PASS (`.tmp/imp063-final-targeted.xml`, exit 0).
- [ ] Affected authority regression only; targeted must not rerun.
- [ ] Broader valid Windows only after affected PASS.
- [ ] Frozen guard + final evidence/Git lifecycle after broader PASS.

NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN IMP-063 AFFECTED AUTHORITY REGRESSION ONLY; DO NOT RERUN TARGETED"


## IMP-063 POST-REVIEW AFFECTED RUNNING - 2026-10-08

- [x] Post-review targeted exact head = 8/8 PASS; excluded from affected.
- [~] Affected authority regression RUNNING under PTY `pty_98da4510d8d9b84203ca3afbf352d27d32e0`, PID `74388`.
- [ ] Finalize `.tmp/imp063-final-affected.xml` from final JUnit/exit only.
- [ ] Broader valid Windows only after affected PASS.

NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-063 POST-REVIEW AFFECTED PASS / BROADER NEXT - 2026-10-08
- [x] Exact review targeted = 8/8 PASS.
- [x] Exact review affected authority regression = 55/55 PASS.
- [ ] Broader valid Windows regression excluding targeted+affected.
- [ ] Frozen Master guard after broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS EXCLUDING TARGETED+AFFECTED -> FROZEN GUARD IF PASS"


## IMP-063 FINAL BROADER REVALIDATION RUNNING - 2026-10-08
- [x] Post-review targeted = 8/8 PASS.
- [x] Post-review affected = 55/55 PASS.
- [~] Broader valid Windows exact review head RUNNING under PTY `pty_771f797281354318cb7c04ae16f3202e9965`, PID `84416`.
- [ ] Final JUnit `.tmp/imp063-final-broader-valid.xml` + PTY exit required.
- [ ] Frozen guard after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-063 FINAL BROADER REVALIDATION PASS / FROZEN NEXT - 2026-10-08
- [x] Post-review targeted exact head = 8/8 PASS.
- [x] Post-review affected authority regression = 55/55 PASS.
- [x] Broader valid Windows exact review head = 730/730 PASS; 3 deselected; PTY exit 0.
- [ ] Frozen Master guard on exact review head.
- [ ] Final evidence / side-effect guard / Git lifecycle after Frozen PASS.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/BROADER"


## IMP-063 FROZEN MASTER GUARD PASS / FINAL REVIEW NEXT - 2026-10-08
- [x] Post-review targeted = 8/8 PASS.
- [x] Post-review affected = 55/55 PASS.
- [x] Post-review broader valid Windows = 730/730 PASS; 3 deselected.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Final static/import/diff/leakage review.
- [ ] Evidence + side-effect guard + Git lifecycle.
NEXT_EXACT_ACTION = "FINAL STATIC/IMPORT/DIFF/LEAKAGE REVIEW -> EVIDENCE -> SIDE-EFFECT GUARD -> COMMIT"


## IMP-063 FINAL REVIEW FIX 2 / REVALIDATION - 2026-10-08
- [x] Frozen §78 review found connected downstream manifestation could still be selected as responsible layer.
- [x] Patch: responsible_ref must be a cited finding source or exact ancestor of one.
- [x] Added negative test for connected-but-too-late FullShotSpec localization.
- [x] Post-fix static/import/diff/leakage gate PASS.
- [ ] Rerun only IMP-063 targeted exact head.
- [ ] Affected only after targeted PASS.
- [ ] Broader valid Windows + Frozen guard only after affected PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN IMP-063 TARGETED EXACT HEAD ONLY -> IF PASS AFFECTED -> BROADER VALID -> FROZEN GUARD"


## IMP-063 FINAL REVIEW FIX 2 TARGETED PASS / AFFECTED NEXT - 2026-10-08
- [x] Post-fix static/import/diff/leakage gate PASS.
- [x] Composite targeted exact head = 9/9 PASS (8 PASS in full run + corrected failed case rerun 1/1 PASS).
- [ ] Run affected authority regression only; targeted must not rerun.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN IMP-063 AFFECTED AUTHORITY REGRESSION ONLY"


## IMP-063 FINAL REVIEW FIX 2 AFFECTED PASS / BROADER NEXT - 2026-10-08
- [x] Post-fix targeted exact head = composite 9/9 PASS.
- [x] Post-fix affected authority regression = 55/55 PASS (`.tmp/imp063-final2-affected.xml`).
- [ ] Run broader valid Windows exact head excluding targeted+affected; do not rerun either PASS stage.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS EXACT HEAD EXCLUDING TARGETED+AFFECTED -> FROZEN MASTER GUARD IF PASS"


## IMP-063 FINAL REVIEW FIX 2 BROADER RUNNING - 2026-10-08
- [x] Post-fix targeted exact head = composite 9/9 PASS.
- [x] Post-fix affected authority regression = 55/55 PASS.
- [~] Broader valid Windows exact head RUNNING under PTY `pty_113b2fa5b62b63c89204d9653ffd6479f34b`, PID `79884`.
- [ ] Finalize `.tmp/imp063-final2-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-063 FINAL REVIEW FIX 2 BROADER INTERRUPTED / RESUME - 2026-10-09
- [x] Post-fix targeted exact head = composite 9/9 PASS; DO NOT rerun.
- [x] Post-fix affected authority regression = 55/55 PASS; DO NOT rerun.
- [!] Prior broader PTY/PID disappeared after FileMCP workspace restart with no final JUnit/result marker: classify INTERRUPTED, not PASS/FAIL.
- [ ] Resume only broader valid Windows stage using proven exclusion envelope and new JUnit/basetemp.
- [ ] Frozen Master guard only after resumed broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RESUME ONLY BROADER VALID WINDOWS STAGE -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-063 FINAL REVIEW FIX 2 BROADER RESUME1 RUNNING - 2026-10-09
- [x] Post-fix targeted exact head = composite 9/9 PASS; excluded.
- [x] Post-fix affected authority regression = 55/55 PASS; excluded.
- [~] Resumed broader valid Windows stage RUNNING under PTY `pty_c911544d958047bcf754e8d9f4d935f0fb9e`, PID `77848` after prior broader interruption.
- [ ] Finalize `.tmp/imp063-final2-broader-resume1.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after resumed broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING RESUME1 BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-063 FINAL REVIEW FIX 2 BROADER RESUME1 PASS / FROZEN NEXT - 2026-10-09
- [x] Post-fix targeted exact head = composite 9/9 PASS; DO NOT rerun.
- [x] Post-fix affected authority regression = 55/55 PASS; DO NOT rerun.
- [x] Resumed broader valid Windows exact head = 730/730 PASS; failures=0 errors=0 skipped=0.
- [ ] Run Frozen Master guard on exact current head.
- [ ] Final static/evidence/side-effect Git lifecycle only after Frozen PASS.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/BROADER"


## IMP-063 FINAL REVIEW FIX 2 FROZEN MASTER GUARD PASS / FINAL REVIEW NEXT - 2026-10-09
- [x] Targeted exact head = composite 9/9 PASS; DO NOT rerun.
- [x] Affected authority regression = 55/55 PASS; DO NOT rerun.
- [x] Broader valid Windows exact head = 730/730 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Final static/import/diff/leakage review.
- [ ] Evidence + side-effect guard + Git lifecycle.
NEXT_EXACT_ACTION = "FINAL STATIC/IMPORT/DIFF/LEAKAGE REVIEW -> EVIDENCE -> SIDE-EFFECT GUARD -> COMMIT"


## IMP-063 LOCAL VERIFIED / COMMIT NEXT - 2026-10-09
- [x] Targeted exact head = composite 9/9 PASS.
- [x] Affected authority regression = 55/55 PASS.
- [x] Broader valid Windows exact head = 730/730 PASS.
- [x] Frozen Master guard PASS.
- [x] Final static/import/diff/leakage gate PASS.
- [x] Evidence written: `evidence/tests/IMP-063_DEFECT_LOCALIZATION_REPAIR_EVIDENCE.md`.
- [x] Side-effect guard PASS: no duplicate commit/remote branch/PR; `.tmp` untracked only.
- [ ] Stage exact 7 files -> verify index -> feature commit.
NEXT_EXACT_ACTION = "STAGE EXACT 7 FILES -> VERIFY INDEX/DIFF-CHECK -> COMMIT FEATURE"


## IMP-063 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-09
- [x] Feature commit created: `c6d7e5455d01f5c77765640c9e9f0d64e8bba01b`.
- [x] Feature commit scope = exact 7 IMP-063 files.
- [x] Worktree after feature commit = `.tmp/` untracked only.
- [ ] Stage only `CURRENT_HANDOFF.md`, `PROJECT_STATE.md`, `tasks/TASK_QUEUE.md`.
- [ ] Governance-only sync commit.
- [ ] Side-effect guard -> push branch -> PR.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> GOVERNANCE SYNC COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-063 POST-MERGE TARGETED RUNNING - 2026-10-09
- [x] PR #72 merged at `d8899957372d9765be4391ee77af9c293192e79f`.
- [~] Post-merge targeted RUNNING under PTY `pty_25536e856e98d610dfadf8ba1482494b8903`, PID `82352`.
- [~] Push-main CI run `37877711999` RUNNING on exact merge SHA.
- [ ] Finalize `.tmp/imp063-main-targeted.xml` from final JUnit/exit only.
- [ ] Affected authority regression only after targeted PASS.
- [ ] Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-063 POST-MERGE TARGETED PASS / AFFECTED NEXT - 2026-10-09
- [x] Post-merge targeted exact main SHA = 9/9 PASS; DO NOT rerun.
- [ ] Run affected authority regression only: versioning + invalidation + story_quality + static_qa + motion_qa + continuity_sequence_qa.
- [ ] Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN 6-FILE AFFECTED AUTHORITY REGRESSION; TARGETED MUST NOT RERUN"


## IMP-063 POST-MERGE AFFECTED RUNNING - 2026-10-09
- [x] Post-merge targeted = 9/9 PASS; excluded.
- [~] Affected authority regression RUNNING under PTY `pty_c7cef733b1ad96a2cb85fd5696afa0adb1de`, PID `89448`.
- [ ] Finalize `.tmp/imp063-main-affected.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-063 PUSH-MAIN CI PASS / AFFECTED STILL RUNNING - 2026-10-09
- [x] Push-main CI run `37877711999` SUCCESS on exact merge SHA; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Post-merge targeted = 9/9 PASS.
- [~] Existing affected PTY `pty_c7cef733b1ad96a2cb85fd5696afa0adb1de` still owns current stage; DO NOT restart.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-063 POST-MERGE AFFECTED PASS / FROZEN NEXT - 2026-10-09
- [x] Post-merge targeted = 9/9 PASS; DO NOT rerun.
- [x] Post-merge affected authority regression = 55/55 PASS; DO NOT rerun.
- [x] Push-main CI run `37877711999` = SUCCESS on exact merge SHA.
- [ ] Run Frozen Master guard on exact main SHA.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/CI"


## IMP-063 FEATURE MAIN VERIFIED / GOVERNANCE SYNC NEXT - 2026-10-09
- [x] PR #72 merged at `d8899957372d9765be4391ee77af9c293192e79f`.
- [x] Post-merge targeted = 9/9 PASS.
- [x] Post-merge affected authority regression = 55/55 PASS.
- [x] Push-main CI run `37877711999` = SUCCESS.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Governance-only sync branch/commit/PR/CI/merge/verify main.
NEXT_EXACT_ACTION = "CREATE GOVERNANCE-ONLY BRANCH FROM EXACT MAIN -> COMMIT 3 STATE FILES -> PUSH/PR/CI/MERGE/VERIFY MAIN"


## IMP-063 GOVERNANCE MAIN VERIFIED / IMP-064 CLAIMED - 2026-10-09
- [x] IMP-063 governance PR #73 merged at `83303da08c89106dc45d9d3addc92db23e787724`.
- [x] Governance push-main CI run `37880708072` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Verify IMP-064 dependencies: IMP-063 + IMP-042 MAIN VERIFIED.
- [x] Duplicate guard PASS for `chatgpt/IMP-064-approval-state-commit`.
- [x] Claim branch from exact main `83303da08c89106dc45d9d3addc92db23e787724`.
- [ ] Read Frozen approval / canonical State commit authority.
- [ ] Audit current QA approval, ApprovedEndState, repair/invalidation and state propagation surfaces.
- [ ] Implement explicit approval/state-commit boundary.
- [ ] Tests: NO QA APPROVAL -> NO STATE COMMIT; stale candidate approval rejected; designation references exact StateSnapshot.
NEXT_EXACT_ACTION = "READ FROZEN APPROVAL/CANONICAL STATE COMMIT AUTHORITY + AUDIT STATE/QA/REPAIR SURFACES BEFORE CODE"


## IMP-064 AUTHORITY + SURFACE AUDIT PASS - 2026-10-09
- [x] Frozen Master creative acceptance + Approval/State Commit authority read.
- [x] Audit GenerationJob creative axis, Static/Motion QA typed results, StateSnapshotRepository, ApprovedEndState, repair/invalidation surfaces.
- [x] KEEP+EXTEND: existing StateSnapshotRepository remains sole canonical State commit owner.
- [x] Lock new thin `ApprovalStateCommitService`: exact GenerationJob creative APPROVED/LOCKED + exact current typed QA COMPLETED/PASS + current approval policy/source outcome + snapshot CAS -> delegate State commit.
- [x] No duplicate State store / no copied state payload / no provider call in transaction.
- [ ] Implement service + exports + targeted tests.
- [ ] Targeted -> affected -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "IMPLEMENT APPROVAL_STATE_COMMIT SERVICE + EXPORTS + TARGETED TESTS -> STATIC GATE -> TARGETED ONLY"


## IMP-064 TARGETED RUNNING - 2026-10-09
- [x] Authority/surface audit PASS; contract frozen before code.
- [x] Implement thin ApprovalStateCommitService + Static/Motion QA identity bridge + public exports.
- [x] Static/import/diff gate PASS.
- [~] Targeted tests RUNNING under PTY `pty_f540a7cf729496ee0321a7b05267809d5a7b`, PID `25464`.
- [ ] Finalize `.tmp/imp064-targeted.xml` from final JUnit/exit only.
- [ ] Affected regression only after targeted PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 TARGETED PASS / REVIEW NEXT - 2026-10-09
- [x] Static/import gate PASS.
- [x] Targeted approval/state-commit tests = 5/5 PASS; JUnit `.tmp/imp064-targeted.xml`; PTY exit 0.
- [ ] Exact-head authority review; targeted must not rerun unless code changes.
- [ ] Affected authority regression after review PASS.
NEXT_EXACT_ACTION = "EXACT-HEAD AUTHORITY REVIEW -> AFFECTED AUTHORITY REGRESSION IF NO CODE CHANGE"


## IMP-064 HUMAN-APPROVAL REVIEW FIX TARGETED RUNNING - 2026-10-09
- [x] Exact-head review found valid HUMAN_APPROVE path blocked by QA lifecycle REVIEW.
- [x] Patch: typed PASS + creative APPROVED may CAS-promote exact current QA REVIEW -> APPROVED before State commit.
- [x] Added human-approval targeted case; post-fix static/import gate PASS.
- [~] Exact-head targeted RUNNING under PTY `pty_efeec3c4be017d1421e1554cd08cceef185b`, PID `90044`.
- [ ] Affected regression only after targeted PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING REVIEW TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 HUMAN-APPROVAL REVIEW FIX TARGETED PASS / AFFECTED NEXT - 2026-10-09
- [x] Human-approval review fix implemented and static/import gate PASS.
- [x] Exact-head targeted = 6/6 PASS; JUnit `.tmp/imp064-review-targeted.xml`; PTY exit 0.
- [ ] Run affected authority regression only; targeted must not rerun.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN 6-FILE AFFECTED AUTHORITY REGRESSION; TARGETED MUST NOT RERUN"


## IMP-064 AFFECTED AUTHORITY REGRESSION RUNNING - 2026-10-09
- [x] Exact-head targeted = 6/6 PASS; excluded from affected stage.
- [~] 6-file affected authority regression RUNNING under PTY `pty_2ecc7d2799413965bb9493ec787a228015b1`, PID `2000`.
- [ ] Finalize `.tmp/imp064-affected.xml` from final JUnit/exit only.
- [ ] Broader valid Windows only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 AFFECTED AUTHORITY REGRESSION PASS / BROADER NEXT - 2026-10-09
- [x] Exact-head targeted = 6/6 PASS; DO NOT rerun.
- [x] Affected authority regression = 69/69 PASS; `.tmp/imp064-affected.xml`; DO NOT rerun.
- [ ] Run broader valid Windows regression excluding targeted + affected authority files and known platform exclusions.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS REGRESSION; TARGETED/AFFECTED MUST NOT RERUN"


## IMP-064 BROADER VALID WINDOWS RUNNING - 2026-10-09
- [x] Targeted exact head = 6/6 PASS; excluded.
- [x] Affected authority regression = 69/69 PASS; excluded.
- [~] Broader valid Windows RUNNING under PTY `pty_4ca4854018b702c18205a3b0341a856392dc`, PID `82176`.
- [ ] Finalize `.tmp/imp064-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-064 BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-064 BROADER VALID WINDOWS PASS / EXACT-HEAD REVIEW - 2026-10-09
- [x] Exact-head targeted = 6/6 PASS; DO NOT rerun.
- [x] Affected authority regression = 69/69 PASS; DO NOT rerun.
- [x] Broader valid Windows regression = 725/725 PASS; 3 deselected; `.tmp/imp064-broader-valid.xml`; PTY exit 0; DO NOT rerun.
- [ ] Complete exact-head authority/transaction review.
- [ ] If code unchanged, run Frozen Master guard; if defect confirmed, fix only IMP-064 and revalidate changed head.
NEXT_EXACT_ACTION = "COMPLETE EXACT-HEAD AUTHORITY/TRANSACTION REVIEW -> FROZEN GUARD IF UNCHANGED; OTHERWISE FIX/REVALIDATE CHANGED HEAD"


## IMP-064 INTERRUPTED AUTO-APPROVAL REVIEW FIX TARGETED RUNNING - 2026-10-09
- [x] Exact-head review found REVIEW QA promotion could mask interrupted `QA_PASS_AND_AUTO_APPROVE` finalize.
- [x] Patch requires durable latest creative approval command `HUMAN_APPROVE` before State Commit promotes REVIEW QA.
- [x] Added regression test for auto-approval crash window; static/import/diff gate PASS.
- [~] Exact-head targeted revalidation RUNNING under PTY `pty_65ec7e16057dec5e1896188109431cb286a8`, PID `92876`.
- [ ] Affected authority regression only after targeted PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING FINAL-REVIEW TARGETED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 INTERRUPTED AUTO-APPROVAL REVIEW FIX TARGETED PASS / AFFECTED NEXT - 2026-10-09
- [x] Transition-history hardening implemented; regression test added.
- [x] Exact-head targeted = 7/7 PASS; `.tmp/imp064-final-review-targeted.xml`; PTY exit 0.
- [ ] Run 6-file affected authority regression only; targeted MUST NOT rerun.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN 6-FILE AFFECTED AUTHORITY REGRESSION; TARGETED MUST NOT RERUN"


## IMP-064 FINAL-REVIEW AFFECTED AUTHORITY REGRESSION RUNNING - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS; excluded from affected stage.
- [~] 6-file affected authority regression RUNNING under PTY `pty_a483a4b59bef9cb8aeebb51a5b2ce76ffc9d`, PID `94568`.
- [ ] Finalize `.tmp/imp064-final-review-affected.xml` from final JUnit/exit only.
- [ ] Broader valid Windows only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING FINAL-REVIEW AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 FINAL-REVIEW AFFECTED PASS / BROADER REVALIDATION NEXT - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS; DO NOT rerun.
- [x] Final-review affected authority regression = 69/69 PASS; `.tmp/imp064-final-review-affected.xml`; DO NOT rerun.
- [ ] Run broader valid Windows regression on current review head excluding targeted + 6 affected authority files and known platform exclusions.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS REGRESSION ON CURRENT REVIEW HEAD; TARGETED/AFFECTED MUST NOT RERUN"


## IMP-064 FINAL-REVIEW BROADER VALID WINDOWS RUNNING - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS; excluded.
- [x] Final-review affected = 69/69 PASS; excluded.
- [~] Broader valid Windows revalidation RUNNING under PTY `pty_a2773b32a6dbf9af50c2981a45a5c69cc468`, PID `54484`.
- [ ] Finalize `.tmp/imp064-final-review-broader.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING FINAL-REVIEW BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN MASTER GUARD IF PASS"


## IMP-064 FINAL-REVIEW BROADER PASS / FROZEN NEXT - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS; DO NOT rerun.
- [x] Final-review affected authority regression = 69/69 PASS; DO NOT rerun.
- [x] Final-review broader valid Windows regression = 725/725 PASS; 3 deselected; PTY exit 0; DO NOT rerun.
- [ ] Run Frozen Master guard on current review head.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; TARGETED/AFFECTED/BROADER MUST NOT RERUN"


## IMP-064 FINAL-REVIEW FROZEN MASTER GUARD PASS - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS; DO NOT rerun.
- [x] Final-review affected authority regression = 69/69 PASS; DO NOT rerun.
- [x] Final-review broader valid Windows regression = 725/725 PASS; 3 deselected; DO NOT rerun.
- [x] Frozen Master guard = PASS; semantic SHA256 `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Run final static/import/diff gate + exact-head authority/transaction review.
NEXT_EXACT_ACTION = "RUN FINAL STATIC/IMPORT/DIFF GATE + EXACT-HEAD AUTHORITY/TRANSACTION REVIEW; TARGETED/AFFECTED/BROADER MUST NOT RERUN"


## IMP-064 LOCAL VERIFIED / SIDE-EFFECT GUARD NEXT - 2026-10-09
- [x] Exact-head targeted = 7/7 PASS.
- [x] Final-review affected authority regression = 69/69 PASS.
- [x] Final-review broader valid Windows regression = 725/725 PASS; 3 deselected.
- [x] Frozen Master guard PASS; final static/import/diff + exact-head authority review PASS.
- [x] Evidence file: `evidence/tests/IMP-064_APPROVAL_STATE_COMMIT_EVIDENCE.md`.
- [ ] Git side-effect guard -> exact-scope stage/commit/push/PR lifecycle.
NEXT_EXACT_ACTION = "RUN GIT SIDE-EFFECT GUARD -> STAGE EXACT IMP-064 SCOPE ONLY -> VERIFY INDEX -> COMMIT; DO NOT RERUN TEST STAGES"


## IMP-064 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-09
- [x] Local verification complete; evidence committed in feature snapshot.
- [x] Feature commit = `6f29c6c32e7baea3890e9b379f74a44d5b6ef25e`.
- [ ] Stage only `CURRENT_HANDOFF.md`, `PROJECT_STATE.md`, `tasks/TASK_QUEUE.md`.
- [ ] Commit governance sync, then side-effect guard before push/PR.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> VERIFY INDEX -> COMMIT GOVERNANCE SYNC -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-064 POST-MERGE TARGETED PASS / AFFECTED NEXT - 2026-10-09
- [x] PR #74 merged to exact main SHA `259d0f48a7d80d042eb62a971e3308991f341547`.
- [x] Push-main CI run `37924356391` SUCCESS; Python 3.10 + 3.13 PASS.
- [x] Post-merge targeted = 7/7 PASS; `.tmp/imp064-main-targeted.xml`; PTY exit 0; DO NOT rerun.
- [ ] Run 6-file post-merge affected authority regression only.
- [ ] Run Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN 6-FILE POST-MERGE AFFECTED AUTHORITY REGRESSION; TARGETED MUST NOT RERUN"


## IMP-064 POST-MERGE AFFECTED RUNNING - 2026-10-09
- [x] Post-merge targeted = 7/7 PASS; DO NOT rerun.
- [x] Push-main CI run `37924356391` SUCCESS on exact merge SHA.
- [~] 6-file post-merge affected authority regression RUNNING under PTY `pty_2149bba73a9f7d94a7c9f9dc68ce3567e6b6`, root PID `91476`.
- [ ] Finalize `.tmp/imp064-main-affected.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING POST-MERGE AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT"


## IMP-064 POST-MERGE AFFECTED PASS / FROZEN NEXT - 2026-10-09
- [x] Push-main CI run `37924356391` SUCCESS on exact main SHA `259d0f48a7d80d042eb62a971e3308991f341547`.
- [x] Post-merge targeted = 7/7 PASS; DO NOT rerun.
- [x] Post-merge affected authority regression = 69/69 PASS; `.tmp/imp064-main-affected.xml`; failures=0 errors=0 skipped=0; recorded PID `91476` absent after completion; DO NOT rerun.
- [ ] Run Frozen Master guard on exact main SHA.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; TARGETED/AFFECTED/CI MUST NOT RERUN"


## IMP-064 FEATURE MAIN VERIFIED / GOVERNANCE SYNC NEXT - 2026-10-09
- [x] PR #74 merged to exact main SHA `259d0f48a7d80d042eb62a971e3308991f341547`.
- [x] Push-main CI run `37924356391` SUCCESS; Python 3.10 + 3.13 PASS.
- [x] Post-merge targeted = 7/7 PASS; DO NOT rerun.
- [x] Post-merge affected = 69/69 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA256 `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Governance-only state sync lifecycle.
NEXT_EXACT_ACTION = "GOVERNANCE SIDE-EFFECT GUARD -> STATE-ONLY BRANCH/COMMIT -> PUSH/PR/CI/REVIEW/MERGE"


## IMP-064 GOVERNANCE MAIN VERIFIED / IMP-070 CLAIMED - 2026-10-09
- [x] IMP-064 governance PR #75 merged at `39ad22e016ed8e4ad977679989401020183eb459`.
- [x] Governance push-main CI run `37960919678` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Verify IMP-070 dependencies: IMP-003 + IMP-006 MAIN VERIFIED.
- [x] Duplicate guard PASS for `chatgpt/IMP-070-electron-host-shell-security`.
- [x] Claim branch from exact governance main `39ad22e016ed8e4ad977679989401020183eb459`.
- [ ] Read Frozen Electron Host Shell Security authority.
- [ ] Audit current Electron main/preload/packaging/security surfaces.
- [ ] Freeze KEEP+EXTEND implementation contract before code.
- [ ] Implement config/static security tests + navigation/new-window denial.
NEXT_EXACT_ACTION = "READ FROZEN ELECTRON HOST SHELL SECURITY AUTHORITY + AUDIT CURRENT ELECTRON/MAIN/PRELOAD/PACKAGING SURFACES BEFORE CODE"


## IMP-070 AUTHORITY + SURFACE AUDIT PASS - 2026-10-09
- [x] Read Frozen Master Security §84 authority.
- [x] Confirm Electron host is NEW target layer; current React/Vite + FastAPI runtime is not Electron evidence.
- [x] Audit tracked Electron/main/preload/package surfaces: production target absent; V0.16 spike is donor-only.
- [x] Lock KEEP+EXTEND boundary: existing dashboard/service authority unchanged.
- [x] Lock NEW `desktop/` shell with hardened BrowserWindow flags, custom `flowkit://app`, deny cross-origin navigation/new-window/webview.
- [x] Lock IMP-070 preload to no generic ipcRenderer/fs/child_process/shell bridge; IMP-071 owns typed IPC.
- [x] Supply-chain check: Electron 44.7.0 MIT; electron-builder 26.15.3 MIT.
- [ ] Implement shell/preload/security policy/package skeleton.
- [ ] Targeted static/behavior tests -> affected regression -> broader valid regression -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "IMPLEMENT DESKTOP HOST SHELL + PRELOAD + SECURITY POLICY/PACKAGING SKELETON + TARGETED TESTS"


## IMP-070 TARGETED SECURITY TESTS PASS - 2026-10-10
- [x] Node security-policy behavior tests = 3/3 PASS.
- [x] Python static/security targeted tests = 6/6 PASS; `.tmp/imp070-targeted.xml`.
- [ ] Run affected service-boundary regression only; targeted MUST NOT rerun.
- [ ] Run broader valid Windows regression after affected PASS.
- [ ] Run Frozen Master guard after broader PASS.
NEXT_EXACT_ACTION = "RUN AFFECTED SERVICE-BOUNDARY REGRESSION ONLY; TARGETED MUST NOT RERUN"


## IMP-070 AFFECTED SERVICE-BOUNDARY REGRESSION PASS - 2026-10-10
- [x] Targeted security: Node 3/3 PASS + pytest 6/6 PASS; DO NOT rerun.
- [x] Affected service-boundary regression: `test_flow_project_session.py` + `test_flow_upload_api.py` = 9/9 PASS; `.tmp/imp070-affected.xml`.
- [ ] Run broader valid Windows regression excluding targeted + affected files and known Windows/POSIX exclusions.
- [ ] Run Frozen Master guard after broader PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS REGRESSION; TARGETED/AFFECTED MUST NOT RERUN"


## IMP-070 BROADER VALID WINDOWS RUNNING - 2026-10-10
- [x] Targeted security gate PASS; DO NOT rerun.
- [x] Affected service-boundary regression 9/9 PASS; DO NOT rerun.
- [~] Broader valid Windows regression RUNNING under PTY `pty_4e16c0eb9b2dc88564bdb2aabe40afca534f`, PID `99208`.
- [ ] Finalize `.tmp/imp070-broader-valid.xml` from final JUnit/exit only.
- [ ] Run Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-070 BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-070 BROADER VALID WINDOWS PASS / FROZEN NEXT - 2026-10-10
- [x] Targeted security gate: Node 3/3 PASS + pytest 6/6 PASS; DO NOT rerun.
- [x] Affected service-boundary regression: 9/9 PASS; DO NOT rerun.
- [x] Broader valid Windows regression: 792/792 PASS; failures=0 errors=0 skipped=0; `.tmp/imp070-broader-valid.xml`; DO NOT rerun.
- [ ] Run Frozen Master guard on current IMP-070 worktree.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; TARGETED/AFFECTED/BROADER MUST NOT RERUN"


## IMP-070 LOCAL VERIFIED / GIT SIDE-EFFECT GUARD NEXT - 2026-10-10
- [x] Targeted security: Node 3/3 PASS + pytest 6/6 PASS; DO NOT rerun.
- [x] Affected service-boundary regression: 9/9 PASS; DO NOT rerun.
- [x] Broader valid Windows regression: 792/792 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Final static/security review PASS; evidence `evidence/tests/IMP-070_ELECTRON_HOST_SECURITY_EVIDENCE.md`.
- [ ] Git side-effect guard -> exact-scope stage/commit/push/PR lifecycle.
NEXT_EXACT_ACTION = "RUN GIT SIDE-EFFECT GUARD -> STAGE EXACT IMP-070 SCOPE ONLY -> VERIFY INDEX -> COMMIT; DO NOT RERUN TEST STAGES"


## IMP-070 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-10
- [x] Local verification complete; evidence committed in feature snapshot.
- [x] Feature commit = `6fdc06087bfa36d31dc1c9a600f4b5c391dd6b24`.
- [ ] Stage only `CURRENT_HANDOFF.md`, `PROJECT_STATE.md`, `tasks/TASK_QUEUE.md`.
- [ ] Commit governance sync, then side-effect guard before push/PR.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> VERIFY INDEX -> COMMIT GOVERNANCE SYNC -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-070 POST-MERGE TARGETED RUNNING - 2026-10-10
- [x] PR #76 merged at exact main SHA `f41a1b8d7409dc3f58e844f4c2f91eee226c37a4`.
- [~] Push-main CI run `38041456564` RUNNING on exact merge SHA.
- [~] Post-merge targeted security RUNNING under PTY `pty_9f34696ce8268570171ea648d20430410cb9`, PID `104824`.
- [ ] Finalize Node security + pytest targeted evidence without restart.
- [ ] Run affected service-boundary regression only after targeted PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING POST-MERGE TARGETED PTY; DO NOT RESTART -> FINAL RESULT -> AFFECTED ONLY IF PASS"


## IMP-070 POST-MERGE TARGETED PASS / AFFECTED NEXT - 2026-10-10
- [x] PR #76 merged at exact main SHA `f41a1b8d7409dc3f58e844f4c2f91eee226c37a4`.
- [x] Post-merge targeted security = Node 3/3 PASS + pytest 6/6 PASS; PTY exit 0; DO NOT rerun.
- [~] Push-main CI run `38041456564` RUNNING; Frozen baseline PASS both jobs.
- [ ] Run affected service-boundary regression only.
- [ ] Run Frozen Master guard after affected PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN POST-MERGE AFFECTED SERVICE-BOUNDARY REGRESSION ONLY; TARGETED MUST NOT RERUN"


## IMP-070 POST-MERGE AFFECTED RUNNING - 2026-10-10
- [x] Post-merge targeted = Node 3/3 + pytest 6/6 PASS; DO NOT rerun.
- [~] Post-merge affected service-boundary regression RUNNING under PTY `pty_27796d73d0ad986666e292e9733d0014cb66`, PID `104556`.
- [ ] Finalize `.tmp/imp070-main-affected.xml` from final JUnit/exit only.
- [ ] Run Frozen Master guard only after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING POST-MERGE AFFECTED PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-070 POST-MERGE AFFECTED PASS / FROZEN NEXT - 2026-10-10
- [x] Post-merge targeted = Node 3/3 + pytest 6/6 PASS; DO NOT rerun.
- [x] Post-merge affected service-boundary regression = 9/9 PASS; `.tmp/imp070-main-affected.xml`; DO NOT rerun.
- [~] Push-main CI run `38041456564`: Python 3.13 SUCCESS; Python 3.10 still RUNNING at checkpoint.
- [ ] Run Frozen Master guard on exact main SHA.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; TARGETED/AFFECTED MUST NOT RERUN; CONTINUE MONITORING EXISTING PUSH-MAIN CI"


## IMP-070 FEATURE MAIN VERIFIED / GOVERNANCE SYNC NEXT - 2026-10-10
- [x] PR #76 merged at exact main SHA `f41a1b8d7409dc3f58e844f4c2f91eee226c37a4`.
- [x] Push-main CI run `38041456564` SUCCESS; Python 3.10 + 3.13 PASS.
- [x] Post-merge targeted = Node 3/3 + pytest 6/6 PASS; DO NOT rerun.
- [x] Post-merge affected = 9/9 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Governance-only state sync lifecycle.
NEXT_EXACT_ACTION = "GOVERNANCE SIDE-EFFECT GUARD -> STATE-ONLY BRANCH/COMMIT -> PUSH/PR/CI/REVIEW/MERGE"


## IMP-070 GOVERNANCE MAIN VERIFIED / IMP-071 CLAIMED - 2026-10-10
- [x] IMP-070 governance PR #77 merged at `e21b5132cec0c92eff0e67c22ea4309d359091a2`.
- [x] Governance push-main CI run `38044348637` SUCCESS; Python 3.10 + 3.13 PASS; Frozen Master baseline PASS.
- [x] IMP-071 dependency `IMP-070` satisfied.
- [x] Duplicate guard: no prior IMP-071 commit/local branch/remote branch/PR before claim.
- [x] Claimed `chatgpt/IMP-071-typed-ipc-utility-bridge` from exact governance main.
- [ ] Read Frozen Master security authority for typed IPC / Production Utility Bridge.
- [ ] Audit current `desktop/` main/preload/renderer surfaces and donor spike; lock allowlisted channel/schema/sender/capability contract.
- [ ] Implement typed IPC/contextBridge without exposing raw ipcRenderer/fs/child_process.
- [ ] Negative tests: invalid sender/schema/channel denied; then affected/broader/Frozen guard/evidence/Git lifecycle.
NEXT_EXACT_ACTION = "READ FROZEN MASTER IMP-071 SECURITY AUTHORITY + AUDIT CURRENT DESKTOP MAIN/PRELOAD/RENDERER SURFACES -> LOCK TYPED IPC CONTRACT/ALLOWLIST/NEGATIVE TEST PLAN -> IMPLEMENT"


## IMP-071 AUTHORITY AUDIT LOCKED / CODE NEXT - 2026-10-10
- [x] Read Frozen Master target topology + §84 Security.
- [x] KEEP IMP-070 hardened BrowserWindow/custom protocol/navigation security unchanged.
- [x] Lock Renderer as low privilege; Main owns host/security boundary; Production Utility owns canonical runtime access.
- [x] Lock no generic channel-invoke bridge and no raw `ipcRenderer`/`fs`/`child_process`/`shell` exposure.
- [x] Lock exact sender/origin/main-frame validation + strict versioned request/response schema + redacted errors.
- [x] Lock typed Production Utility transport and narrow preload wrapper; future privileged capabilities require project/session authorization hook.
- [ ] Implement `ipc-contract.cjs`, main IPC handler, utility transport/entry, preload wrapper, package wiring.
- [ ] Targeted negative tests: invalid sender/schema/channel denial + no raw privilege exposure.
- [ ] Affected security regression -> broader valid regression -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "IMPLEMENT TYPED IPC CONTRACT/MAIN HANDLER/PRODUCTION UTILITY TRANSPORT/PRELOAD WRAPPER + TARGETED NODE TESTS; DO NOT REOPEN IMP-070"


## IMP-071 NODE TARGETED PASS / PYTHON STATIC GATE NEXT - 2026-10-10
- [x] Node targeted security + typed IPC suite: 12/12 PASS; DO NOT rerun unless code changes.
- [x] Invalid sender/origin/frame, schema/version, unknown channel, redacted errors, Utility round-trip and narrow preload surface covered.
- [x] npm bootstrap failure classified as harness-only before tests; direct `node --test` payload PASS.
- [ ] Run only `tests/unit/test_electron_host_security.py` in repo uv environment.
- [ ] If PASS, run affected service-boundary regression without rerunning targeted Node/Python files.
NEXT_EXACT_ACTION = "RUN ONLY PYTHON STATIC-SECURITY TARGETED FILE IN UV ENV; NODE TARGETED MUST NOT RERUN"


## IMP-071 TARGETED PASS / AFFECTED NEXT - 2026-10-10
- [x] Node typed IPC + security targeted = 12/12 PASS; DO NOT rerun unless code changes.
- [x] Python Electron static-security targeted = 7/7 PASS; `.tmp/imp071-targeted.xml`; DO NOT rerun unless code/test changes.
- [x] Exact sender/origin/frame, schema/version, unknown channel absence, redacted errors, Utility transport and bounded preload surface verified.
- [ ] Run affected service-boundary regression only: `tests/unit/test_flow_project_session.py` + `tests/unit/test_flow_upload_api.py`.
- [ ] Broader valid regression excluding targeted/affected -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN AFFECTED SERVICE-BOUNDARY REGRESSION ONLY; TARGETED MUST NOT RERUN"


## IMP-071 AFFECTED PASS / BROADER NEXT - 2026-10-10
- [x] Node targeted = 12/12 PASS; DO NOT rerun unless JS code changes.
- [x] Python Electron static-security targeted = 7/7 PASS; DO NOT rerun unless code/test changes.
- [x] Affected project/session + upload API regression = 9/9 PASS; `.tmp/imp071-affected.xml`; DO NOT rerun.
- [ ] Run broader valid Windows regression excluding targeted+affected + `test_setup.py` + `test_video_reviewer.py` + established 3 POSIX-path deselections.
- [ ] Frozen Master guard after broader PASS -> exact-head review/evidence/Git lifecycle.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS REGRESSION; TARGETED/AFFECTED MUST NOT RERUN"


## IMP-071 BROADER VALID WINDOWS RUNNING - 2026-10-10
- [x] Targeted Node 12/12 + Python 7/7 PASS; DO NOT rerun.
- [x] Affected service-boundary regression 9/9 PASS; DO NOT rerun.
- [~] Broader valid Windows regression RUNNING under PTY `pty_faec2ae1e4f7ba1e6c4df090d90cb1fbb84b`, PID `104796`.
- [x] Scope excludes IMP-071 targeted+affected, `test_setup.py`, `test_video_reviewer.py`; established 3 POSIX assertions deselected.
- [ ] Finalize `.tmp/imp071-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-071 BROADER PTY; DO NOT RESTART -> FINAL JUNIT/EXIT -> FROZEN GUARD IF PASS"


## IMP-071 BROADER VALID WINDOWS PASS / FROZEN GUARD NEXT - 2026-10-10
- [x] Targeted Node 12/12 + Python 7/7 PASS; DO NOT rerun unless code/test changes.
- [x] Affected service-boundary regression 9/9 PASS; DO NOT rerun.
- [x] Broader valid Windows regression 792/792 PASS; `.tmp/imp071-broader-valid.xml`; failures=0 errors=0 skipped=0.
- [ ] Run Frozen Master guard on current IMP-071 worktree.
- [ ] If PASS: exact-head review -> evidence -> Git lifecycle.
NEXT_EXACT_ACTION = "RUN ONLY FROZEN MASTER GUARD; TARGETED/AFFECTED/BROADER MUST NOT RERUN"


## IMP-071 FROZEN MASTER GUARD PASS / EXACT-HEAD REVIEW NEXT - 2026-10-10
- [x] Targeted Node 12/12 + Python 7/7 PASS; DO NOT rerun unless code/test changes.
- [x] Affected service-boundary regression 9/9 PASS; DO NOT rerun.
- [x] Broader valid Windows regression 792/792 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Exact-head static/security review + evidence.
- [ ] Side-effect guard -> feature commit -> governance sync -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "EXACT-HEAD REVIEW + EVIDENCE; NO TEST STAGE RERUN"


## IMP-071 LOCAL VERIFIED / COMMIT NEXT - 2026-10-10
- [x] Targeted Node 12/12 + Python 7/7 PASS; DO NOT rerun unless code/test changes.
- [x] Affected regression 9/9 PASS; DO NOT rerun.
- [x] Broader valid Windows regression 792/792 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Exact-head static/security review PASS.
- [x] Evidence written: `evidence/tests/IMP-071_TYPED_IPC_UTILITY_BRIDGE_EVIDENCE.md`.
- [x] Side-effect guard PASS: no duplicate feature commit/remote branch/PR; `.tmp` untracked only.
- [ ] Stage exact IMP-071 scope -> verify index -> feature commit.
NEXT_EXACT_ACTION = "STAGE EXACT IMP-071 SCOPE -> VERIFY INDEX -> FEATURE COMMIT; DO NOT RERUN TESTS"


## IMP-071 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-10
- [x] Feature commit created: `af6dbc84786504eef4f883b40adfbd01bbf8a3ec`.
- [x] Local verification evidence remains valid; code/test bytes unchanged after commit.
- [ ] Governance-only state sync commit.
- [ ] Side-effect guard -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "SYNC FEATURE SHA -> GOVERNANCE-ONLY COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-071 POST-MERGE TARGETED PASS / AFFECTED NEXT - 2026-10-10
- [x] PR #78 merged at exact main SHA `7ed4c28cd2010d5338e1b13232715eaab05ad3d6`.
- [x] Post-merge Node targeted 12/12 PASS; DO NOT rerun.
- [x] Post-merge Python Electron security targeted 7/7 PASS; `.tmp/imp071-main-targeted.xml`; DO NOT rerun.
- [~] Push-main CI run `38051480412` RUNNING on exact merge SHA.
- [ ] Run post-merge affected service-boundary regression only.
- [ ] Frozen Master guard after affected PASS.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN ONLY POST-MERGE AFFECTED REGRESSION; TARGETED MUST NOT RERUN"


## IMP-071 FEATURE MAIN VERIFIED / GOVERNANCE SYNC NEXT - 2026-10-10
- [x] PR #78 merged at exact main SHA `7ed4c28cd2010d5338e1b13232715eaab05ad3d6`.
- [x] Push-main CI run `38051480412` SUCCESS; Python 3.10 + 3.13 PASS.
- [x] Post-merge targeted Node 12/12 + Python 7/7 PASS; DO NOT rerun.
- [x] Post-merge affected 9/9 PASS; DO NOT rerun.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Governance-only state sync lifecycle.
NEXT_EXACT_ACTION = "GOVERNANCE SIDE-EFFECT GUARD -> STATE-ONLY BRANCH/COMMIT -> PUSH/PR/CI/REVIEW/MERGE"


## IMP-071 GOVERNANCE MAIN VERIFIED / IMP-072 CLAIMED - 2026-10-10
- [x] IMP-071 governance PR #79 merged at `021cdb068944f69059099b432767cffab4c67e9c`.
- [x] Governance push-main CI run `38068491662` SUCCESS; Python 3.10 + 3.13 PASS; Frozen Master baseline PASS.
- [x] IMP-072 dependency `IMP-071` satisfied.
- [x] Duplicate guard: no prior IMP-072 commit/local branch/remote branch/PR before claim.
- [x] Claimed `chatgpt/IMP-072-credential-broker-leases` from exact governance main.
- [ ] Read Frozen Master security authority for Credential Broker / safeStorage / scoped leases.
- [ ] Audit current typed IPC / Production Utility / preload secret surfaces and lock lease scope/expiry/revocation/rotation contract.
- [ ] Implement broker + safe storage boundary + scoped short-lived authorization without renderer secret access.
- [ ] Negative tests: renderer denial, invalid scope/expiry, revocation/rotation, secret scan; then affected/broader/Frozen guard/evidence/Git lifecycle.
NEXT_EXACT_ACTION = "READ FROZEN MASTER IMP-072 SECURITY/CREDENTIAL AUTHORITY + AUDIT CURRENT IPC/UTILITY/PRELOAD SECRET SURFACES -> LOCK CONTRACT/NEGATIVE TEST PLAN -> IMPLEMENT"


## IMP-072 AUTHORITY AUDIT LOCKED / CODE NEXT - 2026-10-10
- [x] Read Frozen Master §85 + ADR-0016 credential authority.
- [x] KEEP IMP-070 shell security + IMP-071 typed IPC/Utility bridge; no generic renderer credential bridge.
- [x] Lock Main/Host Security Broker as long-lived secret owner; safeStorage vault encrypted at rest; project/log/export surfaces metadata-only.
- [x] Lock utility session + lease scope: utility/session/provider/operation/credential-version/correlation + bounded TTL + single-use.
- [x] Lock revoke/rotation/utility-exit invalidation and Linux `basic_text` fail-closed policy.
- [x] Lock browser-session credentials as provider-specific; generic API-key lease semantics must not absorb them.
- [ ] Implement `credential-broker.cjs` + Main/package wiring.
- [ ] Targeted Node security tests: renderer denial, vault canary scan, wrong scope, expiry/replay, session revoke, rotation stale, insecure backend denial.
- [ ] Update Python Electron static-security gate; then affected/broader/Frozen guard/evidence/Git lifecycle.
NEXT_EXACT_ACTION = "IMPLEMENT MAIN-ONLY CREDENTIAL BROKER + PACKAGE WIRING + TARGETED NODE/PYTHON SECURITY TESTS"


## IMP-072 BROKER TARGETED NODE PASS - 2026-10-10
- [x] `node --test desktop/tests/credential-broker.test.cjs` = 9/9 PASS.
- [x] Renderer public surface has no credential/secret capability.
- [x] Vault canary scan confirms plaintext absent; metadata omits encrypted payload/secret.
- [x] Lease is single-use, TTL-bound and utility/provider/operation/version/correlation scoped.
- [x] Wrong session/provider/operation, expiry/replay, utility revoke, credential revoke, rotation stale and insecure backend all fail closed.
- [ ] Run targeted Python Electron static/security gate in standard uv Python 3.13 environment.
NEXT_EXACT_ACTION = "RUN TARGETED PYTHON ELECTRON SECURITY GATE; DO NOT RERUN STANDALONE NODE BROKER SUITE UNLESS BROKER CODE CHANGES"


## IMP-072 TARGETED PYTHON RUNNING - 2026-10-10
- [x] Broker Node security suite 9/9 PASS.
- [ ] Targeted Python Electron security gate RUNNING under PTY `pty_23c1dd144b40934a589bddbcbff00d4cf464`, root PID `97488`.
- JUnit `.tmp/imp072-targeted.xml` pending.
- Do not restart or create duplicate targeted pytest.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-072 TARGETED PYTHON PTY/PID/JUNIT -> CLASSIFY FINAL RESULT"


## IMP-072 TARGETED PASS / AFFECTED NEXT - 2026-10-11
- [x] Broker Node targeted = 9/9 PASS.
- [x] Python Electron security targeted = `.tmp/imp072-targeted.xml` 9/9 PASS, no fail/error/skip.
- [ ] Run affected project/session + upload API regression only; do not rerun targeted unless code/test changes.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN tests/unit/test_flow_project_session.py + tests/unit/test_flow_upload_api.py -> CLASSIFY FINAL RESULT"


## IMP-072 AFFECTED PASS / BROADER NEXT - 2026-10-11
- [x] Node broker targeted = 9/9 PASS.
- [x] Python Electron security targeted = 9/9 PASS.
- [x] Affected project/session + upload API regression = 9/9 PASS; `.tmp/imp072-affected.xml`.
- [ ] Run broader valid Windows regression excluding targeted/affected + `test_setup.py` + `test_video_reviewer.py` + established POSIX deselections.
- [ ] Frozen Master guard after broader PASS -> exact-head review/evidence/Git lifecycle.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN BROADER VALID WINDOWS REGRESSION; TARGETED/AFFECTED MUST NOT RERUN"


## IMP-072 BROADER VALID WINDOWS RUNNING - 2026-10-11
- [x] Targeted Node 9/9 + Python 9/9 PASS; do not rerun.
- [x] Affected service-boundary 9/9 PASS; do not rerun.
- [~] Broader valid Windows regression RUNNING under PTY `pty_2ce6a7d16b8ad605aaf6654eb1a812ddc3a1`, PID `98584`.
- [x] Scope excludes IMP-072 targeted+affected, `test_setup.py`, `test_video_reviewer.py`; established POSIX deselections unchanged.
- [ ] Finalize `.tmp/imp072-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-072 BROADER PTY/PID/JUNIT; DO NOT RESTART"


## IMP-072 BROADER VALID WINDOWS PASS / FROZEN GUARD NEXT - 2026-10-11
- [x] Node broker targeted = 9/9 PASS; do not rerun unless broker code/test changes.
- [x] Python Electron security targeted = 9/9 PASS; do not rerun unless affected code/test changes.
- [x] Affected project/session + upload API regression = 9/9 PASS; do not rerun.
- [x] Broader valid Windows regression = `.tmp/imp072-broader-valid.xml` 792/792 PASS; failures=0 errors=0 skipped=0; recorded PID 98584 absent after completion.
- [ ] Run Frozen Master guard on current IMP-072 worktree.
- [ ] Exact-head review/evidence/Git lifecycle only after Frozen guard PASS.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; TARGETED/AFFECTED/BROADER MUST NOT RERUN"


## IMP-072 EXACT-HEAD REVIEW FIX / PYTHON TARGETED RUNNING - 2026-10-11
- [x] Exact-head review found missing trusted Utility lease-consumer wiring required by Frozen §85 + ADR-0016.
- [x] Main now injects Credential Broker into ProductionUtilityBridge; Renderer API remains unchanged/secret-free.
- [x] Trusted child transport requires Main-authorized provider/operation scope, issues metadata-only lease, redeems once, and revokes session on Utility exit/bridge close.
- [x] Direct full desktop Node security suite = 22/22 PASS; npm wrapper failure was environment-only and executed no tests.
- [~] Python Electron security targeted RUNNING under PTY `pty_e14920849cc0dd328e75e9b653c060561249`, PID `111568`; JUnit `.tmp/imp072-review-targeted.xml` pending.
- [x] Prior broader valid Windows 792/792 PASS retained: it excludes Electron targeted file and does not execute desktop Node tests.
- [ ] On Python targeted PASS: final Frozen Master guard -> evidence -> side-effect guard -> commit/push/PR lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING PYTHON TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-072 LOCAL VERIFIED AFTER EXACT-HEAD REVIEW FIX - 2026-10-11
- [x] Exact-head review fixed the missing trusted Production Utility lease-consumer path required by Frozen §85 + ADR-0016.
- [x] Renderer remains secret-free; Main owns safeStorage/broker/session; Utility receives only Main-authorized scoped short-lived lease material over internal child transport.
- [x] Direct full desktop Node security suite = 22/22 PASS. The npm wrapper invocation failed before test execution because local npm bootstrap is broken; not a product failure.
- [x] Python Electron security targeted `.tmp/imp072-review-targeted.xml` = 9/9 PASS; no failures/errors/skips; PTY exit 0.
- [x] Affected backend 9/9 PASS retained because review fix does not touch those boundaries.
- [x] Broader valid Windows `.tmp/imp072-broader-valid.xml` = 792/792 PASS retained because it excludes the Electron targeted file and does not execute desktop Node tests.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Create evidence file, run side-effect guard, stage exact scope and feature commit.
NEXT_EXACT_ACTION = "CREATE IMP-072 EVIDENCE -> SIDE-EFFECT GUARD -> STAGE EXACT SCOPE/FEATURE COMMIT; DO NOT RERUN VERIFIED TESTS"


## IMP-072 EVIDENCE READY / SIDE-EFFECT GUARD PASS / COMMIT NEXT - 2026-10-11
- [x] Exact-head LOCAL VERIFIED: Node security 22/22 + Python Electron targeted 9/9 + affected 9/9 + broader Windows 792/792 + Frozen Master guard PASS.
- [x] Evidence: `evidence/tests/IMP-072_CREDENTIAL_BROKER_LEASES_EVIDENCE.md`.
- [x] Side-effect guard: no feature commit, remote branch or PR; staged index empty; `.tmp` untracked only.
- [x] Exact feature scope = 10 files (6 code/test/package + evidence + 3 state files).
- [ ] Stage exact scope; cached diff-check/index review; create feature commit.
NEXT_EXACT_ACTION = "STAGE EXACT IMP-072 SCOPE -> VERIFY CACHED INDEX/DIFF CHECK -> FEATURE COMMIT; EXCLUDE .tmp"


## IMP-072 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-11
- [x] Feature commit `710ddf4859290d78cc50ae4e6d2a7e2f0b64befc` created from the exact 10-file verified scope.
- [x] Worktree outside committed scope is `.tmp/` untracked only.
- [ ] Commit only the three state files recording the exact feature SHA.
- [ ] Side-effect guard -> push branch once -> create PR once -> exact-head CI/review.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> GOVERNANCE SYNC COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-072 POST-MERGE TARGETED RUNNING - 2026-10-11
- [x] PR #80 merged at exact main SHA `ce158039d3d732b8690fae7cacdcd798749f102d`.
- [x] Post-merge Node full desktop security suite = 22/22 PASS; do not rerun unless code changes.
- [~] Post-merge Python Electron targeted RUNNING under PTY `pty_2d13284979910771d16c45ea5db676cfc9de`, PID `106592`; JUnit `.tmp/imp072-main-targeted.xml` pending.
- [~] Push-main CI run `38105680682` RUNNING on exact main SHA.
- [ ] On Python targeted PASS: run affected 9-test backend regression, then Frozen Master guard; no broader rerun.
NEXT_EXACT_ACTION = "MONITOR EXISTING PYTHON TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-072 POST-MERGE PYTHON TARGETED PASS / AFFECTED RUNNING - 2026-10-11
- [x] Exact main SHA `ce158039d3d732b8690fae7cacdcd798749f102d`; PR #80 merged.
- [x] Post-merge Node desktop security = 22/22 PASS; do not rerun.
- [x] Post-merge Python Electron targeted = `.tmp/imp072-main-targeted.xml` 9/9 PASS; PTY exit 0; do not rerun.
- [~] Post-merge affected 9-test regression RUNNING: PTY `pty_60b2044469819f01a10d6c7c44af5df29d65`, PID `110328`; JUnit pending.
- [~] Push-main CI run `38105680682` tracked on exact merge SHA.
- [ ] On affected PASS: Frozen Master guard -> verify push-main CI -> feature MAIN VERIFIED.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-072 POST-MERGE AFFECTED PASS / FROZEN GUARD NEXT - 2026-10-11
- [x] Exact main SHA `ce158039d3d732b8690fae7cacdcd798749f102d`; PR #80 merged.
- [x] Post-merge Node desktop security = 22/22 PASS; do not rerun.
- [x] Post-merge Python Electron targeted = 9/9 PASS; do not rerun.
- [x] Post-merge affected project/session + upload API regression = `.tmp/imp072-main-affected.xml` 9/9 PASS; failures=0 errors=0 skipped=0; PID 110328 absent after completion.
- [x] Push-main CI run `38105680682` SUCCESS on exact main SHA; Python 3.10 + 3.13 unit tests and Frozen baseline PASS.
- [ ] Run Frozen Master guard on exact main SHA; then mark IMP-072 feature MAIN VERIFIED if PASS.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/CI"


## IMP-072 FEATURE MAIN VERIFIED - 2026-10-11
- [x] PR #80 merged at exact main SHA `ce158039d3d732b8690fae7cacdcd798749f102d`.
- [x] Post-merge Node desktop security = 22/22 PASS.
- [x] Post-merge Python Electron targeted = 9/9 PASS.
- [x] Post-merge affected project/session + upload API regression = 9/9 PASS.
- [x] Push-main CI run `38105680682` SUCCESS; Python 3.10 + 3.13 unit tests PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Read queue/DAG and claim next dependency-ready task.
NEXT_EXACT_ACTION = "READ TASK_QUEUE/DAG -> CLAIM NEXT DEPENDENCY-READY TASK; DO NOT RERUN IMP-072 VERIFIED STAGES"


## IMP-073 RENDERER / DASHBOARD ADAPTATION — CLAIMED + CODE CHECKPOINT 2026-10-11
- [x] Base exact main `9368a1ce4696e80752bb830481b7c0735da05756` (IMP-072 governance merge PR #81).
- [x] Hard dependencies IMP-071 + IMP-013 + IMP-023 + IMP-031 + IMP-052 + IMP-064 MAIN VERIFIED.
- [x] Authority audit locked to Frozen Master §93 + §84 and UX-001..004; no second UI truth store.
- [x] Typed versioned Studio read-model contract with all 8 required view groups implemented.
- [x] Narrow Utility/Main/preload capability; strict sender/schema validation; canonical-provider-unavailable fail-closed.
- [x] Electron renderer consumes bounded bridge only; no generic invoke/fs/child_process/shell/secret surface.
- [x] React/Vite donor adapter + Project Overview Studio panel implemented; web fallback explicitly `LEGACY_COMPATIBILITY`.
- [x] Desktop Node syntax gate PASS.
- [x] Desktop security/IPC/credential targeted suite PASS 25/25.
- [x] `npm ci` failure classified harness/bootstrap only: package-lock missing transitive `@emnapi/*`; build never started.
- [x] Corrected dependency bootstrap `npm install --no-package-lock --no-audit --no-fund` PASS; 532 packages materialized.
- [ ] Dashboard TypeScript/Vite build.
- [ ] Exact-head authority/security/backward-compat review, Frozen guard, evidence, commit/PR/main verification.
NEXT_EXACT_ACTION = "RUN DASHBOARD BUILD; DO NOT RERUN DESKTOP 25/25 UNLESS CODE CHANGES"


## IMP-073 DASHBOARD BUILD CHECKPOINT — 2026-10-11
- [x] Dashboard dependency materialization PASS using no-package-lock retry after pre-existing lock mismatch.
- [x] Dashboard production build `tsc -b && vite build` PASS, exit 0.
- [x] package-lock remains unchanged.
- [x] Desktop targeted 25/25 PASS retained.
- [ ] Changed-file lint + exact-head authority/security review.
- [ ] Frozen Master guard -> evidence -> Git/PR/main verification.
NEXT_EXACT_ACTION = "RUN CHANGED-FILE LINT + EXACT-HEAD SECURITY/AUTHORITY REVIEW; DO NOT RERUN PASSED DESKTOP OR DASHBOARD BUILD STAGES"


## IMP-073 EXACT-HEAD REVIEW FIX VERIFIED - 2026-10-11
- [x] Changed-file dashboard ESLint PASS after fixing synchronous effect state reset.
- [x] Exact dashboard production build PASS via direct local `tsc -b` + Vite; npm wrapper failure occurred before build and is environment-only.
- [x] Exact-head review found and fixed wrong-project canonical read-model acceptance: response now binds to requested projectId at Utility bridge/Main/preload.
- [x] Added wrong-project negative coverage.
- [x] Desktop static gate PASS.
- [x] Direct desktop security/IPC/credential targeted suite = 27/27 PASS.
- [x] `git diff --check` + renderer leakage/generic-invoke scan PASS.
- [ ] Frozen Master guard.
- [ ] Evidence + Git/PR/main verification lifecycle.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN VERIFIED LINT/BUILD/DESKTOP TARGETED UNLESS CODE CHANGES"


## IMP-073 LOCAL VERIFIED / GIT SIDE-EFFECT GUARD NEXT - 2026-10-11
- [x] Dashboard changed-file ESLint PASS.
- [x] Exact dashboard TypeScript/Vite build PASS.
- [x] Exact-head project-binding security fix implemented + negative tests.
- [x] Desktop affected static gate PASS.
- [x] Desktop security/IPC/credential targeted = 27/27 PASS.
- [x] Exact-head diff/security/authority review PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [x] Evidence: `evidence/tests/IMP-073_RENDERER_DASHBOARD_ADAPTATION_EVIDENCE.md`.
- [ ] Git side-effect guard -> exact-scope commit/push/PR lifecycle.
NEXT_EXACT_ACTION = "RUN GIT SIDE-EFFECT GUARD -> STAGE EXACT IMP-073 SCOPE EXCLUDING .tmp -> VERIFY INDEX -> COMMIT; DO NOT RERUN VERIFIED STAGES"


## IMP-073 FEATURE COMMIT CREATED / GOVERNANCE SYNC NEXT - 2026-10-11
- [x] Exact feature commit `ff3d236258c4655c658d45a4ce99dd85890bcc21` created from locally verified IMP-073 scope.
- [x] Dashboard lint/build, desktop static + 27/27 targeted, authority/security review and Frozen Master guard remain PASS; do not rerun unless code changes.
- [x] Worktree outside committed scope is `.tmp/` untracked only.
- [ ] Commit only the three state files recording the exact feature SHA.
- [ ] Side-effect guard -> push branch once -> create PR once -> exact-head CI/review.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> GOVERNANCE SYNC COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-073 POST-MERGE LOCAL PASS / PUSH-MAIN CI RUNNING - 2026-10-11
- [x] PR #82 merged at exact main SHA `706b2bed14e38881d04e9552df1ab5441de8d911`.
- [x] Post-merge desktop security/IPC/read-model targeted = 27/27 PASS; do not rerun unless code changes.
- [x] Post-merge dashboard TypeScript `tsc -b` + Vite production build PASS; do not rerun.
- [x] Post-merge Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [~] Push-main CI run `38125248556` RUNNING on exact main SHA.
- [ ] On CI SUCCESS: mark IMP-073 feature MAIN VERIFIED, then run governance-only state lifecycle.
NEXT_EXACT_ACTION = "MONITOR PUSH-MAIN CI 38125248556; DO NOT RERUN POST-MERGE TARGETED/BUILD/FROZEN"


## IMP-073 FEATURE MAIN VERIFIED - 2026-10-11
- [x] PR #82 merged at exact main SHA `706b2bed14e38881d04e9552df1ab5441de8d911`.
- [x] Post-merge desktop security/IPC/read-model targeted = 27/27 PASS.
- [x] Post-merge dashboard TypeScript/Vite production build PASS.
- [x] Push-main CI run `38125248556` SUCCESS; Python 3.10 + 3.13 unit tests and Frozen baseline PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Governance-only state sync branch/commit/PR, then governance main verification.
- [ ] Read queue/DAG and claim next dependency-ready task.
NEXT_EXACT_ACTION = "GOVERNANCE-ONLY STATE SYNC -> VERIFY GOVERNANCE MAIN -> CLAIM NEXT TASK"


## 2026-10-11T16:09+07:00 — IMP-080 CLAIMED
- Prior checkpoint: IMP-073 governance MAIN VERIFIED on exact `main` SHA `35823eeafbf6f0f8a6c6354b9d874d346d432247`; CI `38127454286` SUCCESS (Python 3.10 + 3.13; Frozen guard PASS).
- Task: `IMP-080 — Legacy Import Anti-Corruption`.
- Status: ACTIVE / CLAIMED / ANALYZE.
- Branch: `chatgpt/IMP-080-legacy-import-anti-corruption` from exact main SHA `35823eeafbf6f0f8a6c6354b9d874d346d432247`.
- Hard deps verified: IMP-005, IMP-023, IMP-031, IMP-052 = MAIN VERIFIED.
- Acceptance focus: bounded/auditable legacy mapping; explicit `NOT_PROVABLE`; legacy prompt/prose MUST NOT auto-create canonical `SceneDramaticBeat` or `FullShotSpec` truth.
- Process/PID: none.
- Blocker: none.
- NEXT_EXACT_ACTION: audit frozen authority + legacy/canonical import surfaces, lock anti-corruption contract and targeted tests, then implement without inventing narrative truth.


## 2026-10-11 — IMP-080 AUTHORITY + SURFACE AUDIT PASS
- [x] Read Master §90 Legacy Anti-Corruption, §91 Current→Canonical Mapping, §92 Migration Strategy.
- [x] Audit legacy Project.story, Entity adapter, operational Scene prompt/media/chain fields, GenerationJob identity/revision and canonical ShotListItem authority.
- [x] Lock no-shadow-truth-store rule; shared VersionRepository only for mapping/finding evidence.
- [x] Lock `project.story = seed-only`, Entity = existing IMP-040 adapter, Scene = compatibility projection only with explicit exact proof.
- [x] Lock prompt/prose/order/media as derivative evidence; they cannot allocate cinematic Scene/SceneDramaticBeat/FullShotSpec/ShotIR truth.
- [x] Lock explicit `NOT_PROVABLE` for missing/stale/dangling/forbidden/ambiguous mapping proof.
- [ ] Implement typed legacy mapping/finding evidence + repository/service + public exports.
- [ ] Targeted tests: prompt non-authority, forbidden creative target, exact ShotListItem/GenerationJob proof, stale/dangling proof, story seed-only, replay/provenance.
- [ ] Affected/broader regression + Frozen guard + evidence/Git lifecycle.
- NEXT_EXACT_ACTION: implement `agent/studio/legacy_import.py`, export API, add targeted tests, run syntax/import then targeted only.


## IMP-080 TARGETED PASS
- [x] Static compile/public-import/diff gate PASS.
- [x] Targeted IMP-080 = 7/7 PASS; JUnit `.tmp/imp080-targeted.xml`, failures=0/errors=0/skipped=0; PTY exit 0.
- [x] Prompt prose non-authority, forbidden creative target, dangling target, explicit ShotListItem+GenerationJob proof, stale revision, project.story seed-only and replay/provenance covered.
- [ ] Exact-head authority/provenance self-review.
- [ ] Affected regression on reused owners; broader valid Windows regression; Frozen guard.
- [ ] Evidence / state sync / commit / push / PR / CI / exact-head review / merge / main verify / governance.
- NEXT_EXACT_ACTION: self-review `legacy_import.py` against Master §90–§92; do not rerun targeted unless code/test changes.


## IMP-080 REVIEW-FIX TARGETED RUNNING
- [x] Exact-head review found and fixed prefix-only Shot proof authority gap.
- [x] Added fault test: fake semantic row with `shot-list-item:*` prefix is not valid canonical ShotListItem proof.
- [ ] Review-fix targeted exact-head result pending.
- PTY/PID: `pty_fb8ec88ef66aea4198465fe876826f9b52c4` / `107864`.
- JUnit: `.tmp/imp080-review-targeted.xml`.
- NEXT_EXACT_ACTION: monitor existing run; do not restart or launch affected until targeted final evidence.


## IMP-080 REVIEW-FIX TARGETED PASS
- [x] Harden Shot proof through ShotPlanning owner repository, not prefix-only generic semantic row.
- [x] Fault test rejects fake `shot-list-item:*` semantic payload.
- [x] Exact-head targeted = 8/8 PASS, JUnit clean, exit 0.
- [ ] Affected regression: entity + shot_planning + generation_job + versioning + invalidation + persistence.
- [ ] Broader valid Windows regression + Frozen guard + evidence/Git lifecycle.
- NEXT_EXACT_ACTION: run affected six-file regression; do not rerun targeted unless code changes.


## IMP-080 AFFECTED REGRESSION RUNNING
- [x] Targeted exact head 8/8 PASS; excluded from affected command.
- [ ] Affected six-file regression running.
- PTY/PID: `pty_5a649998908c99da8be3d26db1de3c474f13` / `118704`.
- JUnit: `.tmp/imp080-affected.xml`.
- NEXT_EXACT_ACTION: monitor existing affected run only; do not restart or launch broader until final JUnit/exit.


## IMP-080 AFFECTED REGRESSION PASS — 2026-10-11
- [x] Exact-head targeted 8/8 PASS retained.
- [x] Affected owner regression `.tmp/imp080-affected.xml` = 72/72 PASS; failures=0 errors=0 skipped=0; prior PID 118704 ended.
- [ ] Broader valid Windows regression excluding targeted + six affected owner suites already PASS.
- [ ] Frozen Master guard -> evidence -> Git/PR/main verification.
NEXT_EXACT_ACTION = "RUN BROADER VALID WINDOWS REGRESSION WITH PASS-SCOPE EXCLUSIONS; DO NOT RERUN TARGETED/AFFECTED"


## IMP-080 BROADER VALID WINDOWS REGRESSION RUNNING — 2026-10-11
- [x] Targeted exact-head 8/8 PASS retained.
- [x] Affected owner regression 72/72 PASS retained.
- [~] Broader valid Windows regression RUNNING under PTY `pty_0c64ebe3fad14a6c0f9ed61019d24fb044e4`, PID `117776`; JUnit pending at `.tmp/imp080-broader-valid.xml`.
- [ ] On broader PASS: Frozen Master guard -> evidence -> Git/PR/main verification.
NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER PTY/JUNIT; DO NOT RESTART"


## IMP-080 BROADER VALID WINDOWS REGRESSION PASS — 2026-10-11
- [x] Exact-head targeted 8/8 PASS retained.
- [x] Affected owner regression 72/72 PASS retained.
- [x] Broader valid Windows regression 738/738 PASS; `.tmp/imp080-broader-valid.xml`, failures/errors/skips = 0.
- [ ] Frozen Master guard on current IMP-080 worktree.
- [ ] Final static/exact-head review -> evidence -> state sync -> commit -> push/PR -> CI -> merge/main verify.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/BROADER"


## IMP-080 FROZEN MASTER GUARD PASS — 2026-10-11
- [x] Targeted exact-head 8/8 PASS.
- [x] Affected owner regression 72/72 PASS.
- [x] Broader valid Windows regression 738/738 PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Final static/exact-head review -> evidence -> state sync -> commit -> push/PR -> CI -> merge/main verify.
NEXT_EXACT_ACTION = "FINAL STATIC/EXACT-HEAD REVIEW; DO NOT RERUN PASSED TEST STAGES"


## IMP-080 FINAL-REVIEW TARGETED RUNNING — 2026-10-11
- [x] Review hardened legacy row serialization to fail closed on opaque runtime objects.
- [~] Exact-head targeted revalidation running under PTY `pty_77816cc53aa446b67a9d52b99f7c44a287e5`, PID `123444`.
- JUnit: `.tmp/imp080-final-review-targeted.xml`.
- [ ] On PASS: rerun affected owner regression because code/test changed, then broader valid Windows regression, Frozen guard, evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING TARGETED RUN; DO NOT RESTART"


## IMP-080 FINAL-REVIEW TARGETED PASS — 2026-10-11
- [x] Strict JSON serialization hardening applied; opaque runtime object fault test added.
- [x] Exact-head targeted revalidation = 9/9 PASS; JUnit clean; PTY exit 0.
- [ ] Rerun affected six-owner regression because implementation/test changed after prior 72/72 checkpoint.
- [ ] Then broader valid Windows regression -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "RUN AFFECTED SIX-OWNER REGRESSION ONLY; DO NOT RERUN TARGETED"


## IMP-080 FINAL-REVIEW AFFECTED RUNNING — 2026-10-11
- [x] Exact-head targeted 9/9 PASS retained.
- [~] Affected six-owner regression running under PTY `pty_be5a6d986811ba45511ee503a578a49b7fa9`, PID `119124`.
- JUnit: `.tmp/imp080-final-review-affected.xml`.
- [ ] On PASS: broader valid Windows regression -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED RUN; DO NOT RESTART OR LAUNCH BROADER"


## IMP-080 FINAL-REVIEW AFFECTED PASS — 2026-10-11
- [x] Targeted exact-head 9/9 PASS retained.
- [x] Affected six-owner regression 72/72 PASS; JUnit clean; PTY exit 0.
- [ ] Broader valid Windows regression excluding targeted + six affected files + `test_setup.py` + `test_video_reviewer.py` + exact 3 historical POSIX-path deselections.
- [ ] Frozen Master guard -> final evidence/Git lifecycle.
NEXT_EXACT_ACTION = "RUN BROADER VALID WINDOWS REGRESSION; DO NOT RERUN TARGETED/AFFECTED"


## IMP-080 FINAL-REVIEW BROADER VALID WINDOWS RUNNING — 2026-10-11
- [x] Targeted exact-head 9/9 PASS retained.
- [x] Affected six-owner regression 72/72 PASS retained.
- [~] Broader valid Windows regression running under PTY `pty_76594df9e4bb2075f72a52fa32fbe831ca6d`, PID `123436`.
- Scope excludes targeted + six affected + `test_setup.py` + `test_video_reviewer.py`; exact 3 POSIX-path assertions deselected; UTF-8 mode enabled.
- [ ] On PASS: Frozen Master guard -> final evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING BROADER RUN; DO NOT RESTART"


## IMP-080 FINAL-REVIEW BROADER VALID WINDOWS PASS — 2026-10-11
- [x] Exact-head targeted 9/9 PASS retained.
- [x] Affected six-owner regression 72/72 PASS retained.
- [x] Broader valid Windows regression 738/738 PASS; `.tmp/imp080-final-review-broader-valid.xml`; PTY exit 0; 3 known assertions deselected by established Windows envelope.
- [ ] Frozen Master guard on exact current worktree.
- [ ] Final static/exact-head review -> evidence -> state sync -> commit -> push/PR -> CI -> merge/main verification.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/BROADER"


## IMP-080 FINAL FROZEN + STATIC PASS — 2026-10-11
- [x] Exact-head targeted 9/9 PASS.
- [x] Affected six-owner regression 72/72 PASS.
- [x] Broader valid Windows regression 738/738 PASS; 3 established assertions deselected by Windows envelope.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [x] Final static/public-import/diff/leakage gate PASS; canonical public service export is `LegacyImportAntiCorruptionService`.
- [ ] Evidence -> side-effect guard -> feature commit -> governance sync -> push/PR -> exact-head CI/review -> merge/main verification.
NEXT_EXACT_ACTION = "CREATE IMP-080 EVIDENCE -> SIDE-EFFECT GUARD -> COMMIT"


## IMP-080 LOCAL VERIFIED / SIDE-EFFECT GUARD PASS — 2026-10-11
- [x] Final exact-head targeted 9/9 PASS.
- [x] Final affected six-owner regression 72/72 PASS.
- [x] Final broader valid Windows regression 738/738 PASS.
- [x] Frozen Master guard + final static/public-import/diff/leakage gate PASS.
- [x] Evidence: `evidence/tests/IMP-080_LEGACY_IMPORT_ANTI_CORRUPTION_EVIDENCE.md`.
- [x] Side-effect guard: no existing feature commit/remote branch/PR; index empty; `.tmp` untracked.
- [ ] Stage exact 7-file scope -> verify cached diff -> feature commit.
- [ ] Governance exact-SHA sync -> push/PR -> exact-head CI/review -> merge/main verify.
NEXT_EXACT_ACTION = "STAGE EXACT 7 FILES -> VERIFY INDEX -> FEATURE COMMIT"


## IMP-080 FEATURE COMMIT CREATED — 2026-10-11
- [x] Feature commit `fcbe193d2be5dd7b5ef46dc6a35f0be836942bfe` created from exact verified 7-file scope.
- [x] `.tmp` excluded.
- [ ] Governance-only commit recording exact feature SHA.
- [ ] Side-effect guard -> push branch once -> create PR once -> exact-head CI/review.
NEXT_EXACT_ACTION = "STAGE ONLY 3 STATE FILES -> GOVERNANCE SYNC COMMIT -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-080 POST-MERGE MAIN TARGETED RUNNING — 2026-10-11
- [x] PR #84 merged at exact main SHA `0c14106121639e90af143715477ec00dd8b1ab6e`.
- [~] Push-main CI `38150493334` RUNNING exact merge SHA; do not retrigger.
- [~] Post-merge targeted `tests/unit/test_studio_legacy_import.py` RUNNING under PTY `pty_26d6ca0a3681446105504064401b6fc2413e`, PID `122104`.
- JUnit: `.tmp/imp080-main-targeted.xml`.
- [ ] On targeted PASS: run six-owner affected main regression only (Entity, ShotPlanning, GenerationJob, VersionRepository, Invalidation, Persistence).
- [ ] After affected PASS + push-main CI SUCCESS: Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-080 MAIN TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-080 POST-MERGE TARGETED PASS / AFFECTED NEXT — 2026-10-11
- [x] PR #84 merged at exact main SHA `0c14106121639e90af143715477ec00dd8b1ab6e`.
- [x] Post-merge targeted = 9/9 PASS; `.tmp/imp080-main-targeted.xml`, failures/errors/skips = 0; prior PID ended.
- [~] Push-main CI `38150493334` still RUNNING exact merge SHA; both jobs passed Frozen baseline and are in unit tests.
- [ ] Post-merge six-owner affected regression only: Entity / ShotPlanning / GenerationJob / VersionRepository / Invalidation / Persistence.
- [ ] After affected PASS + CI SUCCESS: Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "RUN SIX-OWNER POST-MERGE AFFECTED REGRESSION ONLY; TARGETED MUST NOT RERUN"


## IMP-080 POST-MERGE AFFECTED RUNNING — 2026-10-11
- [x] Post-merge targeted 9/9 PASS on exact main SHA `0c14106121639e90af143715477ec00dd8b1ab6e`; do not rerun.
- [~] Six-owner affected regression RUNNING under PTY `pty_e0a686fb9cc48664f93592c953069787d74f`, PID `123476`.
- JUnit: `.tmp/imp080-main-affected.xml`.
- Scope: Entity / ShotPlanning / GenerationJob / VersionRepository / Invalidation / Persistence only.
- [~] Push-main CI `38150493334` RUNNING exact merge SHA; do not retrigger.
- [ ] After affected PASS + CI SUCCESS: Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-080 MAIN AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-080 PUSH-MAIN CI PASS / AFFECTED STILL RUNNING — 2026-10-11
- [x] Push-main CI `38150493334` SUCCESS on exact main SHA `0c14106121639e90af143715477ec00dd8b1ab6e`; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Main targeted 9/9 PASS retained.
- [~] Main six-owner affected regression remains RUNNING under PTY `pty_e0a686fb9cc48664f93592c953069787d74f`, PID `123476`.
- [ ] On affected PASS: run Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-080 POST-MERGE AFFECTED PASS / FROZEN NEXT — 2026-10-11
- [x] Main targeted = 9/9 PASS.
- [x] Main six-owner affected = 72/72 PASS; `.tmp/imp080-main-affected.xml`, failures/errors/skips = 0; PTY exit 0.
- [x] Push-main CI `38150493334` SUCCESS on exact merge SHA `0c14106121639e90af143715477ec00dd8b1ab6e`; Python 3.10 + 3.13 + Frozen baseline PASS.
- [ ] Run Frozen Master guard on exact main SHA.
- [ ] On guard PASS: feature MAIN VERIFIED -> governance-only state sync -> governance PR/CI/merge/main verify.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT MAIN; DO NOT RERUN TARGETED/AFFECTED/CI"


## IMP-080 FEATURE MAIN VERIFIED — 2026-10-11
- [x] PR #84 merged at exact main SHA `0c14106121639e90af143715477ec00dd8b1ab6e`.
- [x] Post-merge targeted = 9/9 PASS.
- [x] Post-merge six-owner affected = 72/72 PASS.
- [x] Push-main CI `38150493334` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Post-merge Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Governance-only MAIN VERIFIED sync -> PR/CI/merge/main verify.
NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD FOR chatgpt/IMP-080-main-verified-state; IF ABSENT CREATE GOVERNANCE-ONLY BRANCH/COMMIT -> PUSH/PR/CI/MERGE/VERIFY MAIN"


## IMP-080 GOVERNANCE VERIFIED / IMP-081 CLAIMED — 2026-10-11
- [x] IMP-080 governance PR #85 merged at exact main SHA `126f927cd9386881a47fb1b8e22b9ac3eb4e6454`.
- [x] Governance push-main CI `38154586703` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] IMP-080 governance lifecycle VERIFIED.
- [x] IMP-081 hard dependencies IMP-080 + IMP-031 + IMP-052 MAIN VERIFIED.
- [x] No pre-existing local/remote branch or PR for `chatgpt/IMP-081-operational-scene-execution-projection`.
- [x] Claimed IMP-081 branch from exact governance main `126f927cd9386881a47fb1b8e22b9ac3eb4e6454`.
- [ ] Read frozen/ADR authority and audit legacy Scene/media/request + canonical ShotListItem/GenerationJob/Artifact compatibility surfaces.
- [ ] Lock projection contract + negative tests: legacy scene never becomes cinematic Scene authority; media/results remain reachable.
- [ ] Implement -> targeted -> affected -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "READ IMP-081 FROZEN/ADR AUTHORITY + AUDIT LEGACY SCENE/MEDIA/REQUEST AND CANONICAL SHOTLISTITEM/GENERATIONJOB/ARTIFACT SURFACES BEFORE CODE"


## IMP-081 TARGETED RUNNING — 2026-10-11
- [x] Frozen/ADR authority + legacy Scene/media/request + canonical ShotListItem/GenerationJob compatibility audit locked.
- [x] Draft implementation + public export + 7 targeted tests written.
- [x] Static/public-import gate PASS.
- [~] Targeted pytest RUNNING under PTY `pty_eb7c0190c55f5fa507613688a289e44a4178`, PID `124812`; JUnit `.tmp/imp081-targeted.xml`.
- [ ] On targeted PASS: exact-head review -> affected owner regression -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-081 TARGETED PASS — 2026-10-11
- [x] Static/public-import gate PASS.
- [x] Targeted composite = 7/7 PASS (initial 6 PASS + 1 expectation-only FAIL; exact failed-case rerun 1/1 PASS, exit 0).
- [x] No implementation change was needed for the failed case; targeted checkpoint is locked.
- [ ] Exact-head review -> affected owner regression -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "EXACT-HEAD REVIEW -> AFFECTED OWNER REGRESSION; DO NOT RERUN TARGETED"


## IMP-081 AFFECTED REGRESSION RUNNING — 2026-10-11
- [x] Targeted composite 7/7 PASS retained.
- [x] Exact-head authority/security/idempotency review PASS.
- [~] Affected owner regression RUNNING under PTY `pty_eb77482fd8159f5d14a7158097de214e5afc`, PID `102324`.
- Scope: LegacyImport + ShotPlanning + GenerationJob + Versioning + Invalidation + Persistence; IMP-081 targeted excluded.
- [ ] On PASS: broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-081 AFFECTED REGRESSION PASS — 2026-10-12
- [x] Targeted composite 7/7 PASS retained; do not rerun unless implementation/test changes.
- [x] Affected owner regression PASS: `.tmp/imp081-affected.xml` = 74 tests / 0 failures / 0 errors / 0 skipped; time 1277.537s.
- [x] Recorded PID `102324` absent after completion; classified PASS, not INTERRUPTED.
- [ ] Run broader valid Windows regression using established exclusions; exclude IMP-081 targeted + affected files already PASS.
- [ ] On broader PASS: Frozen Master guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "RUN BROADER VALID WINDOWS REGRESSION WITH TARGETED + AFFECTED FILES EXCLUDED; DO NOT RERUN PASSED STAGES"


## IMP-081 BROADER VALID WINDOWS REGRESSION RUNNING — 2026-10-12
- [x] Targeted composite 7/7 PASS retained.
- [x] Affected owner regression 74/74 PASS retained.
- [~] Broader valid Windows regression RUNNING under PTY `pty_dfe2fa6f3464bbda878215b2872b46cc27c7`, PID `125556`.
- [ ] Finalize `.tmp/imp081-broader-valid.xml` from final JUnit/exit only.
- [ ] On broader PASS: Frozen Master guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 BROADER PTY/JUNIT; DO NOT RESTART"

## IMP-081 BROADER VALID WINDOWS REGRESSION PASS — 2026-10-12
- [x] Targeted composite 7/7 PASS retained.
- [x] Affected owner regression 74/74 PASS retained.
- [x] Broader valid Windows regression PASS: `.tmp/imp081-broader-valid.xml` = 745 tests / 0 failures / 0 errors / 0 skipped; time 2032.554s.
- [x] Recorded PID `125556` absent after completion; durable JUnit => PASS, not INTERRUPTED.
- [ ] Run Frozen Master guard on exact current head.
- [ ] On guard PASS: final review/evidence -> side-effect guard -> commit/push/PR/CI/merge/main verify.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD; DO NOT RERUN TARGETED/AFFECTED/BROADER"

## IMP-081 LOCAL VERIFIED — 2026-10-12
- [x] Targeted composite 7/7 PASS.
- [x] Affected owner regression 74/74 PASS.
- [x] Broader valid Windows regression 745/745 PASS.
- [x] Frozen Master guard PASS; semantic SHA unchanged.
- [x] Final static/public-import/diff/leakage gate PASS.
- [x] Evidence: `evidence/tests/IMP-081_OPERATIONAL_SCENE_EXECUTION_PROJECTION_EVIDENCE.md`.
- [ ] Side-effect guard -> stage exact 7-file scope -> commit -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD; STAGE ONLY IMP-081 SOURCE/EXPORT/TEST/EVIDENCE + 3 STATE FILES; EXCLUDE .tmp"

## IMP-081 FEATURE COMMIT — 2026-10-12
- [x] Feature commit $sha created.
- [x] Worktree outside Git = .tmp/ only.
- [ ] Governance-only sync of exact feature SHA in CURRENT_HANDOFF / PROJECT_STATE / TASK_QUEUE.
- [ ] Then side-effect guard -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "CREATE GOVERNANCE-ONLY STATE SYNC COMMIT FOR IMP-081 FEATURE SHA"

## IMP-081 POST-MERGE TARGETED RUNNING — 2026-10-12
- [x] PR #86 merged at exact main SHA `c16ad1ba555803152f095d8fbba3fba2f540bb47`.
- [~] Push-main CI `38198156256` RUNNING exact merge SHA; do not retrigger.
- [~] Main targeted RUNNING under PTY `pty_ea1061336efe3db5a5458e6a74aa5ae8142b`, PID `128468`; JUnit `.tmp/imp081-main-targeted.xml`.
- [ ] On targeted PASS: affected owner regression -> Frozen guard -> feature MAIN VERIFIED.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 MAIN TARGETED PTY/JUNIT; DO NOT RESTART"

## IMP-081 POST-MERGE TARGETED PASS — 2026-10-12
- [x] Main targeted = 7/7 PASS; PTY exit 0; JUnit `.tmp/imp081-main-targeted.xml`.
- [ ] Run affected owner regression only (LegacyImport + ShotPlanning + GenerationJob + Versioning + Invalidation + Persistence); targeted excluded.
- [~] Monitor push-main CI `38198156256` read-only.
NEXT_EXACT_ACTION = "RUN IMP-081 MAIN AFFECTED OWNER REGRESSION; DO NOT RERUN TARGETED"

## IMP-081 POST-MERGE AFFECTED RUNNING — 2026-10-12
- [x] Main targeted = 7/7 PASS retained.
- [~] Main affected owner regression RUNNING under PTY `pty_f517073f90e95ba5c2a9cd97fd5927d2db29`, PID `121468`; JUnit `.tmp/imp081-main-affected.xml`.
- Scope: LegacyImport + ShotPlanning + GenerationJob + Versioning + Invalidation + Persistence; targeted excluded.
- [~] Push-main CI `38198156256` monitored read-only.
- [ ] On affected PASS + CI SUCCESS: Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 MAIN AFFECTED PTY/JUNIT; DO NOT RESTART"

## IMP-081 PUSH-MAIN CI PASS / AFFECTED STILL RUNNING — 2026-10-12
- [x] Push-main CI `38198156256` SUCCESS on exact main SHA `c16ad1ba555803152f095d8fbba3fba2f540bb47`; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Main targeted 7/7 PASS retained.
- [~] Main affected owner regression remains RUNNING under PTY `pty_f517073f90e95ba5c2a9cd97fd5927d2db29`, PID `121468`.
- [ ] On affected PASS: Frozen Master guard -> feature MAIN VERIFIED -> governance-only sync.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-081 MAIN AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-081 POST-MERGE AFFECTED PASS / FROZEN NEXT — 2026-10-12
- [x] Main targeted = 7/7 PASS; do not rerun.
- [x] Main affected owner regression PASS: `.tmp/imp081-main-affected.xml` = 74 tests / 0 failures / 0 errors / 0 skipped; time 1121.232s.
- [x] Recorded PID `121468` absent after completion; classified PASS, not INTERRUPTED.
- [x] Push-main CI `38198156256` SUCCESS on exact merge SHA `c16ad1ba555803152f095d8fbba3fba2f540bb47`; Python 3.10 + 3.13 + Frozen baseline PASS.
- [ ] Run Frozen Master guard on exact main SHA.
- [ ] On guard PASS: feature MAIN VERIFIED -> governance-only state sync -> governance PR/CI/merge/main verify.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT MAIN; DO NOT RERUN TARGETED/AFFECTED/CI"


## IMP-081 FEATURE MAIN VERIFIED — 2026-10-12
- [x] PR #86 merged at exact main SHA `c16ad1ba555803152f095d8fbba3fba2f540bb47`.
- [x] Post-merge targeted = 7/7 PASS.
- [x] Post-merge affected owner regression = 74/74 PASS.
- [x] Push-main CI `38198156256` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] Post-merge Frozen Master guard PASS; semantic SHA unchanged.
- [ ] Governance-only MAIN VERIFIED sync -> PR/CI/merge/main verify.
NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD FOR chatgpt/IMP-081-main-verified-state; IF ABSENT CREATE GOVERNANCE-ONLY BRANCH/COMMIT -> PUSH/PR/CI/MERGE/VERIFY MAIN"


## IMP-081 GOVERNANCE VERIFIED / IMP-082 CLAIMED — 2026-10-12
- [x] IMP-081 governance PR #87 merged at exact main SHA `dbee0bc784bcbf6ccd164069d8399ce61af1f277`.
- [x] Governance push-main CI `38202460325` SUCCESS; Python 3.10 + 3.13 + Frozen baseline PASS.
- [x] IMP-081 governance lifecycle VERIFIED.
- [x] IMP-082 hard dependencies IMP-003 + IMP-055 + IMP-080 MAIN VERIFIED/governance VERIFIED.
- [x] No pre-existing local/remote branch or PR for `chatgpt/IMP-082-backup-restore-migration-safety`.
- [x] Claimed IMP-082 branch from exact governance main `dbee0bc784bcbf6ccd164069d8399ce61af1f277`.
- [ ] Read frozen/ADR authority and audit persistence/schema migration + artifact backup/restore surfaces.
- [ ] Lock restart-safe backup manifest/hash/staged-restore contract and negative tests: interrupted migration, unsupported newer schema, manifest/hash mismatch, partial backup never success.
- [ ] Implement -> targeted -> affected -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "READ IMP-082 FROZEN/ADR AUTHORITY + AUDIT PERSISTENCE/MIGRATION/ARTIFACT BACKUP-RESTORE SURFACES BEFORE CODE"


## IMP-082 AUTHORITY / SURFACE AUDIT LOCKED — 2026-10-12
- [x] Read update/migration/backup authority + failure/recovery model + Windows persistence evidence.
- [x] Audit current persistence: keep transactional `ensure_schema_compatibility`; newer/identity-mismatched schemas fail closed; no IMP-082 schema bump.
- [x] Audit artifact lifecycle: required canonical artifact backup set derives from READY `MATERIALIZE_VALID` path/hash/size evidence.
- [x] Lock contract: verified atomic backup publication; partial backup never success; deterministic retry; staged restore only; migrate/verify staging before promotion outside this task.
- [x] Lock negative tests: interrupted migration rollback/resume; unsupported newer schema; manifest/artifact hash mismatch; missing required artifact blocks success; staged restore does not overwrite active project.
- [ ] Implement module/export/tests -> targeted -> affected -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "IMPLEMENT MINIMAL IMP-082 BACKUP/RESTORE ORCHESTRATION + TARGETED TESTS; STATIC/IMPORT THEN TARGETED ONLY"


## IMP-082 TARGETED RUNNING — 2026-10-12
- [x] Authority/surface audit locked.
- [x] Draft backup/restore orchestration + exports + 8 targeted tests written.
- [x] Static/public-import/diff gate PASS.
- [~] Targeted pytest RUNNING: PTY `pty_0855d1ea5bbec2d65ce8aa80e96ef6154dcc`, PID `122212`, JUnit `.tmp/imp082-targeted.xml`.
- [ ] On PASS: exact-head review -> affected regression -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-082 TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-082 EXACT-HEAD TARGETED PASS — 2026-10-12
- [x] Initial targeted 8/8 PASS historical evidence.
- [x] Exact-head replay/security hardening applied.
- [x] Static/public-import/diff gate PASS after hardening.
- [x] Exact-head targeted revalidation PASS: 8/8, 0 failures/errors/skips, PTY exit 0; JUnit `.tmp/imp082-review-targeted.xml`.
- [ ] Exact-head review -> affected owner regression -> broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "EXACT-HEAD REVIEW -> AFFECTED OWNER REGRESSION; DO NOT RERUN TARGETED"


## IMP-082 FINAL EXACT-HEAD TARGETED PASS — 2026-10-12
- [x] Final review hardening: Windows-safe backup IDs + mandatory canonical migration history.
- [x] Static/public-import/diff gate PASS.
- [x] Final targeted PASS: 10/10, 0 failures/errors/skips, PTY exit 0; JUnit `.tmp/imp082-final-targeted.xml`.
- [ ] Affected owner regression: persistence + GenerationJob + artifact lifecycle only; targeted excluded.
- [ ] Broader valid Windows -> Frozen guard -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN AFFECTED OWNER REGRESSION ONLY; DO NOT RERUN TARGETED"


## IMP-082 AFFECTED REGRESSION RUNNING — 2026-10-12
- [x] Final targeted 10/10 PASS locked; excluded from affected run.
- [~] Affected owner regression RUNNING: PTY `pty_83293ff6e07a97cfdbf77755e15d954cb9b7`, PID `129192`.
- Scope: persistence + GenerationJob + artifact lifecycle owner tests only; JUnit `.tmp/imp082-affected.xml`.
- [ ] Broader valid Windows -> Frozen guard -> evidence/Git lifecycle after affected final PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-082 AFFECTED REGRESSION PASS — 2026-10-12
- [x] Final targeted checkpoint = 10/10 PASS; do not rerun.
- [x] Affected owner regression PASS: `.tmp/imp082-affected.xml` = 43 tests / 0 failures / 0 errors / 0 skipped; PID `129192` absent after completion.
- [ ] Broader valid Windows regression excluding targeted + affected owner files; preserve known Windows exclusions.
- [ ] Frozen Master guard -> evidence -> Git lifecycle.
NEXT_EXACT_ACTION = "ANTI-DUPLICATE GUARD -> RUN IMP-082 BROADER VALID WINDOWS REGRESSION; DO NOT RERUN TARGETED/AFFECTED"


## IMP-082 BROADER VALID WINDOWS REGRESSION RUNNING — 2026-10-12
- [x] Targeted final 10/10 PASS retained; do not rerun.
- [x] Affected owner regression 43/43 PASS retained; do not rerun.
- [~] Broader valid Windows regression RUNNING under PTY `pty_b7862ed163bddc535664c19875199bce7c36`, PID `114276`.
- Scope excludes IMP-082 targeted + persistence + generation_job + artifact_lifecycle + `test_setup.py` + `test_video_reviewer.py`; historical POSIX deselections retained; `PYTHONUTF8=1`.
- [ ] Finalize `.tmp/imp082-broader-valid.xml` from final JUnit/exit only.
- [ ] Frozen Master guard only after broader PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-082 BROADER PTY/JUNIT; DO NOT RESTART"


## IMP-082 BROADER VALID WINDOWS REGRESSION PASS — 2026-10-12
- [x] Targeted final checkpoint 10/10 PASS retained; do not rerun.
- [x] Affected owner regression 43/43 PASS retained; do not rerun.
- [x] Broader valid Windows regression PASS: `.tmp/imp082-broader-valid.xml` = 783 tests / 0 failures / 0 errors / 0 skipped; PID `114276` absent after completion.
- [ ] Frozen Master guard -> final static/review -> evidence/Git lifecycle.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT IMP-082 WORKTREE; DO NOT RERUN TARGETED/AFFECTED/BROADER"


## IMP-082 FROZEN MASTER GUARD PASS — 2026-10-12
- [x] Targeted final 10/10 PASS retained.
- [x] Affected owner regression 43/43 PASS retained.
- [x] Broader valid Windows regression 783/783 PASS retained.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [ ] Final static/review -> evidence -> Git lifecycle.
NEXT_EXACT_ACTION = "FINAL STATIC/IMPORT/DIFF REVIEW -> EVIDENCE -> SIDE-EFFECT GUARD -> GIT LIFECYCLE"


## IMP-082 LOCAL VERIFIED / SIDE-EFFECT GUARD PASS — 2026-10-12
- [x] Targeted 10/10 PASS.
- [x] Affected owner regression 43/43 PASS.
- [x] Broader valid Windows regression 783/783 PASS.
- [x] Frozen Master guard PASS; final static/import/diff review PASS.
- [x] Evidence created: `evidence/tests/IMP-082_BACKUP_RESTORE_MIGRATION_SAFETY_EVIDENCE.md`.
- [x] Side-effect guard: no existing commit/remote branch/PR; staged index empty; `.tmp` untracked.
- [ ] Stage exact 7-file scope -> verify -> commit -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "STAGE EXACT 7-FILE IMP-082 SCOPE EXCLUDING .tmp -> VERIFY INDEX -> COMMIT"


## IMP-082 FEATURE COMMIT CREATED — 2026-10-12
- [x] Feature commit `2df68c0821b95123d5940d6d81a44b2007488e26` created.
- [x] Worktree after feature commit only `.tmp/` untracked.
- [ ] Governance-only exact-SHA sync commit -> side-effect guard -> push/PR/CI/review/merge/main verify.
NEXT_EXACT_ACTION = "GOVERNANCE-ONLY SYNC EXACT FEATURE SHA IN 3 STATE FILES -> COMMIT STATE-ONLY -> SIDE-EFFECT GUARD -> PUSH/PR"


## IMP-082 POST-MERGE TARGETED RUNNING — 2026-10-12
- [x] PR #88 merged at exact main SHA `71e52c740274db7c537377e7bde9fab42b79db24`.
- [~] Push-main CI `38227957664` RUNNING on exact merge SHA.
- [~] Post-merge targeted RUNNING: PTY `pty_34aedc32d392eb3ebd3bbb4d1ef9d19df483`, PID `133220`, JUnit `.tmp/imp082-main-targeted.xml`.
- [ ] Affected owner main regression -> Frozen guard after targeted PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN TARGETED PTY/JUNIT; DO NOT RESTART"


## IMP-082 POST-MERGE TARGETED PASS — 2026-10-12
- [x] Main targeted PASS: `.tmp/imp082-main-targeted.xml` = 10 tests / 0 failures / 0 errors / 0 skipped; PTY exit 0.
- [~] Push-main CI `38227957664` still RUNNING; Frozen guard PASS in both matrix jobs.
- [ ] Run affected owner regression only; targeted locked.
- [ ] Frozen Master guard after affected PASS.
NEXT_EXACT_ACTION = "RUN POST-MERGE AFFECTED OWNER REGRESSION ONLY; DO NOT RERUN TARGETED"


## IMP-082 POST-MERGE AFFECTED RUNNING — 2026-10-12
- [x] Main targeted 10/10 PASS locked; do not rerun.
- [~] Affected owner regression RUNNING: PTY `pty_8ceaf5366c867b9bd3e5d408444ffcbb56e9`, PID `122776`, JUnit `.tmp/imp082-main-affected.xml`.
- [~] Push-main CI `38227957664` RUNNING on exact main SHA.
- [ ] Frozen Master guard after affected PASS.
NEXT_EXACT_ACTION = "MONITOR EXISTING MAIN AFFECTED PTY/JUNIT; DO NOT RESTART"


## IMP-082 POST-MERGE AFFECTED PASS — 2026-10-12
- [x] Main targeted 10/10 PASS locked; do not rerun.
- [x] Affected owner regression PASS: `.tmp/imp082-main-affected.xml` = 43 tests / 0 failures / 0 errors / 0 skipped; PID `122776` absent after completion.
- [x] Push-main CI `38227957664` COMPLETED/SUCCESS on exact main SHA; Python 3.10 + 3.13 PASS.
- [ ] Frozen Master guard on exact main SHA.
NEXT_EXACT_ACTION = "RUN FROZEN MASTER GUARD ON EXACT MAIN SHA; DO NOT RERUN TARGETED/AFFECTED/CI"


## IMP-082 MAIN VERIFIED — 2026-10-12
- [x] Main targeted 10/10 PASS.
- [x] Main affected owner regression 43/43 PASS.
- [x] Push-main CI `38227957664` SUCCESS on exact main SHA `71e52c740274db7c537377e7bde9fab42b79db24`.
- [x] Frozen Master guard PASS; semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [x] Feature MAIN VERIFIED.
- [ ] Governance-only state sync lifecycle.
NEXT_EXACT_ACTION = "GOVERNANCE-ONLY SYNC BRANCH/COMMIT/PR; DO NOT RERUN TARGETED/AFFECTED/CI/FROZEN GUARD"


## TERMINAL QUEUE CHECKPOINT — 2026-10-12
- [x] IMP-082 governance merged to main SHA `4f1267010522b9451a88af6f32fdb4fd5b203c11`.
- [x] Governance push-main CI `38238675686` COMPLETED/SUCCESS; Python 3.10 + 3.13 PASS; Frozen baseline PASS.
- [x] No open PR remains.
- [x] No `IMP-083+` task is defined; IMP-082 is the last queue task.
- [x] ALL CURRENTLY DEFINED VALID TASKS DONE / MAIN VERIFIED.
- Terminal-sync rule: do not create another governance PR solely to record this governance CI result; avoid infinite self-referential governance loop.
NEXT_EXACT_ACTION = "NONE — QUEUE EXHAUSTED; RE-CHECK REPO/GIT/RUNTIME ONLY WHEN A NEW VALID TASK IS ADDED"


## FINAL TERMINAL STATE - 2026-10-12
- [x] IMP-082 governance main SHA `4f1267010522b9451a88af6f32fdb4fd5b203c11` verified.
- [x] Governance push-main CI `38238675686` COMPLETED/SUCCESS; Python 3.10 + 3.13 PASS.
- [x] No open PR remains.
- [x] No IMP-083+ task exists in the current queue.
- [x] ALL CURRENTLY DEFINED VALID TASKS DONE / MAIN VERIFIED.
- terminal_sync: local state checkpoint only; do not create a self-referential governance PR solely to record this final CI result.
NEXT_EXACT_ACTION = "NONE. QUEUE EXHAUSTED. ON FUTURE RESUME, RE-CHECK REPO/GIT/RUNTIME AND PROCEED ONLY IF A NEW VALID TASK EXISTS."


## QUEUE REOPENED / IMP-100 CLAIMED — 2026-10-12
- [x] User requested IMP-083, but authoritative task decomposition defines no IMP-083–099.
- [x] Correct next defined task is SYSTEM ACCEPTANCE LANE `IMP-100 — Full Contract Regression`.
- [x] Global execution law §13A added to govern queue-exhaustion/new-task admission without inventing task IDs/scopes.
- [x] Hard dependencies verified MAIN VERIFIED: IMP-006, IMP-013, IMP-028, IMP-033, IMP-042, IMP-055, IMP-064, IMP-073, IMP-082.
- [x] Duplicate guard: no pre-existing IMP-100 local/remote branch or PR.
- [x] Claimed branch `chatgpt/IMP-100-full-contract-regression` from exact main `4f1267010522b9451a88af6f32fdb4fd5b203c11`.
- [ ] Audit provider-neutral unit/contract/architecture test surfaces and lock one durable regression command.
- [ ] Run IMP-100 Full Contract Regression once; zero blocking contract failures required.
- [ ] Record durable JUnit/evidence -> Frozen guard if required by repo workflow -> Git lifecycle/main verification.
NEXT_EXACT_ACTION = "AUDIT TEST/CONTRACT/ARCHITECTURE COMMAND SURFACES -> LOCK IMP-100 FULL CONTRACT REGRESSION COMMAND -> ANTI-DUPLICATE GUARD -> RUN ONCE WITH DURABLE JUNIT/EVIDENCE"


## IMP-100 FULL CONTRACT REGRESSION RUNNING — 2026-10-12
- [x] Test-surface audit locked: local Windows-valid provider-neutral `tests/unit` envelope; PR CI will run full `tests/unit` on Ubuntu Python 3.10 + 3.13.
- [~] Regression RUNNING under PTY `pty_5c13226282aaf615d2a68d9f5ebcc9a5638e`, root PID `139328`.
- JUnit `.tmp/imp100-contract-regression.xml`; basetemp `.tmp/pytest-imp100-contract-regression`.
- [ ] Finalize PASS/FAIL from PTY exit + final JUnit only; do not restart.
NEXT_EXACT_ACTION = "MONITOR EXISTING IMP-100 PTY/JUNIT; DO NOT RESTART"


## IMP-100 LOCAL FULL CONTRACT REGRESSION JUNIT PASS — 2026-10-13
- [x] Complete durable JUnit `.tmp/imp100-contract-regression.xml`: 836 tests / 0 failures / 0 errors / 0 skipped.
- [x] No matching pytest/IMP-100 process remains; do not restart the completed regression.
- [~] Original PTY expired/unknown; exit code unavailable. This limitation is recorded, not guessed.
- [x] `git diff --check` exit 0; no remote IMP-100 branch existed at last check; `.tmp/` must not be staged.
- [ ] Run Frozen Master guard on current IMP-100 worktree.
- [ ] Exact-worktree static/import/diff review; create/verify tracked evidence.
- [ ] Side-effect guard -> stage exact intended files -> commit -> push/PR -> full Ubuntu Python 3.10 + 3.13 CI -> review/merge if required -> verify main.
NEXT_EXACT_ACTION = "RUN python tools/frozen_master_guard.py ON CURRENT IMP-100 WORKTREE; DO NOT RERUN 836-TEST REGRESSION; THEN EXACT-WORKTREE STATIC/IMPORT/DIFF REVIEW AND GIT LIFECYCLE"


## IMP-100 FROZEN MASTER GUARD PASS — 2026-10-13
- [x] Frozen Master guard exit 0 / PASS on the current IMP-100 worktree.
- [x] Canonical Master semantic SHA256 unchanged: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- [x] Retain local regression JUnit 836/836; do not rerun it.
- [ ] Final static/import/diff review -> verify tracked evidence/state -> side-effect guard -> stage exact intended files.
NEXT_EXACT_ACTION = "FINAL STATIC/IMPORT/DIFF REVIEW -> VERIFY TRACKED EVIDENCE/STATE -> SIDE-EFFECT GUARD -> STAGE ONLY INTENDED FILES"


## IMP-100 EXACT-WORKTREE REVIEW PASS — 2026-10-13
- [x] Frozen Master guard PASS.
- [x] Final static/diff review PASS; `git diff --check` exit 0; no source/test diff.
- [x] Side-effect guard: no existing IMP-100 commit, remote branch or PR found.
- [x] Exact intended scope locked to five files; exclude all `.tmp/` runtime/test outputs.
- [ ] Verify empty index -> stage exact five files -> verify staged diff/diff-check -> commit.
NEXT_EXACT_ACTION = "VERIFY EMPTY INDEX -> STAGE EXACT 5 INTENDED FILES EXCLUDING .tmp -> VERIFY STAGED DIFF/DIFF-CHECK -> COMMIT"


## IMP-100 STALE GIT LOCK RECOVERY — 2026-10-13
- [x] Verified zero-byte `.git/index.lock` was stale (age > 10 minutes), index older, and no live Git process existed.
- [x] Removed only that stale lock; worktree preserved and index still empty.
- [ ] Stage exact five intended files excluding `.tmp/`, verify staged diff and diff-check, then commit.
NEXT_EXACT_ACTION = "STAGE EXACT 5 INTENDED FILES EXCLUDING .tmp -> VERIFY STAGED DIFF/DIFF-CHECK -> COMMIT"


## IMP-100 ACCEPTANCE EVIDENCE COMMITTED — 2026-10-13
- [x] Local provider-neutral regression durable JUnit: 836 tests / 0 failures / 0 errors / 0 skipped; do not rerun this completed stage.
- [x] Frozen Master guard PASS (exit 0; canonical semantic SHA256 unchanged).
- [x] Exact-worktree review and `git diff --check` PASS.
- [x] Five intended files staged and committed as `4cd1a51` (`test(acceptance): record IMP-100 contract regression evidence`); `.tmp/` excluded.
- [ ] Re-check current remote branch and PR state, push branch once, verify remote HEAD, create PR only if absent.
- [ ] Obtain full Ubuntu `tests/unit` CI on Python 3.10 and 3.13 without exclusions; inspect exact PR-head checks.
- [ ] Review, merge only after required gates pass, checkout/pull main, verify main and sync state.
NEXT_EXACT_ACTION = "RECHECK GIT/REMOTE/PR -> PUSH IMP-100 BRANCH ONCE -> VERIFY REMOTE HEAD -> CREATE PR ONLY IF NONE EXISTS -> MONITOR FULL UBUNTU PYTHON 3.10 + 3.13 CI"


## IMP-100 BRANCH PUSH VERIFIED — 2026-10-13
- [x] Push succeeded; `origin/chatgpt/IMP-100-full-contract-regression` created and upstream configured.
- [x] Pushed head at this checkpoint: `ae84835e547c3a57e389a1061b1c6d2ec0a35f1e`.
- [ ] Sync this push checkpoint, then re-check remote head and all PR states.
- [ ] Create IMP-100 PR only if absent; capture exact PR number/head.
- [ ] Monitor full Ubuntu `tests/unit` CI on Python 3.10 and 3.13 at the exact PR head.
NEXT_EXACT_ACTION = "SYNC PUSH CHECKPOINT -> RECHECK REMOTE HEAD AND ALL PR STATES -> CREATE IMP-100 PR ONLY IF ABSENT -> CAPTURE PR NUMBER/HEAD -> MONITOR EXACT-HEAD CI"


## IMP-100 PULL REQUEST OPEN — 2026-10-13
- [x] PR #90 created: https://github.com/nguyenkhactang922-bot/flowkit/pull/90.
- [x] Base main SHA at PR creation: `4f1267010522b9451a88af6f32fdb4fd5b203c11`.
- [x] Initial PR head: `d554d1a0a53ffb81081473762ad57262857ebd46`; 5 changed files.
- [ ] Sync PR checkpoint and push state update; then capture the final exact PR head.
- [ ] Review exact PR diff and monitor full Ubuntu `tests/unit` CI on Python 3.10 + 3.13 without exclusions.
- [ ] Merge only after required checks pass and review is clear; verify main before marking MAIN VERIFIED.
NEXT_EXACT_ACTION = "SYNC PR CHECKPOINT -> PUSH STATE UPDATE -> FETCH PR #90 FINAL HEAD -> REVIEW EXACT DIFF AND REQUIRED CHECKS -> WAIT/MONITOR CI WITHOUT RERUNNING LOCAL 836-TEST STAGE"


## IMP-100 PR DIFF REVIEW / CI MONITORING — 2026-10-13
- [x] PR #90 open; base main `4f1267010522b9451a88af6f32fdb4fd5b203c11`.
- [x] Exact 5-file PR diff reviewed; governance/state/evidence only, no source/test code changes.
- [x] No review submissions or inline review threads found at inspection.
- [~] Workflow `tests` run `38347480120` was pending on pre-sync head `2ca7d5d4dd61b4f6588e0d9901514806ca951634`; this state-sync push may create a new exact-head run.
- [ ] Push this state sync, fetch the new PR head, and monitor required CI jobs on that exact SHA.
- [ ] Do not merge until all required checks pass and review is clear; do not rerun the completed local 836-test regression.
NEXT_EXACT_ACTION = "COMMIT/PUSH THIS PR STATE SYNC -> FETCH PR #90 CURRENT HEAD -> FETCH WORKFLOW RUNS AND JOBS FOR THAT EXACT SHA -> MONITOR UNTIL ALL REQUIRED CHECKS COMPLETE; DO NOT MERGE OR RERUN LOCAL JUNIT"



## IMP-100 MAIN VERIFIED / IMP-101 CLAIMED — 2026-10-13
- [x] IMP-100 PR #90 merged at main SHA `0c0d977edfc0edfa374d9bc009631516700dab34`.
- [x] Exact PR-head CI `38347617423` SUCCESS: Python 3.10 + 3.13; frozen baseline and unit tests PASS.
- [x] Push-main CI `38348297682` SUCCESS on exact merge SHA: Python 3.10 + 3.13; frozen baseline and unit tests PASS.
- [x] IMP-100 is MAIN VERIFIED; its 836-test local JUnit stage is retained and not rerun.
- [x] Anti-duplicate guard: no local/remote `chatgpt/IMP-101-migration-dry-run` branch and no existing IMP-101 PR; new task branch created from exact main SHA.
- [x] Hard dependencies IMP-080, IMP-081, IMP-082, IMP-100 verified present on main.
- [~] IMP-101 Migration Dry Run CLAIMED / ANALYZE on `chatgpt/IMP-101-migration-dry-run`.
- [x] Runtime check: no local `flow_agent.db` and no listener on port 8100; do not represent a synthetic fixture run as live-user migration.
- [ ] Inspect legacy schema/import/backup contracts; implement read-only source scan, deterministic resumable migration manifest, isolated canonical staging DB, privacy-safe durable report.
- [ ] Add integration tests using a real temporary SQLite DB populated from the repository legacy schema; prove no narrative inference, idempotent restart/replay, retained evidence, and source DB remains unchanged.
NEXT_EXACT_ACTION = "INSPECT IMP-080/081/082 CONTRACTS AND LEGACY DB SCHEMA -> DESIGN READ-ONLY, RESTART-SAFE IMP-101 DRY-RUN RUNNER/REPORT -> ADD REAL SQLITE FIXTURE INTEGRATION TESTS; DO NOT MUTATE SOURCE DB OR CALL LIVE PROVIDERS"



## IMP-101 TARGETED CHECKPOINT 1
- [x] New module syntax/import succeeded under isolated Python 3.13.
- [~] Targeted SQLite migration dry-run tests: 2/3 PASS; one assertion mismatch in diagnostic ordering, not in fail-closed behavior.
- [x] Source-change resume test confirmed the runner refuses to mix changed source snapshots.
- [ ] Report source fingerprint mismatch before derived run-id mismatch for clearer diagnosis.
- [ ] Rerun only the IMP-101 targeted test file after that fix; do not rerun IMP-100 stages.
NEXT_EXACT_ACTION = "REORDER MANIFEST IDENTITY VALIDATION TO REPORT SOURCE_FINGERPRINT FIRST -> RERUN ONLY tests/unit/test_studio_migration_dry_run.py"



## IMP-101 TARGETED PASS — 2026-10-13
- [x] New IMP-101 SQLite migration dry-run tests: 3/3 PASS; exit 0.
- [x] Durable JUnit: `.tmp/imp101-targeted-rerun.xml`; prior failed JUnit `.tmp/imp101-targeted.xml` retained, not overwritten.
- [x] Source DB remained byte-identical during successful run.
- [x] Resume/replay is idempotent; changed source snapshot is rejected; raw story/prompt text is absent from mapping/report/staging output.
- [x] No canonical StoryCore/SceneDramaticBeat/FullShotSpec/ShotIR targets are created by dry-run.
- [ ] Review code/diff; run affected legacy import, operational projection, backup/restore and persistence regressions.
- [ ] Capture durable evidence and frozen guard; then proceed to Git lifecycle.
NEXT_EXACT_ACTION = "REVIEW IMP-101 DIFF AND MIGRATION CONTRACT -> RUN AFFECTED LEGACY-IMPORT/PROJECTION/BACKUP-RESTORE REGRESSION ONLY -> RECORD DURABLE IMP-101 EVIDENCE"



## IMP-101 TARGETED CHECKPOINT 2 — 2026-10-13
- [x] Report now exposes mapping counts by source kind and source table without exposing source row IDs.
- [~] Revised targeted run: 2 passed; 1 assertion mismatch because project-table count includes its media-lineage record.
- [ ] Adjust test to assert at least one project-table mapping and exact one PROJECT-kind mapping.
- [ ] Rerun only IMP-101 targeted test file; preserve prior JUnit files.
NEXT_EXACT_ACTION = "FIX IMP-101 TABLE-COUNT ASSERTION TO ACCOUNT FOR MEDIA LINEAGE RECORDS -> RERUN ONLY tests/unit/test_studio_migration_dry_run.py"



## IMP-101 TARGETED PASS — 2026-10-13 (report contract)
- [x] IMP-101 targeted tests: 3/3 PASS; final JUnit `.tmp/imp101-targeted-final2.xml`.
- [x] Report includes mapping counts by source kind/table; no source row IDs or raw story/prompt/media values.
- [x] Previous failed-attempt JUnit artifacts remain preserved; final passing JUnit is separate.
- [ ] Run affected existing legacy-import, operational-scene projection, backup/restore, and persistence regression tests only.
- [ ] Record evidence, run frozen guard for the changed worktree, review diff, then Git lifecycle.
NEXT_EXACT_ACTION = "RUN AFFECTED EXISTING REGRESSION: test_studio_legacy_import.py + test_studio_operational_scene_projection.py + test_studio_backup_restore.py + test_studio_persistence.py; DO NOT RERUN THE IMP-101 TARGETED STAGE OR IMP-100 FULL REGRESSION"



## IMP-101 AFFECTED REGRESSION INTERRUPTED — 2026-10-13
- [x] Immediate process check after tool failure: no affected pytest/uv process remains.
- [x] No complete affected JUnit exists; partial basetemp artifacts are not PASS evidence.
- [~] Affected regression command classified INTERRUPTED.
- [x] IMP-101 targeted 3/3 PASS checkpoint preserved.
- [ ] Run existing affected test files one at a time, each with independent JUnit/basetemp; do not rerun IMP-100 full contract regression.
NEXT_EXACT_ACTION = "RUN tests/unit/test_studio_legacy_import.py ALONE WITH NEW JUNIT/BASETEMP; THEN RUN REMAINING AFFECTED FILES ONE AT A TIME"



## IMP-101 AFFECTED CHECKPOINT — LEGACY IMPORT PASS
- [x] Existing `test_studio_legacy_import.py`: 9/9 PASS; JUnit `.tmp/imp101-legacy-import.xml`.
- [ ] Run `test_studio_operational_scene_projection.py` independently with its own JUnit/basetemp.
NEXT_EXACT_ACTION = "RUN tests/unit/test_studio_operational_scene_projection.py ALONE WITH NEW JUNIT/BASETEMP"



## IMP-101 AFFECTED CHECKPOINT — OPERATIONAL PROJECTION PASS
- [x] Existing `test_studio_operational_scene_projection.py`: 7/7 PASS; JUnit `.tmp/imp101-projection.xml`.
- [x] Existing `test_studio_legacy_import.py`: 9/9 PASS; JUnit `.tmp/imp101-legacy-import.xml`.
- [x] New IMP-101 targeted: 3/3 PASS; JUnit `.tmp/imp101-targeted-final2.xml`.
- [ ] Run `test_studio_backup_restore.py` independently with its own JUnit/basetemp.
NEXT_EXACT_ACTION = "RUN tests/unit/test_studio_backup_restore.py ALONE WITH NEW JUNIT/BASETEMP"



## IMP-101 AFFECTED CHECKPOINT — BACKUP / RESTORE PASS
- [x] Existing `test_studio_backup_restore.py`: 10/10 PASS; JUnit `.tmp/imp101-backup-restore.xml`.
- [x] Existing legacy import: 9/9 PASS; operational projection: 7/7 PASS; new IMP-101 targeted: 3/3 PASS.
- [ ] Run `test_studio_persistence.py` independently with its own JUnit/basetemp.
NEXT_EXACT_ACTION = "RUN tests/unit/test_studio_persistence.py ALONE WITH NEW JUNIT/BASETEMP"



## IMP-101 AFFECTED CHECKPOINT — PERSISTENCE PASS — 2026-10-13
- [x] `tests/unit/test_studio_persistence.py`: 12/12 PASS, 0 failures/errors/skips; JUnit `.tmp/imp101-persistence.xml`.
- [x] Affected regression checkpoints are all complete: targeted 3/3, legacy import 9/9, operational projection 7/7, backup/restore 10/10, persistence 12/12.
- [ ] Review IMP-101 migration contract, diff, and failure paths.
- [ ] Run frozen Master guard and static/syntax/diff-check on the current worktree.
- [ ] Record evidence, stage only intentional source/test/state files (never `.tmp/`), commit and follow required push/PR/review/merge/main-verification lifecycle.
NEXT_EXACT_ACTION = "REVIEW IMP-101 MIGRATION CONTRACT/DIFF AND FAILURE PATHS -> RUN FROZEN MASTER GUARD ON CURRENT WORKTREE -> RUN STATIC/SYNTAX/DIFF-CHECK -> SYNC EVIDENCE AND PREPARE EXACT-FILE GIT LIFECYCLE; DO NOT RERUN ANY PASS TEST FILE"



## IMP-101 CONTRACT REVIEW / FROZEN GUARD PASS — 2026-10-13
- [x] Reviewed IMP-101 acceptance and the migration runner against the IMP-080 mapping-only boundary; no silent narrative inference or canonical creative targets are introduced.
- [x] Targeted migration dry-run tests: 3/3 PASS; JUnit `.tmp/imp101-targeted-final2.xml`.
- [x] Affected regression: legacy import 9/9, operational projection 7/7, backup/restore 10/10, persistence JUnit 12/12. Persistence process exit metadata is unavailable and is not inferred from JUnit.
- [x] Frozen Master guard PASS (exit 0); Python compileall PASS (exit 0); `git diff --check` PASS (exit 0).
- [x] Durable evidence file created: `evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md`.
- [ ] Recheck empty index and exact worktree; stage only the seven intended source/test/fixture/evidence/state files; exclude `.tmp/`.
- [ ] Inspect staged diff and `git diff --cached --check`; commit only after the exact scope is verified.
- [ ] Push once, verify remote head, create PR only if absent, review exact PR head and required CI/review gates, merge only after all required gates pass, then verify main.
NEXT_EXACT_ACTION = "RECHECK EMPTY INDEX AND EXACT WORKTREE -> STAGE ONLY THE SEVEN INTENDED IMP-101 FILES (EXCLUDE .tmp) -> REVIEW STAGED DIFF AND DIFF-CHECK -> COMMIT"



## IMP-101 STAGED DIFF REVIEW PASS — 2026-10-13
- [x] Exact staged allowlist contains only seven intended files: migration runner, targeted test, synthetic fixture, durable evidence, and three governance state files.
- [x] Staged diff reviewed; 7 files / 1,679 insertions; `git diff --cached --check` exit 0.
- [x] Local `.tmp/` artifacts are not staged.
- [ ] Recheck the exact staged set and commit IMP-101 implementation/evidence/state.
- [ ] Push once; verify remote head; create PR only if absent; wait for exact-head CI and required review; merge only after gates pass; verify main.
NEXT_EXACT_ACTION = "RECHECK EXACT SEVEN-FILE STAGED SET AND STAGED DIFF-CHECK -> COMMIT IMP-101 IMPLEMENTATION/EVIDENCE/STATE"



## IMP-101 IMPLEMENTATION COMMIT VERIFIED — 2026-10-13
- [x] Implementation commit `ff332976a0f396c92845f178c325b8d1c381b55b` created on `chatgpt/IMP-101-migration-dry-run` from `0c0d977edfc0edfa374d9bc009631516700dab34`.
- [x] Commit contains exactly seven intended files; commit diff-check PASS; `.tmp/` excluded.
- [x] Worktree after commit contains only untracked local `.tmp/` test/runtime artifacts.
- [ ] Commit the post-commit state/evidence sync, then recheck remote branch/PR and push once.
- [ ] Verify remote HEAD, create PR only if absent, inspect exact-head CI and review, merge only after required gates pass, then verify main.
NEXT_EXACT_ACTION = "APPEND/VERIFY POST-COMMIT STATE AND EVIDENCE CHECKPOINT -> COMMIT STATE SYNC -> RECHECK REMOTE BRANCH/PR -> PUSH BRANCH ONCE -> VERIFY REMOTE HEAD -> CREATE PR ONLY IF ABSENT"



## IMP-101 BRANCH PUSH VERIFIED — 2026-10-13
- [x] Push completed with exit 0; upstream configured.
- [x] Exact remote branch head verified by `git ls-remote`: `7f1186634c621050e5d114d17cef2feb50dfc393`, equal to local HEAD.
- [x] GitHub branch search finds the task branch; PR search is empty, so no duplicate PR exists.
- [ ] Commit this push checkpoint state/evidence sync and push that new state head once.
- [ ] Verify remote HEAD, recheck PR search, create PR only if absent, inspect exact-head CI/review, merge only after gates pass, and verify main.
NEXT_EXACT_ACTION = "COMMIT PUSH-CHECKPOINT STATE/EVIDENCE SYNC -> PUSH THE NEW STATE HEAD ONCE -> VERIFY REMOTE HEAD -> RECHECK PR SEARCH -> CREATE PR ONLY IF ABSENT"



## IMP-101 PR CREATED — 2026-10-13
- [x] PR #91 created only after remote branch and duplicate-PR checks: https://github.com/nguyenkhactang922-bot/flowkit/pull/91.
- [x] PR head at creation: `4d93ee5bf922cf7802d68e75d51973921a8fb137`; base main SHA `0c0d977edfc0edfa374d9bc009631516700dab34`.
- [ ] Commit and push this PR-state sync, then fetch the new exact PR head and its CI runs/jobs.
- [ ] Review exact PR head and required gates; do not merge while checks/review are pending; verify main after merge.
NEXT_EXACT_ACTION = "COMMIT PR-CREATION STATE/EVIDENCE SYNC -> PUSH STATE HEAD -> FETCH PR #91 CURRENT HEAD AND WORKFLOW RUNS/JOBS -> REVIEW EXACT HEAD/REQUIRED CHECKS; DO NOT MERGE WHILE GATES ARE PENDING"



## IMP-101 PR HEAD / CI CHECKPOINT — 2026-10-13
- [x] PR #91 remains open and unmerged; current exact head at inspection: `cf1a5835c12ee54a4c8ddb4d44ff03e96f410158`.
- [x] Workflow run `38368157340` for that head is pending; no combined statuses, review submissions, or inline review threads were returned at inspection.
- [ ] Commit/push this state sync; it will change PR head, so fetch and inspect CI for the new exact SHA.
- [ ] Review the exact PR diff and wait for required checks/review; do not merge while gates are pending.
NEXT_EXACT_ACTION = "COMMIT/PUSH PR HEAD + CI PENDING STATE SYNC -> FETCH PR #91 NEW CURRENT HEAD -> FETCH WORKFLOW RUNS/JOBS FOR THAT EXACT SHA -> REVIEW EXACT PR DIFF AND MONITOR UNTIL REQUIRED GATES COMPLETE"



## IMP-101 REVIEW GATE FAIL — MANIFEST INTEGRITY GAP — 2026-10-13
- [x] Reviewed exact PR head `21fba3246956cf7f440aa67f49f027bb222f3f26`; PR #91 remains open/unmerged.
- [x] Identified a manifest corruption fail-open risk: missing validation of total source record count, integrity/FK summary fields, complete checkpoint-set coverage/uniqueness, and artifact/source-key binding.
- [x] Preserve prior PASS checkpoints, but do not merge based on them while this review finding remains open.
- [ ] Harden manifest identity/checkpoint validation and artifact source-key validation; add targeted negative tests.
- [ ] Rerun only `tests/unit/test_studio_migration_dry_run.py` after the fix; then diff-check and push the fix.
- [ ] Verify all required CI/review gates on the new exact PR head before merge.
NEXT_EXACT_ACTION = "HARDEN IMP-101 MANIFEST IDENTITY/CHECKPOINT SET AND ARTIFACT SOURCE-KEY VALIDATION -> ADD NEGATIVE TESTS FOR TAMPERED COMPLETE MANIFEST/REBOUND MAPPING -> RERUN ONLY tests/unit/test_studio_migration_dry_run.py -> DIFF-CHECK AND PUSH FIX; THEN VERIFY CI ON THE NEW EXACT PR HEAD"



## IMP-101 MANIFEST INTEGRITY HARDENING — TARGETED PASS — 2026-10-13
- [x] Fixed manifest/source identity validation: bind integrity result, foreign-key violation count, context-only tables, and total record count to the source snapshot.
- [x] Validate manifest checkpoint keys for source membership and uniqueness; COMPLETE manifests must cover the entire source key set.
- [x] Verify each persisted mapping artifact's actual source kind/table/ID hashes to the manifest checkpoint key.
- [x] Targeted migration tests after fix: **8/8 PASS**, JUnit `.tmp/imp101-manifest-hardening.xml`, exit 0, 0 failures/errors/skips.
- [x] Syntax compile and `git diff --check` PASS (exit 0); frozen Master unchanged, existing guard PASS retained.
- [ ] Stage only six intended changed files (migration runner, targeted tests, three state files, evidence); exclude `.tmp/`.
- [ ] Review staged diff, commit fix/state/evidence, push, then verify CI on the new exact PR #91 head.
NEXT_EXACT_ACTION = "VERIFY THE SIX-FILE FIX/STATE DIFF -> STAGE ONLY THE SIX INTENDED FILES (EXCLUDE .tmp) -> STAGED DIFF-CHECK -> COMMIT FIX + STATE/EVIDENCE -> PUSH AND VERIFY NEW PR HEAD/CI"



## IMP-101 MANIFEST HARDENING FIX COMMITTED — 2026-10-13
- [x] Fix commit `9ad0d6fec9d5a9fa1d933a3e2f296906a97c644b` created; commit diff-check PASS; `.tmp/` excluded.
- [x] Targeted manifest-hardening suite 8/8 PASS, exit 0; previous PASS checkpoints preserved.
- [ ] Commit this post-fix state/evidence sync, then push the new branch head once.
- [ ] Verify exact remote/PR head, update PR #91 validation text, fetch CI for the new SHA, review and wait for required gates; do not merge early.
NEXT_EXACT_ACTION = "COMMIT POST-FIX STATE/EVIDENCE SYNC -> RECHECK REMOTE STILL AT 21fba32 AND PR #91 OPEN -> PUSH NEW BRANCH HEAD ONCE -> VERIFY REMOTE/PR EXACT SHA -> FETCH CI RUNS/JOBS FOR THAT SHA"



## IMP-101 PRE-PUSH RESUME CHECK — 2026-10-13 16:08 +07
- Source-of-truth recheck: project root `E:\FlowKit-Studio-Upgrade`; Git root `E:/FlowKit-Studio-Upgrade`; branch `chatgpt/IMP-101-migration-dry-run`; local HEAD `9ad0d6fec9d5a9fa1d933a3e2f296906a97c644b` (`fix(studio): validate migration resume checkpoints`).
- Runtime: no active FlowKit pytest/build/frozen-guard process found. The only workspace PTY reported alive belongs to `E:\Tang-VPN-Tool-Studio`; it is unrelated and was not touched. Do not restart any IMP-101 test checkpoint.
- Latest targeted evidence `.tmp/imp101-manifest-hardening.xml`: 8 tests, 0 failures, 0 errors, 0 skipped; prior recorded process exit 0. Existing targeted/affected regression and frozen-guard PASS checkpoints remain preserved.
- Side-effect guard: remote branch is still at `21fba3246956cf7f440aa67f49f027bb222f3f26`; local fix commit is not pushed. PR #91 is OPEN, unmerged, base `main` at `0c0d977edfc0edfa374d9bc009631516700dab34`, PR head still `21fba3246956cf7f440aa67f49f027bb222f3f26`. No submitted reviews or inline review threads were found. Workflow run `38368452247` succeeded for the OLD head only; no workflow run exists yet for local fix SHA `9ad0d6f` because it is not pushed. Do not attribute old-head CI to the fix.
- Git scope before this state sync: the three governance files have a staged 32-line checkpoint; the evidence file has a matching unstaged 9-line checkpoint; `.tmp/` is untracked local runtime evidence and must remain excluded from Git.
- Current stage classification: implementation/fix checkpoint PASS; overall IMP-101 lifecycle is IN PROGRESS pending state-sync commit, push, exact-head CI/review, merge, and main verification. No blocker identified; merge is prohibited until new-head gates pass.
- NEXT_EXACT_ACTION = "STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md -> VERIFY EXACT FOUR-FILE STAGED SET AND git diff --cached --check -> COMMIT STATE/EVIDENCE SYNC -> RECHECK PR #91 OPEN AND REMOTE STILL AT 21fba324 -> PUSH CURRENT LOCAL BRANCH HEAD ONCE -> VERIFY REMOTE/PR EXACT SHA -> FETCH WORKFLOW RUNS/JOBS FOR THAT SHA -> REVIEW EXACT PR DIFF AND REQUIRED GATES; DO NOT MERGE WHILE CI/REVIEW IS PENDING"



## IMP-101 PUSH VERIFIED — 2026-10-13 16:09 +07
- Push completed with exit 0 from old remote `21fba3246956cf7f440aa67f49f027bb222f3f26` to local/remote HEAD `25cbb8386bac9ebaedb54f9c2c5ef0bce3a76bae`; local and `git ls-remote` SHA match. Worktree has no tracked changes; `.tmp/` remains untracked and excluded.
- GitHub PR #91 is still OPEN and unmerged; exact current head verified as `25cbb8386bac9ebaedb54f9c2c5ef0bce3a76bae`, base `main` at `0c0d977edfc0edfa374d9bc009631516700dab34`, mergeable=true at inspection. No submitted reviews or inline review threads were returned.
- Workflow run `38375082331` (`tests`) is IN_PROGRESS for SHA `25cbb8386bac9ebaedb54f9c2c5ef0bce3a76bae`. This checkpoint's required state/evidence sync will move the PR head; run `38375082331` must not be treated as validation of the next head. Fetch runs/jobs for the exact SHA after the state-sync push.
- No FlowKit local test/build process is running. All prior targeted/affected test PASS checkpoints remain preserved; do not rerun them merely to recover process metadata. Merge remains prohibited until exact-head CI and review gates pass.
- NEXT_EXACT_ACTION = "STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md -> VERIFY EXACT FOUR-FILE STAGED SET AND git diff --cached --check -> COMMIT PUSH-CHECKPOINT STATE/EVIDENCE -> RECHECK PR #91 AND REMOTE HEAD -> PUSH THE NEW STATE HEAD ONCE -> VERIFY EXACT PR SHA -> FETCH WORKFLOW RUNS/JOBS FOR THAT SHA -> REVIEW EXACT PR DIFF AND REQUIRED GATES; DO NOT MERGE WHILE CI/REVIEW IS PENDING"



## IMP-101 EXACT-HEAD REVIEW CHECKPOINT — 2026-10-13 16:10 +07
- PR #91 exact head `383ecdf62a89e57101b1a643bb81f599b1cb2e7d` was verified against GitHub; base `main` remains `0c0d977edfc0edfa374d9bc009631516700dab34`; PR remains OPEN/unmerged and mergeable=true at inspection.
- CI run `38375303187` (`tests`) is PENDING for exact head `383ecdf62a89e57101b1a643bb81f599b1cb2e7d`; its job list was empty while pending. This run will be stale once the following state-sync commit is pushed. Fetch the workflow run for the new exact SHA and do not infer PASS from the old run.
- Exact diff self-review PASS for the manifest hardening: source snapshot identity now includes integrity/FK/context/table/total fields; checkpoint entries are dicts, source-member keys, and unique; COMPLETE requires full source-key coverage; persisted mapping source kind/table/ID must hash to the checkpoint key; negative tests cover incomplete/rewritten totals, duplicate checkpoints, source-key rebinding, and tampered FK summary. No new issue found in this focused review. This is self-review only; GitHub currently has no submitted reviews or inline review threads, so any repository-required independent approval remains unverified.
- Local targeted JUnit `.tmp/imp101-manifest-hardening.xml` is 8/8 with 0 failures/errors/skips; recorded process exit 0. All earlier PASS checkpoints are retained; no test rerun is justified by stream loss.
- Latest push `383ecdf` was verified local=remote; worktree has only untracked `.tmp/` artifacts, excluded from Git. No FlowKit test/build process is active; the remaining PTY belongs to another repository and is untouched.
- NEXT_EXACT_ACTION = "STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md -> VERIFY EXACT FOUR-FILE STAGED SET AND git diff --cached --check -> COMMIT EXACT-HEAD REVIEW/CI-PENDING STATE SYNC -> RECHECK PR #91/REMOTE HEAD -> PUSH NEW STATE HEAD ONCE -> VERIFY NEW EXACT PR SHA -> FETCH WORKFLOW RUNS/JOBS AND REQUIRED STATUS FOR THAT SHA -> MONITOR UNTIL GATES COMPLETE; DO NOT MERGE WITHOUT REQUIRED CI/REVIEW PASS"



## IMP-101 EXACT-HEAD CI PASS — 2026-10-13
- Exact PR head `5973b75319f21f7b27a114e1755ef512159825fd` passed workflow `tests`, run `38375924080`, conclusion `success`. Both jobs `unit (3.10)` and `unit (3.13)` completed successfully; in each job, `Verify frozen Master baseline` and `Run unit tests` steps concluded `success`.
- PR #91 remained OPEN/unmerged at that exact head, base `main` SHA `0c0d977edfc0edfa374d9bc009631516700dab34`, mergeable=true at inspection. GitHub returned no review submissions or inline review threads; previous PR #90 was merged with no submitted reviews. Exact PR diff self-review found no remaining issue in the focused manifest-hardening change.
- PR body validation text still names run `38375924080` as in progress; update it after the next state-sync push to reflect that run as PASS and identify the new exact-head run accurately.
- This state sync will create a new commit and therefore move the PR head; run `38375924080` is PASS evidence only for SHA `5973b75319f21f7b27a114e1755ef512159825fd`, not the next SHA. Do not merge until CI is verified on the final exact PR head.
- Prior targeted 8/8 PASS and affected regression PASS checkpoints remain preserved; no local test rerun. Worktree had only untracked `.tmp/` runtime artifacts, excluded from Git; no FlowKit process is running.
- NEXT_EXACT_ACTION = "STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md -> VERIFY EXACT FOUR-FILE STAGED SET AND git diff --cached --check -> COMMIT CI-PASS STATE SYNC -> RECHECK PR #91 AND REMOTE HEAD -> PUSH NEW STATE HEAD ONCE -> VERIFY NEW EXACT PR SHA -> FETCH WORKFLOW RUNS/JOBS FOR THAT SHA -> UPDATE PR VALIDATION TEXT TO THE EXACT-HEAD RESULT -> MERGE ONLY IF FINAL CI AND ALL REQUIRED GATES PASS -> CHECKOUT/PULL MAIN AND VERIFY MAIN"



## IMP-101 MAIN VERIFIED / IMP-102 NEXT DEPENDENCY-READY — 2026-10-13

- [x] IMP-101 implementation/evidence commit and manifest-integrity hardening verified; targeted migration suite 8/8 PASS, previous affected regressions retained, frozen Master guard PASS.
- [x] PR #91 merged from exact head `c0e303c890fd5d07024f8281cf0002e691509064`.
- [x] PR-head CI run `38377111243` SUCCESS on exact PR head; Python 3.10 and 3.13 jobs PASS, including frozen Master guard and unit tests.
- [x] Merge SHA `2e3e4c6e4b5b8ceedd5cbb7ab2f0f11de4bb216f`; local `main` fast-forwarded to exact merge SHA and tree matched feature branch.
- [x] Main push CI run `38381133828` SUCCESS on exact merge SHA; Python 3.10 and 3.13 jobs PASS, including frozen Master guard and unit tests.
- [x] No local test or frozen-guard stage was rerun after its PASS evidence. Synthetic SQLite only; no live-user migration claim.
- [x] IMP-101 status = MAIN VERIFIED. Governance-only state sync is in progress.
- [x] Next task selected from authoritative decomposition: IMP-102 Failure / Recovery Fault Injection.
- [x] IMP-102 hard dependencies are verified MAIN VERIFIED: IMP-052, IMP-053, IMP-054, IMP-055, IMP-100.
- [x] Duplicate guard before claim: no local/remote feature branch and no PR for `chatgpt/IMP-102-failure-recovery-fault-injection`.
- [ ] Commit/push the exact four-file governance state/evidence sync, open PR only if absent, verify exact-head CI, merge after required gates, then verify governance merge on main.
- [ ] After governance main verification, create the IMP-102 feature branch from the exact updated main SHA, claim it in the state files, audit Frozen Master §§69–71 and current GenerationJob/Scheduler/Recovery/Artifact failure surfaces before code.
NEXT_EXACT_ACTION = "VERIFY EXACT FOUR-FILE GOVERNANCE STATE/EVIDENCE DIFF -> STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md -> git diff --cached --check -> COMMIT GOVERNANCE STATE SYNC -> PUSH BRANCH ONCE -> CREATE PR ONLY IF ABSENT -> VERIFY GOVERNANCE PR CI ON EXACT HEAD -> MERGE ONLY AFTER REQUIRED GATES PASS -> CHECKOUT/PULL MAIN AND VERIFY GOVERNANCE MERGE CI -> CREATE IMP-102 FEATURE BRANCH FROM EXACT UPDATED MAIN SHA -> CLAIM IMP-102 AND AUDIT FROZEN AUTHORITY/CURRENT FAILURE-RECOVERY SURFACES"


## IMP-101 GOVERNANCE SYNC MAIN VERIFIED / IMP-102 CLAIMED — 2026-10-13 22:42 +07

- [x] Governance PR #92 merged; merge commit `51a54667f6bd65137bf9293a6a8e922e8d3bb381`.
- [x] Push CI run `38383519269` SUCCESS on exact merge/main SHA `51a54667f6bd65137bf9293a6a8e922e8d3bb381`.
- [x] Frozen Master semantic hash matches manifest after CRLF-to-LF normalization; frozen files unchanged.
- [x] IMP-102 duplicate guard passed; no pre-existing branch/PR. Branch `chatgpt/IMP-102-failure-recovery-fault-injection` created from exact verified main SHA.
- [x] IMP-102 CLAIMED; hard dependencies IMP-052/053/054/055/100 MAIN VERIFIED.
- [ ] Audit Frozen Master §§69–71, GenerationJob/Scheduler/Recovery/Artifact code, existing unit tests and accepted evidence; record the fault-injection coverage gap matrix before code changes.
- [ ] Implement only uncovered crash/restart/provider ambiguity/artifact-failure cases and any proven root-cause defect; preserve existing PASS checkpoints.
- [ ] Run only new/changed targeted fault-injection tests first; record JUnit/exit code and deterministic outcome assertions.
- [ ] Run the smallest affected regression set justified by changes; do not rerun prior PASS suites solely due to chat/stream loss.
- [ ] Verify diff/checks, update evidence and all three state files, commit/push, create/update PR only after duplicate check, validate exact-head CI/review, merge only after gates pass, then verify main and select next dependency-ready task.

NEXT_EXACT_ACTION = "AUDIT FROZEN MASTER §§69–71 AND CURRENT GenerationJob/Scheduler/Recovery/Artifact implementations, existing unit tests and IMP-052..055/IMP-100 evidence -> BUILD A GAP MATRIX FOR CRASH/RESTART, PROVIDER AMBIGUITY, ARTIFACT FAILURE, IDEMPOTENCY AND DETERMINISTIC RECONCILIATION -> IMPLEMENT ONLY MISSING FAULT-INJECTION COVERAGE/ROOT-CAUSE FIXES; DO NOT RERUN PRIOR PASS SUITES"


## IMP-102 PLAN CHECKPOINT - FAULT-INJECTION GAP MATRIX - 2026-10-13 22:50 +07

- [x] Read authoritative IMP-102 goal/acceptance and frozen Master sections 69-71; frozen semantic SHA matches manifest.
- [x] Review existing IMP-052/053/054/055/100 evidence and test inventories; preserve all existing PASS checkpoints without rerunning those suites.
- [x] Identify focused gap: durable recovery-event/finalization and artifact-finalization replay after an actual SQLite writer close/reopen is not comprehensively covered across the boundaries.
- [ ] Add only four new true-restart tests in `tests/unit/test_studio_failure_recovery_fault_injection.py`: ambiguous recovery event replay; safe-requeue partial finalization replay; scheduler lease restart with proof-gated requeue; artifact final-event restart reconciliation.
- [ ] Run only the new test module and capture JUnit + process exit status; fix only a concrete failure exposed by those tests.

NEXT_EXACT_ACTION = "ADD THE FOUR TRUE-RESTART FAULT-INJECTION TESTS IN tests/unit/test_studio_failure_recovery_fault_injection.py USING EXISTING FIXTURE HELPERS -> RUN ONLY THAT NEW TEST MODULE WITH JUNIT EVIDENCE -> FIX ONLY ANY PROVEN FAILURE"


## IMP-102 TRUE-RESTART FAULT-INJECTION TARGETED PASS - 2026-10-13 23:02 +07

- [x] Four new true-restart fault-injection tests pass: 4/4; JUnit `.tmp/imp102-targeted.xml`; process exit 0; zero failures/errors/skips.
- [x] `python -m py_compile tests/unit/test_studio_failure_recovery_fault_injection.py` PASS; `git diff --check` PASS.
- [x] No production source changed; prior IMP-052..055/IMP-100 and frozen-guard PASS checkpoints were not rerun.
- [ ] Review exact six tracked files; exclude `.tmp/`; stage only the explicit intended list and verify staged diff.
- [ ] Commit and push the feature branch once; recheck remote/PR duplicate guard before creating PR.
- [ ] Verify CI and review on the exact PR head; merge only after required gates pass; checkout/pull main and verify main CI.

NEXT_EXACT_ACTION = "REVIEW THE EXACT SIX-TRACKED-FILE CHANGESET -> STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-101_MIGRATION_DRY_RUN_EVIDENCE.md, evidence/tests/IMP-102_FAILURE_RECOVERY_FAULT_INJECTION_EVIDENCE.md, tests/unit/test_studio_failure_recovery_fault_injection.py -> VERIFY STAGED FILE LIST AND git diff --cached --check -> COMMIT -> PUSH FEATURE BRANCH ONCE -> VERIFY REMOTE SHA AND CREATE PR ONLY IF ABSENT -> CHECK EXACT-HEAD CI/REVIEW -> MERGE ONLY AFTER REQUIRED GATES -> VERIFY MAIN AND CONTINUE QUEUE"


## IMP-102 COMMIT CHECKPOINT - 2026-10-13 23:07 +07

- [x] Test/evidence commit `ddcfb9550e7ccb1fae87199f570507dcbc020008` created from exact main parent `51a54667f6bd65137bf9293a6a8e922e8d3bb381`.
- [x] Commit scope verified: six intended files only; `.tmp/` excluded; commit diff-check PASS.
- [ ] Push branch after a fresh remote branch/PR duplicate guard; verify remote SHA.
- [ ] Create PR only if absent; verify CI/review for exact head; merge only after required gates and verify main CI.

NEXT_EXACT_ACTION = "RECHECK REMOTE FEATURE BRANCH AND PR ABSENT -> PUSH CURRENT BRANCH HEAD ONCE -> VERIFY origin BRANCH SHA EQUALS CURRENT HEAD -> CREATE PR ONLY IF ABSENT -> VERIFY PR EXACT HEAD AND CI"


## IMP-102 PUSH VERIFIED - 2026-10-13 23:10 +07

- [x] Feature branch push completed with exit 0; local and remote SHA matched at `c8e519d06479f578f99ecae90761cf70f200fbbe`.
- [x] Duplicate guard before push found no remote branch and no PR.
- [ ] Create PR only after a fresh duplicate guard; verify current PR head and exact-head CI/review.
- [ ] Merge only after required gates pass; verify main CI on exact merge SHA.

NEXT_EXACT_ACTION = "VERIFY PR ABSENT AND REMOTE BRANCH HEAD -> CREATE PR ONLY IF ABSENT -> RECORD PR NUMBER/HEAD AND CI STATE -> VERIFY REQUIRED CI/REVIEW ON THE FINAL EXACT PR HEAD"


## IMP-102 PR CREATED / CI PENDING - 2026-10-13 23:14 +07

- [x] PR #93 created after duplicate guard; state OPEN.
- [x] Exact head at creation verified: `c8e519d06479f578f99ecae90761cf70f200fbbe`; base main `51a54667f6bd65137bf9293a6a8e922e8d3bb381`.
- [x] Workflow run `38428355006` is IN_PROGRESS for that exact head; both Python 3.10 and 3.13 jobs are PENDING.
- [x] Exact local diff self-review PASS; no production source changes; no review submissions/comments at inspection.
- [ ] Commit/push PR/CI-pending state sync, then verify CI for the new exact head; do not attribute the old-head run to the new head.
- [ ] Merge only after exact-head required checks pass; verify main push CI on exact merge SHA.

NEXT_EXACT_ACTION = "STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md, evidence/tests/IMP-102_FAILURE_RECOVERY_FAULT_INJECTION_EVIDENCE.md -> VERIFY STAGED SET AND git diff --cached --check -> COMMIT PR/CI-PENDING STATE -> PUSH BRANCH -> FETCH PR #93 NEW EXACT HEAD AND ITS WORKFLOW RUN/JOBS -> DO NOT ATTRIBUTE RUN 38428355006 TO A NEWER HEAD"


## IMP-102 MAIN VERIFIED / GOVERNANCE SYNC FOR IMP-103 — 2026-10-14 00:02 +07

- [x] IMP-102 targeted true-restart fault-injection tests: 4/4 PASS, exit 0; JUnit `.tmp/imp102-targeted.xml` (local-only).
- [x] PR #93 merged; merge SHA `1e4bddef67db7e6b56b220da37e6e058d32c1638`; PR head `907f3cee51a291f037c4f1622f7a2fe2e32d9d6a`.
- [x] Exact PR-head CI run `38428733066` SUCCESS; Python 3.10 and 3.13 jobs PASS, including frozen Master baseline and unit tests.
- [x] Exact main push CI run `38434288246` SUCCESS on merge SHA `1e4bddef67db7e6b56b220da37e6e058d32c1638`; Python 3.10 and 3.13 jobs PASS, including frozen Master guard and unit tests.
- [x] Local `main` fast-forwarded to exact merge SHA; `HEAD = 1e4bddef67db7e6b56b220da37e6e058d32c1638`; tracked worktree clean. `.tmp/` remains untracked and excluded.
- [x] IMP-102 status = MAIN VERIFIED. No previous PASS test stage rerun; no live-provider/E2E claim (localhost:8100/health unavailable).
- [x] DAG next candidate = IMP-103 300-Shot Scale Benchmark. Hard dependencies IMP-003, IMP-053, IMP-060, IMP-061, IMP-062, IMP-100 are recorded MAIN VERIFIED; no IMP-103 branch or PR existed at duplicate guard.
- [ ] Merge this governance-only state sync and verify push-main CI before creating/claiming the IMP-103 implementation branch from the exact updated main SHA.
- NEXT_EXACT_ACTION = "REVIEW GOVERNANCE-ONLY THREE-FILE DIFF -> STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md -> VERIFY STAGED FILE LIST AND git diff --cached --check -> COMMIT -> PUSH ONCE -> CREATE PR ONLY IF ABSENT -> VERIFY EXACT-HEAD CI -> MERGE ONLY AFTER REQUIRED GATES -> CHECKOUT/PULL MAIN AND VERIFY PUSH CI -> CREATE IMP-103 FEATURE BRANCH FROM EXACT UPDATED MAIN SHA -> CLAIM IMP-103 AND AUDIT SCALE-BENCHMARK ACCEPTANCE/EXISTING LOAD TEST INFRASTRUCTURE BEFORE CODING"


## IMP-103 CLAIMED — 300-SHOT SCALE BENCHMARK — 2026-10-14 00:25 +07

- PROJECT_ROOT = `E:\FlowKit-Studio-Upgrade`; Git root `E:/FlowKit-Studio-Upgrade`.
- Branch = `chatgpt/IMP-103-300-shot-scale-benchmark`; base main SHA = `01f9f9939515d87065eb4ea9143981ace5770d42`.
- Governance PR #94 merged at `01f9f9939515d87065eb4ea9143981ace5770d42`; exact push-main workflow `38436895355` SUCCESS on that SHA; Python 3.10 and 3.13 jobs passed, including Frozen Master guard and unit tests.
- IMP-102 = MAIN VERIFIED: PR #93 merge SHA `1e4bddef67db7e6b56b220da37e6e058d32c1638`; exact PR-head CI run `38428733066` SUCCESS; main push CI `38434288246` SUCCESS. IMP-102 targeted fault-injection tests remain 4/4 PASS; no prior PASS suites rerun.
- IMP-103 hard dependencies per authoritative DAG: IMP-003, IMP-053, IMP-060, IMP-061, IMP-062, IMP-100; queue/evidence records each as MAIN VERIFIED. Duplicate guard: no prior local/remote branch or PR for `chatgpt/IMP-103-300-shot-scale-benchmark`.
- Goal = measure 300-shot long-form scale; acceptance = no starvation, unbounded queue or data loss, with reproducible measured evidence. Frozen Master Benchmark Strategy §§95/NFR-009/PERF-001/PERF-002 remain authority; historical spikes are reference only, not current acceptance evidence.
- Runtime = no local FlowKit test/build process; `.tmp/` is local-only and excluded from Git. Local API `http://127.0.0.1:8100/health` has previously been unreachable; this task must not claim live-provider evidence without a fresh health check.
- STATUS = CLAIMED / ANALYZE; implementation not started.
- NEXT_EXACT_ACTION = "AUDIT FROZEN MASTER BENCHMARK STRATEGY §§95/NFR-009/PERF-001/PERF-002 AND CURRENT QUEUE/DAG/SCHEDULER/GENERATIONJOB/PERSISTENCE IMPLEMENTATIONS + EXISTING UNIT TESTS + ACCEPTED EVIDENCE -> DEFINE A REPRODUCIBLE 300-SHOT WORKLOAD AND MEASURED GATES FOR REPOSITORY THROUGHPUT, QUEUE BOUNDS, DB/PERSISTENCE, FAIRNESS/STARVATION AND DATA INTEGRITY -> IDENTIFY EXISTING REUSABLE HARNESS AND COVERAGE GAPS -> IMPLEMENT ONLY MISSING BENCHMARK/TEST COVERAGE; DO NOT RERUN PRIOR PASS STAGES"


## IMP-103 ANALYZE COMPLETE - 2026-10-14 14:20 +07

- Repo truth: branch chatgpt/IMP-103-300-shot-scale-benchmark; HEAD 01f9f9939515d87065eb4ea9143981ace5770d42; no active FlowKit test/build process and no PTY session.
- Frozen Master integrity: normalized LF/UTF-8 SHA-256 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287 exactly matches the freeze manifest; 6770 lines. Raw Windows CRLF hash differs only because line endings; do not edit the Master.
- Authority: Master section 95 requires metadata/repository throughput and 300-shot scheduling/admission. NFR-009 requires bounded scalable workflow; PERF-001 requires hierarchical admission/cap-backpressure evidence; PERF-002 requires multi-project fairness/no starvation.
- Existing implementation: SQLiteWriteOwner uses asyncio.Queue(maxsize=128) by default and fails closed with WriteQueueFull; SchedulerRepository ordering is priority -> durable per-priority project round-robin -> oldest-ready. Existing tests already cover basic queue pressure, global capacity, concurrent claims and small fairness; these PASS checkpoints are not to be rerun.
- Gap found: no reusable 300-shot scale benchmark or accepted measured evidence found under evidence/. Historical spikes are not acceptance evidence.
- Plan: add a dedicated offline performance harness with 300 distinct canonical ShotIR/GenerationJob work items, deterministic synthetic routing only (no live provider calls), scheduler admission/claim metrics, bounded queue stress with capacity 32 and 300 unique writes, 300-row/3-project fairness simulation, DB row integrity/size, throughput and tracemalloc peak. Do not invent an absolute throughput SLA absent from frozen authority; report measurements and enforce invariants: all 300 unique shots/jobs preserved, no duplicate claim, cap never exceeded, queue depth never exceeds configured capacity, no project starvation.
- NEXT_EXACT_ACTION = "IMPLEMENT IMP-103 OFFLINE 300-SHOT BENCHMARK HARNESS AND FAST 300-ROW FAIRNESS CONTRACT TEST; RUN ONLY THE NEW TARGETS; CAPTURE JUNIT/JSON AND DATABASE/MEMORY/THROUGHPUT METRICS; VERIFY FROZEN MASTER UNCHANGED; SYNC EVIDENCE AND STATE BEFORE COMMIT"


## IMP-103 IMPLEMENTATION CHECKPOINT — 2026-10-14

- Task = IMP-103 300-Shot Scale Benchmark.
- Repo truth = `E:\FlowKit-Studio-Upgrade`; Git root = `E:/FlowKit-Studio-Upgrade`; branch = `chatgpt/IMP-103-300-shot-scale-benchmark`; HEAD = `01f9f9939515d87065eb4ea9143981ace5770d42`.
- Runtime classification = INTERRUPTED at post-implementation / pre-validation checkpoint: no FlowKit-specific test/build process is running, and no completed PASS/FAIL result exists for the new targets. Do not restart or rerun any prior PASS suite.
- Implementation artifacts present: `tests/performance/test_imp103_300_shot_scale.py` (806 lines) and `tests/unit/test_imp103_scale_contract.py`. Existing production code is unchanged by the IMP-103 implementation so far.
- Existing output guard checked: `.tmp/imp103-targeted.xml`, `.tmp/imp103-benchmark.json`, and `.tmp/imp103-targeted.log` were absent; no prior IMP-103 targeted evidence was found.
- Environment: global Python 3.11.9 has no pytest module; repository-local reusable interpreter and pytest executable exist at `.tmp/imp053-test-venv/Scripts/python.exe` and `.tmp/imp053-test-venv/Scripts/pytest.exe`. Use the project venv, not global Python. Unrelated PTY sessions were confirmed to run in another repository and were not touched.
- Current Git status includes the three state files modified, `.tmp/` untracked, and the two new test artifacts untracked. Keep `.tmp/` local-only and exclude it from commits.
- NEXT_EXACT_ACTION = "VERIFY .tmp/imp053-test-venv/Scripts/python.exe -m pytest --version -> RUN ONLY tests/performance/test_imp103_300_shot_scale.py AND tests/unit/test_imp103_scale_contract.py WITH JUNIT AT .tmp/imp103-targeted.xml AND CAPTURE THE IMP103_BENCHMARK_RESULT JSON MARKER -> CLASSIFY FINAL EXIT/JUNIT -> FIX ONLY A PROVEN NEW-TARGET FAILURE -> WRITE ACCEPTED MEASURED EVIDENCE AND SYNC ALL THREE STATE FILES; DO NOT RERUN PRIOR PASS SUITES"


## IMP-103 TARGETED VALIDATION RUNNING — 2026-10-14

- State = RUNNING; only the new IMP-103 targets are executing. Existing PASS suites are not being rerun.
- Process = FileMCP PTY `pty_8499d97743d1aa27c23c1583a1da8b78760d`; PID `161800`; command = `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q tests/performance/test_imp103_300_shot_scale.py tests/unit/test_imp103_scale_contract.py --junitxml=.tmp/imp103-targeted.xml`.
- Output paths = `.tmp/imp103-targeted.log` and `.tmp/imp103-targeted.xml`; initial PTY read had no output yet, so no result is inferred.
- NEXT_EXACT_ACTION = "MONITOR THE EXISTING PTY pty_8499d97743d1aa27c23c1583a1da8b78760d / PID 161800 AND ITS LOG/JUNIT; DO NOT START A SECOND TEST PROCESS; AFTER EXIT VERIFY FINAL EXIT CODE, JUNIT COUNTS/FAILURES AND IMP103_BENCHMARK_RESULT JSON BEFORE CLASSIFYING PASS/FAIL"


## IMP-103 TARGETED TEST FAILURE CHECKPOINT — 2026-10-14

- Test process = completed; FileMCP PTY `pty_8499d97743d1aa27c23c1583a1da8b78760d`, PID `161800`, final exit code 1. No FlowKit test process remains running.
- Evidence = `.tmp/imp103-targeted.log` and `.tmp/imp103-targeted.xml`. JUnit records two cases: `tests.unit.test_imp103_scale_contract.test_300_ready_rows_round_robin_three_projects_without_starvation` PASS (0.011s); `tests.performance.test_imp103_300_shot_scale.test_imp103_300_shot_scale_benchmark` FAIL (246.284s).
- Exact test failure = `ShotRealizationGateBlocked: StaticKeyframeSpec visible subject is not a ShotListItem subject` at `tests/performance/test_imp103_300_shot_scale.py:466`. Benchmark candidates inherit empty `subject_refs=()`, while reused `_static()` fixture sets `visible_subject_refs=(ENTITY_REF,)`.
- Secondary runner teardown error = pytest session-finish cleanup hit `PermissionError [WinError 5]` resolving global `C:\Users\Admin\AppData\Local\Temp\pytest-of-unknown\pytest-current`; this is an environment cleanup issue, separate from the benchmark assertion. Retry with repository-local `--basetemp=.tmp/imp103-pytest-tmp`.
- Preserve PASS = the three-project 300-row fairness contract test is PASS and must not be rerun. Do not rerun any pre-existing suite.
- NEXT_EXACT_ACTION = "FIX ONLY THE NEW BENCHMARK FIXTURE BY SETTING EACH SYNTHETIC ShotExpansionCandidate.subject_refs TO (ENTITY_REF,) SO IT MATCHES THE EXISTING StaticKeyframeSpec SUBJECT CONTRACT -> VERIFY NEW RETRY OUTPUT PATHS ARE ABSENT AND NO FLOWKIT TEST PROCESS IS RUNNING -> RERUN ONLY tests/performance/test_imp103_300_shot_scale.py WITH --basetemp=.tmp/imp103-pytest-tmp, --capture=tee-sys, JUNIT .tmp/imp103-benchmark-retry.xml AND LOG .tmp/imp103-benchmark-retry.log -> VERIFY EXIT/JUNIT/JSON MARKER; DO NOT RERUN THE PASSING UNIT CONTRACT TEST"


## IMP-103 BENCHMARK FIX CHECKPOINT — 2026-10-14

- Previous result remains recorded as FAIL; evidence preserved at `.tmp/imp103-targeted.log` and `.tmp/imp103-targeted.xml`. The independent unit fairness contract remains PASS and will not be rerun.
- Root-cause fix applied only to `tests/performance/test_imp103_300_shot_scale.py`: each synthetic `ShotExpansionCandidate` now sets `subject_refs=(ENTITY_REF,)`, matching the existing `_static()` fixture and canonical `ShotListItem.subject_refs` gate. No production implementation changed.
- Retry guard verified: no FlowKit test process remains; `.tmp/imp103-pytest-tmp`, `.tmp/imp103-benchmark-retry.xml`, and `.tmp/imp103-benchmark-retry.log` are absent.
- NEXT_EXACT_ACTION = "RUN ONLY tests/performance/test_imp103_300_shot_scale.py WITH .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-tmp --junitxml=.tmp/imp103-benchmark-retry.xml AND TEE OUTPUT TO .tmp/imp103-benchmark-retry.log -> MONITOR THAT SINGLE PROCESS -> VERIFY FINAL EXIT/JUNIT COUNTS, BENCHMARK JSON MARKER AND CLEANUP STATUS -> FIX ONLY ANY NEW PROVEN FAILURE; DO NOT RERUN tests/unit/test_imp103_scale_contract.py OR PRIOR PASS SUITES"


## IMP-103 FAILED-TARGET RETRY RUNNING — 2026-10-14

- State = RUNNING; this is the single retry of the previously failing benchmark target after the fixture correction. The already-PASS fairness unit test and all historical PASS suites are excluded.
- Process = FileMCP PTY `pty_8230acddbe09223c9ab411712fbce1022678`; PID `154644`; target child process must be verified from live runtime.
- Command = `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-tmp tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-retry.xml`.
- Durable output paths = `.tmp/imp103-benchmark-retry.log`, `.tmp/imp103-benchmark-retry.xml`; metrics marker will be captured with `--capture=tee-sys`. No result is inferred until final exit/JUnit is verified.
- NEXT_EXACT_ACTION = "MONITOR THE EXISTING PTY pty_8230acddbe09223c9ab411712fbce1022678 / PID 154644 AND ITS LOG; DO NOT START A SECOND BENCHMARK; AFTER EXIT VERIFY PROCESS EXIT CODE, JUNIT COUNTS, IMP103_BENCHMARK_RESULT JSON, ALL 300 JOB/SHOT INVARIANTS AND LOCAL TEMP CLEANUP"


## IMP-103 BENCHMARK RETRY INTERRUPTED - 2026-10-14 22:22 +07

- Runtime classification = INTERRUPTED, not PASS or FAIL. Repo branch remains `chatgpt/IMP-103-300-shot-scale-benchmark`; HEAD remains `01f9f9939515d87065eb4ea9143981ace5770d42`.
- Process check: PID 154644 is absent; no live command matches the IMP-103 benchmark/pytest target; FileMCP-E reports no owned PTY sessions. Do not infer PASS from a lost stream.
- Retry artifacts: `.tmp/imp103-benchmark-retry.log` and `.tmp/imp103-benchmark-retry.xml` are absent, and no `IMP103_BENCHMARK_RESULT` marker is available for the retry. The old failed-target evidence remains `.tmp/imp103-targeted.log` / `.tmp/imp103-targeted.xml`; its separate fairness contract case is PASS and must not be rerun.
- The fixture fix remains present at `tests/performance/test_imp103_300_shot_scale.py:397` (`subject_refs=(ENTITY_REF,)`). No production source or frozen Master was changed. Existing partial temp artifacts under `.tmp/imp103-pytest-tmp` are preserved.
- NEXT_EXACT_ACTION = "VERIFY NO LIVE IMP-103 TEST PROCESS AND NEW OUTPUT PATHS ABSENT -> RESUME ONLY tests/performance/test_imp103_300_shot_scale.py WITH .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume --junitxml=.tmp/imp103-benchmark-resume.xml; TEE OUTPUT TO .tmp/imp103-benchmark-resume.log -> MONITOR THE SINGLE EXISTING PTY -> VERIFY FINAL EXIT CODE, JUNIT, IMP103_BENCHMARK_RESULT AND ALL 300-SHOT/QUEUE/PERSISTENCE/FAIRNESS INVARIANTS -> DO NOT RERUN tests/unit/test_imp103_scale_contract.py OR ANY PRIOR PASS SUITE"


## IMP-103 BENCHMARK RESUME RUNNING - 2026-10-14 22:27 +07

- Runtime classification = RUNNING. The previously interrupted retry had no live process and no final log/JUnit; this is one resumed process for the same incomplete benchmark stage, not a duplicate.
- Active PTY = `pty_8be8c95ccb464f0d9f7d1eadc01872e5c986`; PowerShell PID `155268`; Python pytest parent PID `136900`, child Python PID `135788`; command = `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-resume.xml`.
- Output targets = `.tmp/imp103-benchmark-resume.log`, `.tmp/imp103-benchmark-resume.xml`; at launch both were absent. PTY initially had no output yet; no result inferred.
- Only the previously failing benchmark test is running. The three-project fairness contract PASS and all historical PASS suites are excluded. Frozen Master remains untouched.
- NEXT_EXACT_ACTION = "MONITOR PTY pty_8be8c95ccb464f0d9f7d1eadc01872e5c986 AND PIDS 155268/136900/135788; DO NOT START ANOTHER PROCESS -> AFTER EXIT VERIFY FINAL PTY EXIT CODE, JUNIT TESTS/FAILURES/ERRORS, IMP103_BENCHMARK_RESULT JSON, ALL 300 SHOT/JOB INTEGRITY, QUEUE CAPACITY, ADMISSION CAP, LEASE RELEASE, THREE-PROJECT FAIRNESS AND CLEANUP -> SYNC PASS/FAIL BEFORE ANY FURTHER STAGE"

## IMP-103 RESUME DIAGNOSTIC — 2026-10-14 23:35 +07

- Repo truth: branch `chatgpt/IMP-103-300-shot-scale-benchmark`; HEAD `01f9f9939515d87065eb4ea9143981ace5770d42`. Worktree still contains only the three state-file edits plus untracked IMP-103 tests and local-only `.tmp/`.
- Runtime classification = INTERRUPTED. PTY `pty_8be8c95ccb464f0d9f7d1eadc01872e5c986` reached `lifetime_expired` with exit code 1; no live FlowKit/pytest process exists. The only other owned PTY is compiling an unrelated Tang Video Merge Studio repo; it was not touched.
- Durable partial evidence: `.tmp/imp103-pytest-resume/test_imp103_300_shot_scale_ben0/imp103-300-shot-scale.db` (88,584,192 bytes) and its WAL (4,680,352 bytes; last write 23:26). Read-only SQLite inspection shows 300 ShotListItems, 300 eligibility gates, 300 FullShotSpecs, 300 StaticKeyframeSpecs, 300 MotionDeltaSpecs, only 46 ShotIR pointers (45 APPROVED + 1 DRAFT), 0 GenerationJobs, and 17,610 dependency edges. Thus the prior run never completed the compiler stage or produced final JUnit/log/result marker; no PASS can be inferred.
- The benchmark starts tracemalloc before the entire upstream 300-shot construction/compiler path and emits no phase progress until the end. To make the same required benchmark diagnosable and avoid instrumenting all upstream setup unnecessarily, adjust only the test harness to scope tracemalloc to the scheduler/claim measurement window and emit flushed phase-progress markers. Keep the full 300-shot/300-job workload and all queue, admission, persistence, fairness, uniqueness, and lease invariants. Do not change production code absent new evidence.
- Preserve the already-PASS `tests/unit/test_imp103_scale_contract.py` result; do not rerun it or any historical PASS suite. Preserve partial `.tmp/` evidence; exclude `.tmp/` from Git.
- NEXT_EXACT_ACTION = "EDIT ONLY tests/performance/test_imp103_300_shot_scale.py TO SCOPE TRACEMALLOC TO THE SCHEDULER/CLAIM MEASUREMENT WINDOW AND ADD FLUSHED PHASE-PROGRESS MARKERS WITHOUT WEAKENING ANY 300-SHOT ACCEPTANCE INVARIANTS -> VERIFY FROZEN MASTER UNCHANGED AND NO FLOWKIT TEST PROCESS RUNNING -> RUN ONLY tests/performance/test_imp103_300_shot_scale.py USING .tmp/imp053-test-venv/Scripts/python.exe WITH --capture=tee-sys --basetemp=.tmp/imp103-pytest-final --junitxml=.tmp/imp103-benchmark-final.xml AND CAPTURE LOG TO .tmp/imp103-benchmark-final.log -> MONITOR THAT SINGLE PROCESS -> VERIFY EXIT CODE, JUNIT, IMP103_BENCHMARK_RESULT JSON, ALL 300-SHOT/JOB/QUEUE/ADMISSION/PERSISTENCE/FAIRNESS/LEASE INVARIANTS -> WRITE ACCEPTED MEASURED EVIDENCE AND SYNC ALL THREE STATE FILES; DO NOT RERUN tests/unit/test_imp103_scale_contract.py OR PRIOR PASS SUITES"

## IMP-103 BENCHMARK HARNESS INSTRUMENTATION READY — 2026-10-14 23:39 +07

- Only `tests/performance/test_imp103_300_shot_scale.py` changed for this checkpoint; production source and prior PASS test files remain untouched.
- Added flushed phase markers through expansion, realization, compiler, routing/job creation, scheduler queue setup, claim drain and bounded-queue probe. Tracemalloc now measures only scheduler queue setup and scheduler claim windows; output keys name that scope explicitly. All 300-shot, distinct-job, queue-bound, hierarchical-admission, fairness, persistence, duplicate-claim and lease-release assertions remain present.
- Verification: project venv `python -m py_compile tests/performance/test_imp103_300_shot_scale.py` exit 0; `git diff --check` exit 0; frozen Master normalized LF/UTF-8 SHA-256 remains `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287` (6,770 lines); no FlowKit pytest process is active. Fresh output targets `.tmp/imp103-pytest-final`, `.tmp/imp103-benchmark-final.xml`, and `.tmp/imp103-benchmark-final.log` are absent.
- The prior benchmark is still classified INTERRUPTED and its partial DB/WAL are preserved. The independent 300-row/3-project fairness contract remains PASS and is not being rerun.
- NEXT_EXACT_ACTION = "RUN ONLY tests/performance/test_imp103_300_shot_scale.py WITH .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-final tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-final.xml; TEE ALL OUTPUT TO .tmp/imp103-benchmark-final.log AND EMIT FINAL EXIT CODE -> MONITOR THIS SINGLE PTY/PROCESS AND ITS PHASE MARKERS -> VERIFY EXIT CODE, JUNIT COUNTS/FAILURES, IMP103_BENCHMARK_RESULT JSON AND ALL 300-SHOT/QUEUE/ADMISSION/PERSISTENCE/FAIRNESS/LEASE INVARIANTS -> SYNC RESULTS; DO NOT RERUN tests/unit/test_imp103_scale_contract.py OR ANY PRIOR PASS SUITE"

## IMP-103 FINAL BENCHMARK RUNNING — 2026-10-14 23:40 +07

- Runtime state = RUNNING. One process launched for the previously interrupted benchmark stage only; no duplicate process was present at launch.
- PTY = `pty_4bba6db9686912469a406845b2c0f460380c`; PowerShell PID = `130800`; command = `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-final tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-final.xml`, with combined output tee'd to `.tmp/imp103-benchmark-final.log`.
- This run contains only `tests/performance/test_imp103_300_shot_scale.py`; the already-PASS `tests/unit/test_imp103_scale_contract.py` and all prior PASS suites are excluded. Frozen Master hash was verified unchanged immediately before launch.
- NEXT_EXACT_ACTION = "MONITOR PTY pty_4bba6db9686912469a406845b2c0f460380c / PID 130800 AND .tmp/imp103-benchmark-final.log; DO NOT START A SECOND PROCESS -> AFTER EXIT VERIFY FINAL PTY EXIT CODE, JUNIT TESTS/FAILURES/ERRORS, IMP103_BENCHMARK_RESULT JSON, 300 DISTINCT SHOT/JOB COUNTS, QUEUE BOUNDS, ADMISSION CAP, PERSISTED ROWS, FAIRNESS, ZERO ACTIVE LEASES AND CLEANUP -> SYNC FINAL RESULT"


## IMP-103 BENCHMARK RESUME3 RUNNING - 2026-10-15 10:32 +07

- Runtime classification = RUNNING. Existing PTY = `pty_845b5a735a06a1f5d1545c0065391a3bdfff`; PowerShell PID = `147820`; command runs only `tests/performance/test_imp103_300_shot_scale.py` using `.tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume3 ... --junitxml=.tmp/imp103-benchmark-resume3.xml`, with combined output tee'd to `.tmp/imp103-benchmark-resume3.log`.
- Prelaunch guard confirmed no live IMP-103 pytest process and all three new output targets absent. Existing partial artifacts in `.tmp/imp103-pytest-final` and `.tmp/imp103-pytest-resume` are preserved and not reused.
- Only the interrupted 300-shot benchmark stage is running. The already-PASS `tests/unit/test_imp103_scale_contract.py` and all historical PASS suites are excluded. This is an offline synthetic benchmark; it makes no real provider calls. Frozen Master/production source remain untouched.
- NEXT_EXACT_ACTION = "MONITOR EXISTING PTY pty_845b5a735a06a1f5d1545c0065391a3bdfff / PID 147820 AND .tmp/imp103-benchmark-resume3.log; DO NOT START A SECOND PROCESS -> AFTER EXIT VERIFY PTY EXIT CODE, FINAL_EXIT_CODE MARKER, JUNIT TESTS/FAILURES/ERRORS, IMP103_BENCHMARK_RESULT JSON, 300 DISTINCT SHOT/JOB COUNTS, QUEUE BOUNDS, HIERARCHICAL ADMISSION CAP, PERSISTENCE, FAIRNESS, ZERO ACTIVE LEASES AND CLEANUP -> SYNC FINAL PASS/FAIL; DO NOT RERUN tests/unit/test_imp103_scale_contract.py OR PRIOR PASS SUITES"


## IMP-103 BENCHMARK RESUME3 RESULT - 2026-10-15 16:12 +07

- Runtime classification = FAIL for the current benchmark attempt; no active IMP-103/pytest process remains and FileMCP-E PTY list is empty.
- Durable evidence: `.tmp/imp103-benchmark-resume3.log` (35,366 bytes; last write 2026-10-15 11:43:07) and `.tmp/imp103-benchmark-resume3.xml`. JUnit: 1 test, 1 failure, 0 errors, 0 skipped; duration 4,160.834 seconds; process PID 147820 is absent.
- The benchmark reached `IMP103_PROGRESS=compiler_complete shots=300` and failed at `tests/performance/test_imp103_300_shot_scale.py:561`: `TypeError: ProviderCapabilityRoutingRepository.route_initial() got an unexpected keyword argument 'correlation_id'`. No `IMP103_BENCHMARK_RESULT` marker was emitted; this is not PASS.
- Root cause verified against `agent/studio/provider_routing.py`: `route_initial` accepts no `correlation_id` argument and obtains it from `ProviderRouteRequest.run_correlation_id`. Fix only the benchmark callsite/request payload; do not change production routing code.
- Preserve prior PASS: `tests/unit/test_imp103_scale_contract.py` three-project 300-row fairness contract PASS. Do not rerun it or historical PASS suites. Preserve all partial `.tmp/` artifacts; keep `.tmp/` out of Git.
- NEXT_EXACT_ACTION = "EDIT ONLY tests/performance/test_imp103_300_shot_scale.py: set route_request.run_correlation_id to a unique run:imp103-route-NNN value in the ProviderRouteRequest payload and remove the unsupported correlation_id keyword from route_initial -> RUN project-venv py_compile + git diff --check and verify frozen Master hash unchanged -> VERIFY no active FlowKit pytest process and fresh resume4 output paths absent -> RUN ONLY tests/performance/test_imp103_300_shot_scale.py with .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume4 --junitxml=.tmp/imp103-benchmark-resume4.xml, tee log to .tmp/imp103-benchmark-resume4.log -> monitor that one process and verify exit/JUnit/IMP103_BENCHMARK_RESULT plus all 300-shot, distinct-job, queue, admission, persistence, fairness and lease invariants -> do not rerun tests/unit/test_imp103_scale_contract.py or any prior PASS suite"

## IMP-103 ROUTING REQUEST FIX READY - 2026-10-15 16:14 +07

- Fixed only tests/performance/test_imp103_300_shot_scale.py: each benchmark ProviderRouteRequest now receives a unique run_correlation_id=f"run:imp103-route-{index:03d}"; removed the unsupported correlation_id argument from route_initial. Production code is unchanged.
- Preflight PASS: project venv python -m py_compile tests/performance/test_imp103_300_shot_scale.py exit 0; git diff --check exit 0; frozen Master normalized SHA-256 matches manifest 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287; no live IMP-103/pytest process; fresh resume4 basetemp/JUnit/log paths absent.
- Previous benchmark FAIL remains preserved as .tmp/imp103-benchmark-resume3.xml and .tmp/imp103-benchmark-resume3.log. The benchmark fairness unit test and historical PASS suites remain excluded from reruns. .tmp/ remains local-only.
- NEXT_EXACT_ACTION = "RUN ONLY tests/performance/test_imp103_300_shot_scale.py with .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume4 tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-resume4.xml; tee combined output to .tmp/imp103-benchmark-resume4.log and record FINAL_EXIT_CODE -> monitor this single PTY/process and phase markers -> after exit verify JUnit, IMP103_BENCHMARK_RESULT JSON, all 300 distinct shot/job counts, queue bounds, hierarchical admission cap, persistence, fairness, zero active leases and cleanup -> do not rerun tests/unit/test_imp103_scale_contract.py or prior PASS suites"

## IMP-103 BENCHMARK RESUME4 RUNNING - 2026-10-15 16:21 +07

- State = RUNNING; a single process has been started for the previously failing benchmark target after the callsite fix. PTY = pty_ccf5907c814e86e41b48118414a34ebc2143; PowerShell PID 105736; pytest parent PID 153688; Python child PID 164860; start time 2026-10-15 16:21:41.
- Command = .tmp/imp053-test-venv/Scripts/python.exe -m pytest -q --capture=tee-sys --basetemp=.tmp/imp103-pytest-resume4 tests/performance/test_imp103_300_shot_scale.py --junitxml=.tmp/imp103-benchmark-resume4.xml; combined output is tee'd to .tmp/imp103-benchmark-resume4.log. At first poll, log/JUnit had not yet been created and PTY output was empty; no result inferred.
- This run includes only the benchmark target. The already-PASS tests/unit/test_imp103_scale_contract.py and all historical PASS suites remain excluded. Prior failed logs/JUnit and partial temp artifacts are preserved; .tmp/ stays out of Git.
- NEXT_EXACT_ACTION = "MONITOR existing PTY pty_ccf5907c814e86e41b48118414a34ebc2143 and PIDs 105736/153688/164860 plus .tmp/imp103-benchmark-resume4.log; do not start a second process -> after exit verify FINAL_EXIT_CODE, JUnit tests/failures/errors, IMP103_BENCHMARK_RESULT JSON, 300 distinct shot/job counts, queue bounds, hierarchical admission cap, persistence, fairness, zero active leases and cleanup -> sync final PASS/FAIL -> do not rerun tests/unit/test_imp103_scale_contract.py or prior PASS suites"

## IMP-103 RESUME4 LIVE MONITORING NOTE - 2026-10-15 16:28 +07

- Runtime remains RUNNING: PTY pty_ccf5907c814e86e41b48118414a34ebc2143; PowerShell PID 105736, pytest parent PID 153688, Python child PID 164860; process start 16:21:41. No duplicate IMP-103/pytest process exists.
- The test signature uses pytest capsys, so its flushed IMP103_PROGRESS prints are captured by the fixture and are not streamed to PTY/log while the test is active. Empty PTY/log at this point is not a process failure. Monitor the existing PIDs and DB/WAL growth; do not restart.
- Current artifact .tmp/imp103-pytest-resume4/test_imp103_300_shot_scale_ben0/imp103-300-shot-scale.db is 12,591,104 bytes (last write 16:28:25); read-only snapshot: studio_semantic_version=228, studio_current_pointer=228, studio_dependency_edge=2317; GenerationJob/Scheduler tables are still empty at this early setup phase. JUnit/log are not created yet.
- AGENTS.md health preflight to http://127.0.0.1:8100/health returned connection unavailable. This task is explicitly offline synthetic and makes no provider calls; no live-provider or production-E2E claim is made.
- NEXT_EXACT_ACTION = "MONITOR existing PTY pty_ccf5907c814e86e41b48118414a34ebc2143 and PIDs 105736/153688/164860; do not start another process -> inspect DB/WAL size and read-only progress snapshots until process exits or final log/JUnit appears -> verify FINAL_EXIT_CODE, JUnit and IMP103_BENCHMARK_RESULT plus all 300-shot, distinct-job, queue, admission, persistence, fairness and lease invariants -> sync final result; preserve prior PASS suites"


## IMP-103 RESUME4 INTERRUPTED / RESUME5 PREFLIGHT — 2026-10-15

- Task = IMP-103 300-Shot Scale Benchmark; status = INTERRUPTED after the resume4 process disappeared without final exit/JUnit/log/result marker.
- Runtime evidence: no live relevant process or owned PTY. Partial `.tmp/imp103-pytest-resume4/.../imp103-300-shot-scale.db` (52,019,200 bytes) and WAL (4,194,192 bytes) preserved; last write 16:44; read-only snapshot 886 semantic versions, 9,351 dependency edges, 0 GenerationJobs. Not PASS evidence.
- Previous resume3 attempt = FAIL, 1 test/1 failure due to unsupported `correlation_id` kwarg. Fixed harness by moving unique correlation into `ProviderRouteRequest.run_correlation_id`; production code untouched. Removed unused `capsys` fixture argument so streamed phase markers are visible under `--capture=tee-sys`.
- Preflight PASS: project venv py_compile exit 0; git diff --check exit 0; frozen Master normalized hash matches manifest `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`; no active process; resume5 outputs absent.
- Preserve PASS: `tests/unit/test_imp103_scale_contract.py::test_300_ready_rows_round_robin_three_projects_without_starvation` is already PASS; do not rerun it or any historical PASS suite. Preserve .tmp artifacts and exclude .tmp from Git.
- NEXT_EXACT_ACTION = "RUN ONLY tests/performance/test_imp103_300_shot_scale.py with .tmp/imp053-test-venv/Scripts/python.exe, --capture=tee-sys, --basetemp=.tmp/imp103-pytest-resume5 and --junitxml=.tmp/imp103-benchmark-resume5.xml; tee combined output to .tmp/imp103-benchmark-resume5.log and record FINAL_EXIT_CODE; use one PTY max lifetime 14,400 seconds and monitor visible phase markers; verify final exit, JUnit, IMP103_BENCHMARK_RESULT and all 300-shot/job, queue, admission, persistence, fairness, lease and cleanup invariants; do not rerun the PASS unit test or historical PASS suites"


## IMP-103 BENCHMARK RESUME5 RUNNING — 2026-10-15 18:17 +07

- Status = RUNNING; PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`; PIDs PowerShell 133688 / pytest 162744 / Python 143356; start 18:17:18 +07.
- Command runs only `tests/performance/test_imp103_300_shot_scale.py`; outputs: `.tmp/imp103-benchmark-resume5.log`, `.tmp/imp103-benchmark-resume5.xml`, basetemp `.tmp/imp103-pytest-resume5`; wrapper records `FINAL_EXIT_CODE`. PTY lifetime 14,400 seconds.
- First poll confirmed fresh DB/WAL growth and no duplicate process. No final result yet. Resume4 was interrupted without final JUnit/log; its partial DB/WAL are preserved. Previous resume3 failure is retained as evidence, not treated as PASS.
- Preflight PASS: project venv py_compile, git diff --check, and frozen Master normalized SHA match. The unused capsys parameter was removed only to make existing phase markers visible. The fairness unit test already PASS and must not be rerun; all historical PASS suites excluded.
- NEXT_EXACT_ACTION = "MONITOR existing PTY pty_73ab9086b5501e0fa31a73cf8097b781f4ca and PIDs 133688/162744/143356; do not start another process; verify final exit/JUnit/IMP103_BENCHMARK_RESULT and all 300-shot, distinct-job, queue, admission, persistence, fairness, lease and cleanup invariants; sync final result without rerunning any PASS suite"


## IMP-103 RESUME5 MONITOR CHECKPOINT — 2026-10-15 18:20 +07

- Runtime remains RUNNING: PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`; PIDs 133688/162744/143356 remain the one active benchmark chain. No duplicate process.
- Read-only progress snapshot: DB 12,177,408 bytes, WAL 4,165,352 bytes (last write 18:20:00); 276 semantic-version rows, 276 current pointers, 2,869 dependency edges, 0 GenerationJobs. This is mid-setup, not a result.
- PTY output cursor remains empty and JUnit/log are not yet created, even after removing the unused capsys fixture. Continue using process/DB/WAL evidence; do not infer failure or restart from absent output alone.
- NEXT_EXACT_ACTION = "MONITOR the same PTY/PIDs and read-only DB/WAL size/count snapshots; do not launch another benchmark; after process exit inspect PTY exit code, FINAL_EXIT_CODE marker, JUnit and result JSON; preserve all previous PASS suites"


## IMP-103 RESUME5 ACTIVE PROGRESS — 2026-10-15 18:24 +07

- Same process remains RUNNING: PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`, PIDs 133688/162744/143356. Python CPU = 103.75s at the last resource snapshot; process has not exited.
- Read-only DB snapshot: 21,598,208 bytes; WAL 4,181,832 bytes; 466 semantic-version/current-pointer rows, 5,046 dependency edges, 0 GenerationJobs; latest write 18:22:22. DB growth and CPU prove active progress, not a final benchmark result.
- PTY cursor/log/JUnit remain empty/not yet created; this absence alone is not FAIL. Use PID/process plus read-only DB/WAL evidence. Do not restart or launch another process.
- NEXT_EXACT_ACTION = "MONITOR the same PTY/PIDs and read-only DB/WAL progress until the existing process exits; then inspect final exit/JUnit/result marker and sync; never rerun any PASS suite"


## IMP-103 RESUME5 300-SHOT EXPANSION CHECKPOINT — 2026-10-15 18:27 +07

- Runtime remains RUNNING on PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`, PIDs 133688/162744/143356. No duplicate process; JUnit/log still not materialized and PTY cursor remains empty.
- Read-only SQLite evidence confirms expansion phase completed its core workload: `shot-v300=300`, `shot-trace-v300=300`; total semantic versions/current pointers = 631, dependency edges = 7,229, GenerationJobs = 0 at this snapshot. DB = 40,620,032 bytes; WAL = 4,194,192 bytes. This is intermediate progress only; realization/compiler/routing/jobs/scheduler assertions are not yet verified.
- NEXT_EXACT_ACTION = "MONITOR the same benchmark process and read-only DB/WAL; wait for final exit/JUnit/result marker; do not restart and do not rerun prior PASS suites"


## IMP-103 RESUME5 REALIZATION PROGRESS — 2026-10-15 18:29 +07

- Runtime remains RUNNING on the same PTY/PIDs 133688/162744/143356; process CPU increased to 197.97s. No duplicate process.
- Read-only DB snapshot: 47,685,632-byte DB, 4,194,192-byte WAL, 762 semantic versions, 8,328 dependency edges, 0 GenerationJobs. Group counts show 300 `shot-v300`, 300 `shot-trace-v300`, and 33 each of `eligibility-v300`, `full-spec-v1`, `static-v1`, `motion-v1`; realization is progressing. No final JUnit/log/result yet.
- NEXT_EXACT_ACTION = "CONTINUE MONITORING THE EXISTING BENCHMARK PROCESS AND DB/WAL; do not launch a duplicate; verify full final result only after process exit; keep previous PASS suites untouched"


## IMP-103 RESUME5 REALIZATION PROGRESS 73/300 — 2026-10-15 18:31 +07

- Same PTY/PIDs 133688/162744/143356 remain RUNNING; Python CPU 256.08s at latest process snapshot; no duplicate.
- Read-only SQLite: DB 53,760,000 bytes, WAL 4,194,192 bytes, 924 semantic versions, 9,664 dependency edges, 0 GenerationJobs. Version counts: 300 shots, 300 traces, 73 eligibility gates, 73 FullShotSpecs, 73 StaticKeyframeSpecs, 72 MotionDeltaSpecs. Realization progress is active; no final result.
- PTY cursor, JUnit and log remain empty/not created. Keep monitoring existing process/DB; no restart.
- NEXT_EXACT_ACTION = "MONITOR same benchmark PTY/PIDs and DB/WAL snapshots until completion; verify final JUnit/exit/result marker; do not rerun prior PASS suites"


## IMP-103 RESUME5 REALIZATION PROGRESS 152/300 — 2026-10-15 18:36 +07

- Runtime still RUNNING on PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`, PIDs 133688/162744/143356; Python CPU 375.67s. No duplicate process.
- Read-only DB snapshot: 64,888,832 bytes; 12,255 dependency edges; 1,238 semantic versions; 152 eligibility gates and 151 each FullShotSpec/StaticKeyframeSpec/MotionDeltaSpec. All 300 shots/traces remain present; GenerationJobs not yet created. This is active realization, not final evidence.
- PTY cursor/log/JUnit remain empty/not created. Process/DB evidence is advancing; continue monitoring the same process.
- NEXT_EXACT_ACTION = "MONITOR same benchmark PTY/PIDs and DB/WAL; wait for process exit and inspect final JUnit/exit/result marker; do not restart or rerun prior PASS suites"


## IMP-103 RESUME5 REALIZATION PROGRESS 189/300 — 2026-10-15 18:39 +07

- Same benchmark PTY/PIDs 133688/162744/143356 remain active; Python CPU 429.66s; no final log/JUnit yet.
- Read-only SQLite snapshot: DB 70,078,464 bytes; 13,492 dependency edges; 1,388 semantic versions; 189 eligibility/full/static artifacts and 188 motion artifacts; all 300 shots/traces remain present; 0 GenerationJobs. Realization continues with persisted progress; no PASS inferred.
- NEXT_EXACT_ACTION = "MONITOR the existing process and DB/WAL until the same benchmark exits; then verify final exit/JUnit/result JSON; do not restart or rerun any PASS suite"


## IMP-103 RESUME5 REALIZATION PROGRESS 252/300 — 2026-10-15 18:42 +07

- Same benchmark process remains RUNNING on PTY `pty_73ab9086b5501e0fa31a73cf8097b781f4ca`; PIDs 133688/162744/143356. Python CPU 516.69s; no duplicate.
- Read-only DB: 79,507,456 bytes, 15,555 dependency edges, 1,638 semantic versions; 252 eligibility gates and 251 each full/static/motion artifacts; 300 shot/trace identities preserved; GenerationJobs still 0. Realization is advancing; not a final result.
- PTY/JUnit/log still no output/artifact. Keep monitoring same process and DB/WAL, no restart.
- NEXT_EXACT_ACTION = "MONITOR existing benchmark process; after exit verify final JUnit/exit/result marker and all invariants; preserve prior PASS suites"


## IMP-103 BENCHMARK PASS / LOCAL VERIFICATION — 2026-10-15

- [x] Local synthetic 300-shot benchmark: final JUnit 1/1 PASS, 0 failures/errors/skips; `FINAL_EXIT_CODE=0`; log/JUnit `.tmp/imp103-benchmark-resume5.log` and `.tmp/imp103-benchmark-resume5.xml` (local-only).
- [x] 300 unique shot IDs and 300 unique GenerationJob IDs; 300 claims; 300 scheduler nodes/readiness checkpoints; 0 queued jobs after claim drain.
- [x] Fairness: 3 projects × 100 shots, max inter-arrival gap 3, 0 starved projects.
- [x] Bounded queue stress: cap/peak 32/32; 268 rejected then retried; 300 unique rows persisted. Admission cap 4: 4 of 8 concurrent claims admitted; max active leases 4. Cleanup leaves 0 active leases.
- [x] Frozen Master guard exit 0 / PASS; normalized SHA-256 unchanged; `git diff --check` exit 0. Production source unchanged; offline synthetic benchmark, no live-provider claim.
- [x] Existing fairness unit-contract PASS preserved without rerun. Previous failed/interrupted artifacts retained. Local-only `.tmp/` must not be staged.
- [x] Durable evidence record: `evidence/tests/IMP-103_300_SHOT_SCALE_BENCHMARK_EVIDENCE.md`.
- [ ] Git lifecycle, PR exact-head checks/review, merge and main verification remain pending; status is LOCAL VERIFIED, not MAIN VERIFIED.
- NEXT_EXACT_ACTION = "REVIEW IMP-103 TEST HARNESS AND EVIDENCE DIFF; VERIFY git status, git diff --check, AND FROZEN MASTER UNCHANGED -> STAGE ONLY tests/performance/test_imp103_300_shot_scale.py, tests/unit/test_imp103_scale_contract.py, evidence/tests/IMP-103_300_SHOT_SCALE_BENCHMARK_EVIDENCE.md, CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md; EXCLUDE .tmp/ -> VERIFY STAGED FILE LIST AND git diff --cached --check -> COMMIT LOCAL-VERIFIED IMP-103 -> RECHECK REMOTE BRANCH/PR AND PUSH ONCE; CREATE PR ONLY IF ABSENT -> VERIFY EXACT-HEAD CI/REVIEW -> MERGE ONLY AFTER REQUIRED GATES -> CHECKOUT/PULL MAIN AND VERIFY MERGE/MAIN CI -> MARK MAIN VERIFIED AND CLAIM THE NEXT DEPENDENCY-READY TASK"


## IMP-103 PR #95 OPEN / CI NOT YET REPORTED — 2026-10-15

- [x] Commit `792e4b236dd745f08544fc8f9aed30627eec0eee` pushed to feature branch.
- [x] PR #95 created and verified OPEN/mergeable; base main `01f9f9939515d87065eb4ea9143981ace5770d42`; initial head `792e4b236dd745f08544fc8f9aed30627eec0eee`.
- [ ] Exact-head CI not yet reported: PR statusCheckRollup empty, `gh pr checks` says no checks reported, and no branch run is listed. The `tests` workflow is active with a pull_request trigger; verify the new exact head after governance sync.
- [ ] Do not merge until required checks pass and review gate is satisfied; after merge verify main and push-main CI.
- NEXT_EXACT_ACTION = "RECORD PR #95 OPEN WITH INITIAL HEAD 792e4b236dd745f08544fc8f9aed30627eec0eee AND BASE main 01f9f9939515d87065eb4ea9143981ace5770d42; NOTE THAT NO PR CHECKS/RUN HAVE BEEN REPORTED YET -> COMMIT/PUSH THIS GOVERNANCE-ONLY SYNC ON THE SAME BRANCH -> VERIFY NEW EXACT PR HEAD AND ITS WORKFLOW RUN/JOBS -> DO NOT MERGE UNTIL REQUIRED CHECKS PASS AND REVIEW GATE IS SATISFIED -> AFTER MERGE CHECKOUT/PULL MAIN, VERIFY MERGE SHA AND PUSH-MAIN CI, THEN MARK MAIN VERIFIED AND CLAIM NEXT DEPENDENCY-READY TASK"


## IMP-103 PR #95 EXACT-HEAD CI DISPATCH DIAGNOSTIC — 2026-10-15 22:21 +07

- Latest observed PR head before this state sync = `4a4b064d89fa3f35b79977b827b1b120b0080441`; PR #95 remains OPEN, base main `01f9f9939515d87065eb4ea9143981ace5770d42`.
- Rechecked GitHub API for the exact head: zero check suites; commit status has zero statuses and state `pending`; no workflow run exists for the branch or exact SHA; no `action_required` or queued run exists.
- Repository Actions are enabled, `.github/workflows/tests.yml` is active and declares `pull_request`, but GitHub has not created the expected run. Branch protection endpoint reports main is not protected; that does not substitute for the project CI gate.
- No code/test stage was rerun. Do not merge or claim MAIN VERIFIED while CI is absent. A new state-sync commit will advance the PR head; inspect the newest exact head after pushing.
- NEXT_EXACT_ACTION = "DIAGNOSE WHY ACTIVE WORKFLOW tests.yml (pull_request trigger, Actions enabled) HAS NOT CREATED A CHECK SUITE/RUN FOR PR #95; QUERY APPROVAL/WEBHOOK/WORKFLOW STATUS FOR THE CURRENT PR HEAD -> DO NOT MERGE WHILE THE PROJECT CI GATE IS UNVERIFIED -> IF THE REQUIRED WORKFLOW CANNOT BE TRIGGERED WITH AVAILABLE AUTHORITY, RECORD THE EXTERNAL BLOCKER AND LEAVE PR #95 OPEN; OTHERWISE VERIFY ALL CHECKS AGAINST THE NEWEST EXACT HEAD"


## IMP-103 PR #95 — EXTERNAL CI DISPATCH BLOCKER — 2026-10-15 22:27 +07

- Latest exact PR head inspected before this state sync = `940944be67a7187a8abe77835d0c5ec627ae8cdf`; PR #95 is OPEN, base main `01f9f9939515d87065eb4ea9143981ace5770d42`.
- GitHub reports zero check suites and zero commit statuses for that head; no workflow run exists for the exact SHA/branch; no queued or `action_required` run exists. This was rechecked after both the initial feature commit and the subsequent state-sync push.
- Repository Actions are enabled and `.github/workflows/tests.yml` is active with `pull_request` and `push: branches: [main]` triggers. The workflow does not declare `workflow_dispatch`; there is no run ID to approve or rerun. Main is not branch-protected, but that does not satisfy the project CI gate.
- I am not merging without the project CI gate and will not broaden the workflow trigger or bypass CI as an unrelated change. Local benchmark PASS and frozen guard PASS remain valid; no test stage was rerun.
- Status = LOCAL VERIFIED / PR OPEN / MAIN NOT VERIFIED. `.tmp/` remains local-only.
- NEXT_EXACT_ACTION = "EXTERNAL BLOCKER: GITHUB ACTIONS HAS NOT CREATED A PR CHECK/RUN FOR PR #95 DESPITE THE ACTIVE pull_request WORKFLOW; REPOSITORY OWNER/MAINTAINER MUST RESOLVE OR AUTHORIZE A SUPPORTED TRIGGER -> KEEP PR #95 OPEN AND DO NOT MERGE -> AFTER A RUN APPEARS, VERIFY ALL CHECKS AGAINST THE LATEST PR HEAD, COMPLETE REVIEW/MERGE, THEN VERIFY MAIN/PUSH CI AND CLAIM THE NEXT DEPENDENCY-READY TASK"


## IMP-103 MAIN VERIFIED / IMP-104 NEXT — STATE RECONCILIATION — 2026-10-17 12:04 +07

- [x] IMP-103 benchmark local acceptance PASS; existing JUnit/log/result evidence retained, no rerun.
- [x] PR #95 merged at `ed3b870a2b96b4509dc97ec9b0569cbed72dd70f`.
- [x] Exact post-merge `main` push CI run `38934508616` SUCCESS on the merge SHA; Python `unit (3.10)` and `unit (3.13)` jobs plus Frozen Master guard passed.
- [x] Local `main` fast-forwarded to exact `origin/main` SHA `ed3b870a2b96b4509dc97ec9b0569cbed72dd70f`; tracked worktree clean; `.tmp/` preserved as local-only untracked artifacts.
- [x] Runtime check found no active FlowKit/pytest/benchmark process and no FileMCP PTY session.
- [x] Historical “PR #95 OPEN / external CI blocker” state is superseded by merged PR + successful main push CI. No PR review is claimed; PR-specific check/review endpoints were empty.
- [ ] Governance-only reconciliation of CURRENT_HANDOFF.md, PROJECT_STATE.md, and this queue remains to be committed/pushed through the normal PR workflow.
- [ ] Next task after accepted governance sync: `IMP-104 — Electron Security Acceptance`; authoritative decomposition dependencies: IMP-070, IMP-071, IMP-072, IMP-073, IMP-100, all recorded MAIN VERIFIED. Duplicate guard: no local/remote IMP-104 branch or PR found.
- NEXT_EXACT_ACTION = "VERIFY THREE-FILE GOVERNANCE DIFF AND git diff --check -> STAGE ONLY CURRENT_HANDOFF.md, PROJECT_STATE.md, tasks/TASK_QUEUE.md -> VERIFY STAGED FILE LIST AND git diff --cached --check -> COMMIT/PUSH GOVERNANCE-ONLY BRANCH ONCE -> CREATE PR ONLY IF ABSENT -> INSPECT EXACT-HEAD CHECKS/REVIEW WITHOUT BYPASS -> AFTER GOVERNANCE SYNC IS ACCEPTED, VERIFY MAIN PUSH CI AND CLAIM IMP-104 FROM EXACT UPDATED MAIN SHA; AUDIT FROZEN ELECTRON SECURITY AUTHORITY AND PACKAGED TARGET TOPOLOGY BEFORE CODING"


## IMP-104 CLAIMED — 2026-10-17 12:30 +07

- [x] Governance state reconciliation merged as PR #96 at main SHA `1f234046f739e21d6963ef5307025793190f8cfd`.
- [x] PR #96 exact-head CI run `39005603559` SUCCESS (Python 3.10 + 3.13; Frozen Master guard PASS).
- [x] Post-merge main push CI run `39006071976` SUCCESS on exact merge SHA `1f234046f739e21d6963ef5307025793190f8cfd` (Python 3.10 + 3.13; Frozen Master guard PASS).
- [x] IMP-103 MAIN VERIFIED; benchmark evidence retained, not rerun.
- [x] Duplicate guard passed for `chatgpt/IMP-104-electron-security-acceptance`: no local/remote branch or PR existed before claim.
- [x] IMP-104 claimed from exact verified main SHA `1f234046f739e21d6963ef5307025793190f8cfd`; hard dependencies IMP-070, IMP-071, IMP-072, IMP-073, IMP-100 are recorded MAIN VERIFIED.
- [ ] Analyze Frozen Master §84/§85 and SEC-001..011; map current packaged Electron target topology to negative-test coverage.
- [ ] Preflight pinned dependency install and packaging safely; no Electron dependencies installed and no package artifact exists yet.
- [ ] Implement only missing IMP-104 acceptance gates; do not rerun unchanged PASS suites from IMP-070..073.
- Procedure note: frozen_master_guard was inadvertently rerun despite prior PASS; it returned PASS with unchanged semantic SHA. Do not repeat unless the frozen artifact changes.
- NEXT_EXACT_ACTION = "READ FROZEN SECURITY §84/§85 + SEC-001..011 -> AUDIT PACKAGED TARGET AND EXISTING TEST COVERAGE -> DEFINE THREAT MATRIX/NEGATIVE CASES -> VERIFY LOCKFILE SOURCES, INTEGRITY, LICENSES, VERSIONS, DISK/OUTPUT AND PROCESS SAFETY BEFORE INSTALL/PACK -> IMPLEMENT MISSING IMP-104 GATES -> RUN ONLY NEW/CHANGED TESTS AND PACKAGE-RUNTIME PROOF -> EVIDENCE, EXACT-HEAD REVIEW, PR/CI, MERGE AND MAIN VERIFICATION"


## IMP-104 DEPENDENCY PREFLIGHT PASS — 2026-10-17 12:35 +07

- [x] Lockfile source/version/license/integrity audit: 284/284 packages from registry.npmjs.org; no missing integrity hashes or license metadata; direct Electron/electron-builder pins match current registry metadata.
- [x] Official Electron v44.7.0 Windows x64 ZIP verified from GitHub release metadata: 158293649 bytes; SHA-256 `eee30dc8fa1f5ea95490e59f44e46ea68dd24c6e93d22facf70fe5c2d4c2665c`; exact match in the pinned package checksum manifest; HEAD 200/content length matched.
- [x] `npm ci --ignore-scripts --no-audit --no-fund` dependency tree installed completely; npm debug log reports exit 0/info ok, all lockfile package paths present. PowerShell wrapper exit 1 was due to elevating a deprecation warning; do not rerun npm ci.
- [ ] Install Electron runtime binary using only the inspected pinned installer/checksum path; capture log and exit marker.
- [ ] Package target into dedicated local `.tmp/imp104` path after builder cache/output preflight; then execute only new packaged security gates.
- NEXT_EXACT_ACTION = "RUN PINNED ELECTRON INSTALLER ONCE -> MONITOR EXISTING PID/LOG/OUTPUT WITHOUT RESTART -> VERIFY VERSION/CHECKSUM -> PACKAGE UNDER .tmp/imp104 -> RUN ONLY NEW PACKAGED SECURITY NEGATIVE TESTS AND RETAIN JUNIT/RUNTIME EVIDENCE"


## IMP-104 PINNED ELECTRON RUNTIME INSTALL PASS — 2026-10-17 12:42 +07

- [x] Pinned Electron installer ran once and exited 0; version marker and Windows file/product versions all `44.7.0`.
- [x] Installed executable exists: 246302208 bytes, SHA-256 `2529B494F4123F152BCE346051F7BD855EF95006424A561953CF17C49A3D1BA8`; upstream ZIP hash matched official release metadata and package checksum manifest.
- [x] Electron-builder CLI version verified `26.15.3`; isolated cache env support confirmed in package source.
- [ ] Package unpacked Windows x64 target to local `.tmp/imp104/package` with cache isolated from other projects.
- [ ] Inspect packaged file/ASAR/runtime markers, then run only new packaged security negative tests.
- NEXT_EXACT_ACTION = "BUILD CONFIG/LOG UNDER .tmp/imp104 -> PACKAGE --dir --win --x64 WITH ELECTRON_BUILDER_CACHE ISOLATED + PUBLISH NEVER -> MONITOR EXISTING PROCESS WITHOUT RESTART -> VERIFY PACKAGE -> NEW PACKAGED SECURITY NEGATIVE TESTS"


## IMP-104 PACKAGED WINDOWS TARGET BUILD PASS — 2026-10-17 12:44 +07

- [x] Packaged target build exit 0, output `.tmp/imp104/package/win-unpacked`, 72 files / 385480975 bytes.
- [x] app.asar SHA-256 `66449745396A1C7B803AD102A413D06F805BA4AFAC41F8449D4D82F58C6F50CC`; executable SHA-256 `A0C095AEEA05E5DE3F465C9806575AED2BFEDCCEE42DC7000EB2477AEAB7BB52`; Electron version 44.7.0 / app version 0.1.0.0.
- [x] Packaged ASAR includes expected main/preload/IPC/broker/utility/renderer modules and excludes test files and node_modules; output and caches isolated under .tmp/imp104.
- [ ] Add safe packaged Main self-test for Windows DPAPI/safeStorage synthetic round-trip with no secret disclosure and no vault write.
- [ ] Add permanent negative acceptance test against exact packaged ASAR modules for API/IPC/navigation/path/CSP/package exclusion boundaries.
- [ ] Repackage only after source change; run only new IMP-104 acceptance gates; do not rerun IMP-070..073 PASS suites or Frozen Master guard.
- NEXT_EXACT_ACTION = "IMPLEMENT SELF-TEST + PACKAGED ASAR NEGATIVE ACCEPTANCE TEST -> SYNTAX CHECK CHANGED JS -> REPACKAGE -> RUN ONLY NEW IMP-104 PACKAGED TESTS -> JUNIT/RUNTIME EVIDENCE"

## IMP-104 PACKAGED SECURITY ACCEPTANCE PASS — 2026-10-17 13:02 +07

- [x] Lockfile supply-chain/license/integrity audit; isolated dependency install.
- [x] Verified official Electron 44.7.0 Windows x64 asset checksum; installed pinned runtime.
- [x] Built packaged Windows x64 target to `.tmp/imp104/package/win-unpacked`; hashes recorded in evidence.
- [x] Added permanent packaged-ASAR negative acceptance test covering package exclusions, hardened BrowserWindow flags, CSP, narrow preload API, URL/path/navigation/popup/webview denial, strict IPC/sender checks and redacted errors.
- [x] Packaged safeStorage synthetic round-trip and no-vault-write proof; native Windows DPAPI key unwrap proof; JUnit 2/2 PASS.
- [x] Added sanitized evidence `evidence/tests/IMP-104_ELECTRON_SECURITY_ACCEPTANCE_EVIDENCE.md`.
- [ ] Review/stage intended files only; exclude all `.tmp/imp104` artifacts.
- [ ] Commit and push implementation/evidence/state; verify PR exists before creating one.
- [ ] Wait for exact-head CI and review; merge only after required gates.
- [ ] Verify main merge SHA and main push CI; then claim next valid queued task.
- NEXT_EXACT_ACTION = "DIFF REVIEW -> DIFF/SYNTAX CHECK -> COMMIT/PUSH INTENDED FILES -> PR CI/REVIEW -> MERGE AFTER GATES -> VERIFY MAIN -> NEXT QUEUE TASK"

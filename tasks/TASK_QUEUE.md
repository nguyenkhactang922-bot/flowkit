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

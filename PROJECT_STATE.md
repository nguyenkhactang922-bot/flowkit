# Project State

- Phase: governance/bootstrap
- Detailed design: not started
- Feature code changes: none
- Dependency installation: none
- Build execution: none
- Commit: none


---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = DISCOVERY / CURRENT STATE AUDIT

### Verified in repository source

- Workspace and Git identity were verified from the live checkout.
- Runtime topology was verified as FastAPI + SQLite + Chrome MV3 extension + React/Vite dashboard.
- No Electron runtime was found.
- No root src/ directory exists; source is split across agent/, dashboard/src/, extension/, skills/, and tests/.
- Entity/reference generation, media persistence, Flow/Omni transport, request queue, retry/resume behavior, and rendered-video QA were inspected in implementation code.
- Current Scene was verified to combine prompt/generation/media/chain responsibilities.
- No canonical runtime StoryGraph, MacroStoryBeat, SceneDramaticBeat, Shot, Shot IR, or production prompt compiler was found.
- Current story state is primarily project.story plus procedural skill instructions.
- Current continuity is primarily media/reference chaining, not a narrative/world-state continuity ledger.
- Current QA reviewer returns structured video findings but does not persist a canonical QA/Repair artifact chain.
- Test source was inventoried; 323 pytest test functions plus an MV3 bootstrap regression script were observed. Tests were NOT executed in this phase.
- docs/CHATCODE_GLOBAL_MULTI_PROJECT_EXECUTION_LAW.md is currently a bootstrap placeholder; no additional detailed law text has yet been imported into that file.

### Discovery artifacts created

- docs/research/repo-audits/FLOWKIT_CURRENT_STATE_ARCHITECTURE_AUDIT.md
- docs/research/findings/FLOWKIT_TO_AI_FILM_STUDIO_GAP_MATRIX.md

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Test execution: none.
- Commit: none.
- Detailed canonical Studio design import: not started.
- Implementation feature task creation: not started.

### Evidence policy

No PASS status is asserted for runtime behavior because no build/test/live execution was requested or performed in this phase.


---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = DISCOVERY / CURRENT STATE AUDIT

### Verified in repository source

- Workspace and Git identity were verified from the live checkout.
- Runtime topology was verified as FastAPI + SQLite + Chrome MV3 extension + React/Vite dashboard.
- No Electron runtime was found.
- No root src/ directory exists; source is split across agent/, dashboard/src/, extension/, skills/, and tests/.
- Entity/reference generation, media persistence, Flow/Omni transport, request queue, retry/resume behavior, and rendered-video QA were inspected in implementation code.
- Current Scene was verified to combine prompt/generation/media/chain responsibilities.
- No canonical runtime StoryGraph, MacroStoryBeat, SceneDramaticBeat, Shot, Shot IR, or production prompt compiler was found.
- Current story state is primarily project.story plus procedural skill instructions.
- Current continuity is primarily media/reference chaining, not a narrative/world-state continuity ledger.
- Current QA reviewer returns structured video findings but does not persist a canonical QA/Repair artifact chain.
- Test source was inventoried; 323 pytest test functions plus an MV3 bootstrap regression script were observed. Tests were NOT executed in this phase.
- docs/CHATCODE_GLOBAL_MULTI_PROJECT_EXECUTION_LAW.md is currently a bootstrap placeholder; no additional detailed law text has yet been imported into that file.

### Discovery artifacts created

- docs/research/repo-audits/FLOWKIT_CURRENT_STATE_ARCHITECTURE_AUDIT.md
- docs/research/findings/FLOWKIT_TO_AI_FILM_STUDIO_GAP_MATRIX.md

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Test execution: none.
- Commit: none.
- Detailed canonical Studio design import: not started.
- Implementation feature task creation: not started.

### Evidence policy

No PASS status is asserted for runtime behavior because no build/test/live execution was requested or performed in this phase.



---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = HISTORICAL DESIGN CORPUS EXPANDED / PRE-CONSOLIDATION

### Verified

- 16/16 historical version snapshots V0.1 through V0.16 extracted and verified.
- Historical entries remain version-separated under `docs/historical/chat-design-corpus/expanded/V0_01` through `V0_16`.
- Historical design files were not edited.
- No deduplication or Master canonical merge was performed.
- Post-V0.16 canonical merge candidates remain at corpus top level.
- `HISTORICAL_EXPANSION_MANIFEST.md` records per-version integrity, counts, presence checks, and global duplicate/byte-identical inventory.

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Test execution: none.
- Commit: none.
- Authority map: not started.
- Supersession resolution: not started.
- Canonical Master merge: not started.



---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = PRE-MASTER AUTHORITY RESOLUTION / BLOCKED

### Verified authority audit

- Entire expanded historical corpus V0.1 through V0.16 was inventoried by normalized logical path and SHA-256.
- 142 logical documents are covered when the 137 historical logical paths are combined with 5 top-level post/standalone sources.
- 85 historical logical families are byte-identical across all appearances.
- 38 historical logical families contain evolved content.
- 161 physical SHA-256 duplicate-content groups were identified without physical deduplication.
- Explicit supersession and split/extension lineage was mapped from ADRs, state/handoff lineage, review decisions, contradiction audit, registries and actual contract changes.
- Required Primary candidate sources: 22.
- Required Supporting sources: 17.
- Historical-only standalone sources: 2.
- Superseded semantics/families excluded from current-authority merge: 12.
- Unresolved unique conflicts: 7.
- Blocking authority decision groups: 5.
- No canonical Master was created.

### Exact blocking areas

1. Credential Broker / secret-storage authority status.
2. Universal BrainPack / ActiveProductionProfile ownership and precedence.
3. Narrative Expansion artifact identity and relation to Story/Sequence/Scene identities.
4. MacroStoryBeat / SceneDramaticBeat plus Directing/Blocking/Cinematography authority chain.
5. Shot identity / ShotListManifest / FullShotSpec / ShotSpec / ShotIR boundary.

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Test execution: none.
- Commit: none.
- Physical historical deduplication: none.
- Historical file deletion: none.
- Master canonical consolidation: blocked / not started.
- Implementation coding tasks: not authorized.



---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = PRE-MASTER AUTHORITY MAP COMPLETE

### Accepted pre-Master authority decisions

- ADR-0016: Host Security Broker is canonical credential authority; Electron Main + safeStorage is target long-lived secret owner; Utility gets scoped short-lived leases; Renderer has no long-lived secret authority; FlowKit auth/session is compatibility-only.
- ADR-0017: one BrainPack Registry, one Profile Resolver, immutable pinned ActiveProductionProfile; hard constraints/locked invariants outrank soft/project preferences; downstream does not independently resolve packs.
- ADR-0018: canonical narrative identities are StoryCore ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ MacroStoryBeat ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Sequence ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ Scene ÃƒÂ¢Ã¢â‚¬Â Ã¢â‚¬â„¢ SceneDramaticBeat; no generic persistent Beat; SceneList/SceneBreakdown are manifests/projections only.
- ADR-0019: canonical dramatic-to-camera authority chain is fixed from SceneDramaticBeat through AudienceExperienceTarget, DirectingIntent, SceneSpatialDramaticContract, BlockingPlan and CinematographyObjective to ShotListItem; camera cannot self-author.
- ADR-0020: ShotListItem originates canonical shot_id; FullShotSpec realizes the same shot_id; legacy generic ShotSpec has no independent authority; ShotIR is provider-neutral derivative referencing shot_id; provider prompt/request is never canonical truth.

### Authority audit result

- PRE_MASTER_AUTHORITY_COVERAGE_AUDIT_V2 = PASS.
- Unique decision conflicts tracked: 20.
- Resolved/principle-set: 18.
- Unresolved unique conflicts: 2.
- Blocking unresolved conflicts: 0.
- Non-blocking unresolved conflicts: 2.
- PM-014 Compiler ownership remains consolidation work, not blocker.
- PM-020 Sequence QA contract remains consolidation work, not blocker.

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Test execution: none.
- Commit: none.
- Historical source edits: none.
- Master canonical consolidation: not started.
- Implementation coding tasks: not authorized.



---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = MASTER IMPLEMENTATION BASELINE CANDIDATE

### Canonical consolidation result

- Master path: docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1.md
- Master status: IMPLEMENTATION BASELINE CANDIDATE ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â NOT YET FROZEN.
- Canonical numbered sections: 103 (00 through 102).
- Directly consolidated unique sources: 56.
- Superseded semantic families excluded as current authority: at least 12.
- Historical-only standalone architecture/audit sources excluded from direct current authority: 2.
- Byte-identical historical copies were not re-merged.
- PM-014 Compiler ownership: RESOLVED IN MASTER Ãƒâ€šÃ‚Â§64.
- PM-020 Sequence QA: RESOLVED IN MASTER Ãƒâ€šÃ‚Â§77.
- MASTER_CONSOLIDATION_SELF_AUDIT_V1 = PASS.
- Unresolved canonical conflicts: 0.
- Blocking conflicts: 0.

### Important source-normalization decision

The source corpus defines canonical semantic Shot layers L1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“L8. It does not define authoritative semantic L9ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“L12.
The Master therefore preserves L1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“L8 and uses T9ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“T12 only as downstream technical realization aliases (Static Keyframe, Motion Delta, ShotIR, Provider Compilation), not invented semantic layers.

### Scope state

- Feature code changes: none.
- Dependency installation: none.
- Build execution: none.
- Runtime test execution: none.
- Commit: none.
- Historical source edits: none.
- Implementation baseline freeze: NOT DONE.
- Independent final Master audit: pending.
- Dependency graph: not created.
- Implementation task decomposition: not created.
- Feature coding: not authorized.



---

## Current Stage ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â 2026-09-22

previous_stage = MASTER FINAL AUDIT / BLOCKED

### Independent final audit result

- Audit: evidence/audits/FINAL_MASTER_INDEPENDENT_AUDIT_V1.md
- Verdict: FAIL.
- BLOCKER: 0.
- MAJOR: 8.
- MINOR: 0.
- NOTE: 2.
- Baseline freeze: BLOCKED.
- Master modification during audit: none.
- Historical source modification: none.

### Blocking-to-freeze MAJOR findings

1. FM-001 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â restore explicit narrative expansion projection/planning contracts.
2. FM-002 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â complete canonical Story/Pre-production lifecycle contracts.
3. FM-003 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â restore exact orthogonal GenerationJob state enums and transition ownership.
4. FM-004 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â restore explicit Electron security hardening baseline.
5. FM-005 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â define durable invalidation record/persistence and explicit reference-change propagation.
6. FM-006 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â allocate/trace post-V0.16 requirements required by final consolidation.
7. FM-007 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â resolve ApprovedEndState identity as non-shadow canonical state.
8. FM-008 ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â restore ShotEligibilityGate identity/version and re-evaluation lineage.

### Scope state

- Feature code changes: none.
- Runtime build/test: none.
- Dependency installation: none.
- Commit: none.
- Dependency graph: not created.
- Coding task decomposition: not created.
- Master freeze: not performed.
- Implementation-ready status: not granted.


---

## Current Stage - 2026-09-22

previous_stage = MASTER REPAIRED / RE-AUDIT REQUIRED

### FM-001 through FM-008 repair result

- Master remains IMPLEMENTATION BASELINE CANDIDATE - NOT YET FROZEN.
- Local repair evidence: evidence/audits/FINAL_MASTER_REPAIR_FM001_FM008_V1.md.
- FM-001 through FM-008: 8/8 REPAIRED by local consistency checks.
- Independent final re-audit: NOT RUN in this repair turn.
- Freeze: NOT PERFORMED.
- Dependency graph: NOT CREATED.
- Coding task decomposition: NOT CREATED.
- Feature code changes: none.
- Runtime build/test: none.
- Dependency installation: none.
- Commit: none.

NEXT_EXACT_ACTION = "RE-RUN INDEPENDENT FINAL MASTER AUDIT AFTER FM-001 THROUGH FM-008 REPAIR"
---

## Current Stage - 2026-09-22

previous_stage = MASTER FINAL AUDIT V2 / BLOCKED

### Independent Final Master Audit V2 result

- Audit: evidence/audits/FINAL_MASTER_INDEPENDENT_AUDIT_V2.md
- Verdict: FAIL.
- BLOCKER: 0.
- MAJOR: 6.
- MINOR: 1.
- NOTE: 1.
- Independent verification of prior findings: 6/8 fully verified; FM-003 and FM-006 remain incomplete.
- Confirmed repair-surfaced regression findings: 1.
- Baseline freeze: BLOCKED.
- Master modification during audit: none.
- Historical source modification: none.
- Feature code changes: none.
- Runtime build/test: none.
- Dependency installation: none.
- Commit: none.
- Dependency graph: not created.
- Coding task decomposition: not created.

### Open V2 findings

- FM2-001 - accepted post-V0.16 requirement IDs point to missing explicit contracts for SequencePlan, DurationBudget, SceneBudget, NarrativeTrace and ShotExpansion.
- FM2-002 - GenerationJob exact enums/owners are restored, but complete legal transition relation remains under-specified.
- FM2-003 - Ã‚Â§01 full component-contract completeness is not satisfied across many canonical components outside Ã‚Â§06-Ã‚Â§41.
- FM2-004 - Topic Intelligence incorrectly depends on Profile Resolver, creating bootstrap authority/order cycle.
- FM2-005 - StoryCore and StoryGraph inputs create a direct authority/order cycle.
- FM2-006 - required Narrative Expansion defect-code registry is missing.
- FM2-007 - Ã‚Â§102 has malformed literal \n row separators for 21 historical requirement IDs.
- FM2-008 - Ã‚Â§100 self-status wording is stale after independent Audit V2.

NEXT_EXACT_ACTION = "REPAIR EXACT FINAL MASTER AUDIT V2 FINDINGS"
---

## Current Stage - 2026-09-23

previous_stage = MASTER REPAIRED AFTER AUDIT V2 / RE-AUDIT REQUIRED

### FM2-001 through FM2-008 repair result

- Repair evidence: evidence/audits/FINAL_MASTER_REPAIR_FM2_001_FM2_008_V1.md.
- FM2-001 through FM2-008: 8/8 REPAIRED by local repair validation.
- Contract components audited: 62.
- Contract components incomplete: 0.
- Design dependency cycles: 0.
- Requirement IDs/rows: 112/112.
- Malformed requirement rows: 0.
- Source-required Narrative Expansion defect codes: 36/36.
- Repair regression self-check: 20/20 PASS.
- Independent Final Master Audit V3: NOT RUN in this repair turn.
- Baseline freeze: NOT PERFORMED.
- Implementation dependency graph: NOT CREATED.
- Implementation task decomposition: NOT CREATED.
- Feature code changes: none.
- Runtime build/test: none.
- Dependency installation: none.
- Commit: none.

Master remains IMPLEMENTATION BASELINE CANDIDATE - NOT YET FROZEN.

NEXT_EXACT_ACTION = "RUN INDEPENDENT FINAL MASTER AUDIT V3 AFTER FM2-001 THROUGH FM2-008 REPAIR"
---

## Current Stage - 2026-09-23

stage = MASTER FINAL AUDIT V3 / BLOCKED

### Independent Final Master Audit V3 result

- Audit: evidence/audits/FINAL_MASTER_INDEPENDENT_AUDIT_V3.md.
- Verdict: FAIL.
- BLOCKER: 0.
- MAJOR: 2.
- MINOR: 0.
- NOTE: 0.
- New V3 findings: FM3-001, FM3-002.
- V2 closure: 6 VERIFIED CLOSED, 1 NOT CLOSED, 1 REGRESSED.
- Canonical implementation-facing components audited: 101.
- Complete component contracts: 60.
- Incomplete component contracts: 41.
- N/A with reason: 204.
- Invalid N/A: 0.
- Requirement IDs/rows: 112/112.
- Malformed requirement rows: 0.
- Narrative Expansion defect registry: 36/36.
- GenerationJob transition rows: 62.
- Undeclared job states: 0.
- Illegal/ambiguous transition-row findings: 0.
- Canonical dependency cycle count: 0.
- Semantic L9-L12 count: 0.
- Master pre/post SHA identical: YES.
- Historical corpus unchanged: YES.
- Feature source unchanged: YES.
- Baseline freeze: BLOCKED / NOT PERFORMED.
- Implementation dependency graph: NOT CREATED.
- Implementation task decomposition: NOT CREATED.
- Feature code changes: none.
- Runtime build/test: none.
- Dependency installation: none.
- Commit: none.

Master remains IMPLEMENTATION BASELINE CANDIDATE - NOT YET FROZEN.

NEXT_EXACT_ACTION = "REPAIR EXACT FINAL MASTER AUDIT V3 FINDINGS"
---

## Active Repair Claim - 2026-09-25

claim = FM3-001 + FM3-002
scope = DESIGN-DOCUMENT REPAIR ONLY

- Feature code: LOCKED.
- Runtime build/test: NOT AUTHORIZED in this repair claim.
- Dependency installation: NOT AUTHORIZED.
- Commit: NOT AUTHORIZED before independent audit/freeze gate.
- Master baseline status: CANDIDATE / NOT YET FROZEN.

REPAIR_SEQUENCE = "FM3-001 CONTRACT COMPLETENESS -> FM3-002 MUTABLE COORDINATION SEMANTICS -> LOCAL SELF-AUDIT -> INDEPENDENT FINAL AUDIT -> FREEZE ONLY IF BLOCKER=0 AND MAJOR=0"

---

## Active Repair Claim - 2026-09-25

claim = FM3-001 + FM3-002
scope = DESIGN-DOCUMENT REPAIR ONLY

- Feature code: LOCKED.
- Runtime build/test: NOT AUTHORIZED in this repair claim.
- Dependency installation: NOT AUTHORIZED.
- Commit: NOT AUTHORIZED before independent audit/freeze gate.
- Master baseline status: CANDIDATE / NOT YET FROZEN.

REPAIR_SEQUENCE = "FM3-001 CONTRACT COMPLETENESS -> FM3-002 MUTABLE COORDINATION SEMANTICS -> LOCAL SELF-AUDIT -> INDEPENDENT FINAL AUDIT -> FREEZE ONLY IF BLOCKER=0 AND MAJOR=0"

---

## FM3 Repair Complete / Re-audit Required - 2026-09-25

- Repair evidence: evidence/audits/FINAL_MASTER_REPAIR_FM3_001_FM3_002_V1.md
- FM3-001 = REPAIRED by local validation.
- FM3-002 = REPAIRED by local validation.
- Component completeness = 101/101; incomplete = 0.
- Coordination generic immutable conflict in §63/§68/§69/§71 = 0.
- Requirement registry = 112/112.
- Narrative Expansion defect registry = 36/36.
- GenerationJob transition rows = 62.
- Independent Final Audit V4 = NOT RUN yet.
- Freeze = NOT PERFORMED.

stage = MASTER REPAIRED AFTER AUDIT V3 / RE-AUDIT REQUIRED
NEXT_EXACT_ACTION = "RUN INDEPENDENT FINAL MASTER AUDIT V4"

---

## Current Stage - 2026-09-25

stage = MASTER IMPLEMENTATION BASELINE V1 / FROZEN

- Frozen Master: docs/design/canonical/MASTER_AI_FILM_STUDIO_FINAL_IMPLEMENTATION_BASELINE_V1.md
- Freeze manifest: docs/design/canonical/MASTER_AI_FILM_STUDIO_IMPLEMENTATION_BASELINE_V1_FREEZE_MANIFEST.md
- Frozen SHA: 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- FINAL_MASTER_INDEPENDENT_AUDIT_V4 = PASS.
- FROZEN_MASTER_INDEPENDENT_AUDIT_V5 = PASS.
- BLOCKER = 0.
- MAJOR = 0.
- Component contracts = 101/101 complete.
- Requirements = 112/112.
- Narrative defect registry = 36/36.
- GenerationJob transitions = 62/62 audited.
- Canonical dependency cycles = 0.
- Semantic L9-L12 leakage = 0.
- Master design freeze = COMPLETE.
- Feature implementation complete = NO.
- Production/release ready = NO.

NEXT_EXACT_ACTION = "DERIVE IMPLEMENTATION DEPENDENCY GRAPH AND TASK DECOMPOSITION FROM FROZEN SHA"

---

## Active Implementation Task - 2026-09-25

task = IMP-001 FROZEN BASELINE GUARD
branch = chatgpt/IMP-001-frozen-baseline-guard
base_head = d7977fd51b87d4da2a25a05b896f5cdac064e030
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

status = CLAIMED / ANALYZE

Acceptance:
- canonical Master path is checked
- exact frozen SHA is checked
- freeze manifest path/SHA/verdict consistency is checked
- missing/mismatched files fail closed
- CLI returns nonzero on failure
- guard runs in normal CI before unit tests
- tests do not modify frozen Master
- frozen Master SHA remains unchanged after task verification

---

## IMP-001 Local Verification - 2026-09-25

status = LOCAL VERIFIED / REMOTE CI GATE PENDING

- guard CLI = PASS
- targeted Python 3.13 tests = 9/9 PASS
- local regression = 371 PASS / 3 deselected when excluding exact known Windows/POSIX-path assertions
- unfiltered Windows UTF-8 regression = 371 PASS / 3 known platform-specific failures
- workflow YAML = PASS
- git diff --check = PASS
- frozen Master SHA unchanged = YES
- evidence = evidence/tests/IMP-001_FROZEN_BASELINE_GUARD_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT INTENTIONAL FROZEN BASELINE + IMP-001 FILES, PUSH BRANCH, OPEN PR, VERIFY UBUNTU CI"

---

## IMP-001 MAIN VERIFIED - 2026-09-25

task = IMP-001 FROZEN BASELINE GUARD
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = bca229eee5a159a59cc880f48a0d62f1ac78fcc5
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

Evidence:
- evidence/tests/IMP-001_FROZEN_BASELINE_GUARD_EVIDENCE.md
- evidence/tests/IMP-001_MAIN_VERIFICATION_EVIDENCE.md
- fork PR #1 exact-head CI = SUCCESS
- post-merge Windows CRLF portability finding = FIXED
- fork PR #2 exact-head CI = SUCCESS
- fork main push workflow run 36112979014 = SUCCESS
- Python 3.10 guard + full unit suite = SUCCESS
- Python 3.13 guard + full unit suite = SUCCESS
- Windows main guard = PASS with CRLF->LF canonical normalization

Upstream status:
- crisng95/flowkit PR #65 remains OPEN / workflow approval required.
- Connected account cannot approve upstream fork workflow: HTTP 403 admin rights required.
- Upstream crisng95/flowkit:main is NOT claimed MAIN VERIFIED.

NEXT_EXACT_ACTION = "CLAIM IMP-002 CANONICAL CONTRACT PRIMITIVES"

---

## Active Implementation Task - 2026-09-25

task = IMP-002 CANONICAL CONTRACT PRIMITIVES
branch = chatgpt/IMP-002-canonical-contract-primitives
base_head = 373f34058c500220a90e18677350310ba61f5317
depends = IMP-001 MAIN VERIFIED
status = CLAIMED / ANALYZE COMPLETE / CODE NEXT

Acceptance:
- typed logical ID/version primitives
- exact source-version bindings
- provenance validation
- provider-neutral lifecycle/gate/finding-severity values
- immutable semantic-record metadata
- serialization/equality tests
- invalid ID/version/provenance rejection tests
- no provider fields in canonical primitive schemas
- frozen Master remains unchanged

---

## IMP-002 Local Verification - 2026-09-25

task = IMP-002 CANONICAL CONTRACT PRIMITIVES
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-002-canonical-contract-primitives

- targeted tests = 19/19 PASS
- Windows full unit suite = 407 PASS / 3 known platform-only failures
- unaffected local regression = 407 PASS / 3 deselected
- frozen Master guard = PASS
- frozen Master SHA unchanged
- provider-neutral schema test = PASS
- diff check = PASS
- evidence = evidence/tests/IMP-002_CANONICAL_CONTRACT_PRIMITIVES_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-002 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-002 MAIN VERIFIED - 2026-09-25

task = IMP-002 CANONICAL CONTRACT PRIMITIVES
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 49a5352fc29c096802ba1d088c5c9739c6be48c3
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #4 exact-head = 5d73a7ed6c5174f4c3370199a13e50a2e31ec1ce
- PR workflow run 36117186461 = SUCCESS
- exact-head review = PASS after missing OPEN gate value repair
- main merge = 49a5352fc29c096802ba1d088c5c9739c6be48c3
- local main guard = PASS
- local main targeted IMP-002 = 19/19 PASS
- main push workflow run 36117340581 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-003 ONE-WRITER PERSISTENCE / MIGRATION FOUNDATION"


---

## Active Implementation Task - 2026-09-25

task = IMP-003 ONE-WRITER PERSISTENCE / MIGRATION FOUNDATION
branch = chatgpt/IMP-003-one-writer-persistence
base_head = fc808402788772ba08347bfc5442e9731f8cc901
depends = IMP-002 MAIN VERIFIED
status = CLAIMED / ANALYZE COMPLETE / CODE NEXT

Acceptance:
- SQLite WAL
- synchronous=FULL
- foreign_keys=ON
- bounded one-writer command queue
- serialized canonical writes
- optimistic revision/CAS conflict rejection
- migration table/version compatibility gate
- separate reads allowed
- no-network-in-transaction guard
- frozen Master unchanged


---

## IMP-003 Local Verification - 2026-09-25

task = IMP-003 ONE-WRITER PERSISTENCE / MIGRATION FOUNDATION
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-003-one-writer-persistence

- one canonical writer per DB path = VERIFIED
- bounded write queue = VERIFIED
- short serialized transactions = VERIFIED
- WAL/FULL/foreign_keys = VERIFIED
- CAS stale-revision rejection = VERIFIED
- migration/version gate = VERIFIED
- separate query-only reads = VERIFIED
- no-network transaction guard = VERIFIED
- targeted Studio tests = 31/31 PASS
- Windows full unit suite = 420 PASS / 3 known platform-only failures
- unaffected local regression = 420 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-003_ONE_WRITER_PERSISTENCE_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-003 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-003 MAIN VERIFIED - 2026-09-25

task = IMP-003 ONE-WRITER PERSISTENCE / MIGRATION FOUNDATION
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 661fdba57520cf25106d644cd143e82936b0451c
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #6 exact-head = 1610b7194ef63d21a57586bae69d99ac6ff667ed
- PR workflow run 36122183881 = SUCCESS
- exact-head review = PASS
- main merge = 661fdba57520cf25106d644cd143e82936b0451c
- local main guard = PASS
- local main targeted IMP-003 = 12/12 PASS
- main push workflow run 36122334589 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-004 VERSION / PROVENANCE REPOSITORY PRIMITIVES"


---

## Active Implementation Task - 2026-09-25

task = IMP-004 VERSION / PROVENANCE REPOSITORY PRIMITIVES
branch = chatgpt/IMP-004-version-provenance-repository
base_head = 0e284bed36aa6335d561b0cbe4a7ee304356933a
depends = IMP-003 MAIN VERIFIED
status = CLAIMED / ANALYZE COMPLETE / CODE NEXT

Acceptance:
- immutable semantic version rows
- provenance persisted and read back
- successor creation with explicit predecessor
- durable supersession history
- current pointer/status stored separately
- current pointer update protected by CAS revision
- stale CAS rejected
- restart/readback preserved
- frozen Master unchanged


---

## IMP-004 Local Verification - 2026-09-25

task = IMP-004 VERSION / PROVENANCE REPOSITORY PRIMITIVES
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-004-version-provenance-repository

- immutable semantic version rows = VERIFIED
- provenance persistence/readback = VERIFIED
- successor + supersession history = VERIFIED
- current pointer/status separation = VERIFIED
- current pointer CAS = VERIFIED
- stale CAS rejection = VERIFIED
- restart/readback = VERIFIED
- schema V1 → V2 migration = VERIFIED
- targeted Studio tests = 39/39 PASS
- Windows full unit suite = 428 PASS / 3 known platform-only failures
- unaffected local regression = 428 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-004_VERSION_PROVENANCE_REPOSITORY_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-004 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-004 MAIN VERIFIED - 2026-09-25

task = IMP-004 VERSION / PROVENANCE REPOSITORY PRIMITIVES
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = a5299e88195f8feaf94c1ddf9016ea31af01b84f
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #8 exact-head = 22d6b341b459518e29764118d5bff992ab575776
- PR workflow run 36123423488 = SUCCESS
- exact-head review = PASS
- main merge = a5299e88195f8feaf94c1ddf9016ea31af01b84f
- local main guard = PASS
- local main targeted IMP-004 = 8/8 PASS
- main push workflow run 36163372531 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-005 DEPENDENCYGRAPH + DURABLE INVALIDATIONRECORD"


---

## Active Implementation Task - 2026-09-25

task = IMP-005 DEPENDENCYGRAPH + DURABLE INVALIDATIONRECORD
branch = chatgpt/IMP-005-dependency-invalidation
base_head = d88af1be0d812c20038cd970b663d99c821f1467
depends = IMP-004 MAIN VERIFIED
status = CLAIMED / AUTHORITY READ / CODE NEXT

Acceptance:
- DependencyGraph owns typed edge truth
- exact source/consumer version refs
- deterministic direct/transitive reachability
- unrelated descendants preserved
- InvalidationRecord does not invent edges
- immutable cause/source/affected/edge evidence
- deterministic active dedupe
- unresolved → resolved lifecycle via CAS
- restart/readback unresolved replay
- frozen Master unchanged


---

## IMP-005 Local Verification - 2026-09-25

task = IMP-005 DEPENDENCYGRAPH + DURABLE INVALIDATIONRECORD
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-005-dependency-invalidation

- exact-version edge truth = VERIFIED
- forward/reverse reachability = VERIFIED
- selective descendant invalidation = VERIFIED
- unrelated descendants preserved = VERIFIED
- deterministic dedupe/idempotency = VERIFIED
- immutable cause/source/affected/edge evidence = VERIFIED
- unresolved → resolved CAS lifecycle = VERIFIED
- transition history = VERIFIED
- restart unresolved replay = VERIFIED
- schema V2 → V3 migration = VERIFIED
- targeted cluster = 28/28 PASS
- Windows full unit suite = 436 PASS / 3 known platform-only failures
- unaffected local regression = 436 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-005_DEPENDENCY_INVALIDATION_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-005 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-005 MAIN VERIFIED - 2026-09-25

task = IMP-005 DEPENDENCYGRAPH + DURABLE INVALIDATIONRECORD
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 8e07bb1066b0d0b75b5050c005a443ea71b5ee10
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #10 exact-head = af74ea8896ac6df7e328283614df3ef23b0141f8
- PR workflow run 36166026866 = SUCCESS
- exact-head review = PASS
- main merge = 8e07bb1066b0d0b75b5050c005a443ea71b5ee10
- local main guard = PASS
- local main targeted IMP-005 = 8/8 PASS
- main push workflow run 36166182569 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-006 OBSERVABILITY / ERROR / EVIDENCE CORE"


---

## Active Implementation Task - 2026-09-26

task = IMP-006 OBSERVABILITY / ERROR / EVIDENCE CORE
branch = chatgpt/IMP-006-observability-error-evidence
base_head = 77c828f04c1a40027dbf7f0172121d9582e1c8d8
depends = IMP-004 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT NEXT

Acceptance:
- typed correlation IDs
- typed structured decision/failure events
- secret/token redaction
- evidence references to exact source/version context
- error taxonomy integration
- event/evidence never becomes current-state authority
- provider-neutral contracts
- frozen Master unchanged


---

## IMP-006 Local Verification - 2026-09-26

task = IMP-006 OBSERVABILITY / ERROR / EVIDENCE CORE
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-006-observability-error-evidence

- typed correlation IDs/context propagation = VERIFIED
- exact frozen ErrorClass taxonomy = VERIFIED
- provider ambiguity reconciliation semantics = VERIFIED
- structured decision/failure events = VERIFIED
- evidence references + exact source-version bindings = VERIFIED
- recursive secret redaction = VERIFIED
- append-only event persistence = VERIFIED
- event != current-state authority = VERIFIED
- schema V3 → V4 migration = VERIFIED
- targeted IMP-006 = 10/10 PASS
- Studio cluster = 57/57 PASS
- Windows full unit suite = 446 PASS / 3 known platform-only failures
- unaffected local regression = 446 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-006_OBSERVABILITY_ERROR_EVIDENCE_CORE_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-006 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-006 MAIN VERIFIED - 2026-09-26

task = IMP-006 OBSERVABILITY / ERROR / EVIDENCE CORE
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 9aaa98e757adbb5f30deea502c6a1f5cce9e06e1
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #12 exact-head = 8d371dec245bec4794b13d21a55e9749041180d8
- PR workflow run 36211006621 = SUCCESS
- exact-head review = PASS after vendor-prefixed secret-key redaction repair
- main merge = 9aaa98e757adbb5f30deea502c6a1f5cce9e06e1
- local main guard = PASS
- local main targeted IMP-006 = 10/10 PASS
- main push workflow run 36211125971 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-010 PROJECT / TOPIC / DOMAIN RESOLUTION"


---

## Active Implementation Task - 2026-09-26

task = IMP-010 PROJECT / TOPIC / DOMAIN RESOLUTION
branch = chatgpt/IMP-010-project-topic-domain
base_head = 1c22e61bbe34538317f8f83df092482b62ec1ede
depends = IMP-004 + IMP-006 MAIN VERIFIED
status = CLAIMED / AUTHORITY READ / CODE NEXT

Acceptance:
- typed ProjectBootstrapInput
- typed TopicResolution
- typed Domain/Niche/Genre Resolution
- exact-version provenance for project input + rule/evaluator/registry metadata
- ambiguity explicit, never silently collapsed
- unknown niche explicit; hybrid niches allowed
- hard project constraints override soft classifier preferences
- Topic interface cannot accept ActiveProductionProfile/ProfileResolver
- provider-specific FlowKit fields absent from canonical contracts
- persistence through immutable VersionRepository
- frozen Master unchanged


---

## IMP-010 Local Verification - 2026-09-26

task = IMP-010 PROJECT / TOPIC / DOMAIN RESOLUTION
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-010-project-topic-domain

- typed ProjectBootstrapInput = VERIFIED
- typed TopicResolution = VERIFIED
- typed Domain/Niche/Genre Resolution = VERIFIED
- exact-version provenance = VERIFIED
- ambiguity explicit = VERIFIED
- unknown/hybrid niche semantics = VERIFIED
- hard constraints > soft classifier preferences = VERIFIED
- no final ActiveProductionProfile/ProfileResolver dependency = VERIFIED
- no provider-specific canonical fields = VERIFIED
- VersionRepository persistence round-trip = VERIFIED
- targeted IMP-010 = 12/12 PASS
- Windows full unit suite = 458 PASS / 3 known platform-only failures
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-010_PROJECT_TOPIC_DOMAIN_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-010 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-010 MAIN VERIFIED - 2026-09-26

task = IMP-010 PROJECT / TOPIC / DOMAIN RESOLUTION
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = ed5fb0ff0aff746b3991c52f32b282fdec7e444a
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #14 exact-head = 6dca6a53bc5733aa9cd93cfd0c13ad15e279543e
- PR workflow run 36225161135 = SUCCESS
- exact-head review = PASS
- main merge = ed5fb0ff0aff746b3991c52f32b282fdec7e444a
- local main guard = PASS
- local main targeted IMP-010 = 12/12 PASS
- main push workflow run 36225238363 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-011 BRAINPACK REGISTRY"


---

## Active Implementation Task - 2026-09-26

task = IMP-011 BRAINPACK REGISTRY
branch = chatgpt/IMP-011-brainpack-registry
base_head = 096ed0109e25390e5ebb2bb1e1eaf146d7c7b5df
depends = IMP-010 MAIN VERIFIED
status = CLAIMED / AUTHORITY READ / STORAGE DESIGN NEXT

Acceptance:
- one registry only
- immutable pack definitions with pack_id + pack_version
- canonical pack family classification
- StoryBrainPack specialization, not parallel registry
- exact parent pack version refs
- applicability metadata
- DRAFT / VALIDATED / FROZEN / DEPRECATED registry lifecycle
- published versions immutable
- provenance + license/source evidence required
- cycle detection for parent inheritance
- registry never resolves effective project policy
- frozen Master unchanged


---

## IMP-011 Local Verification - 2026-09-26

task = IMP-011 BRAINPACK REGISTRY
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-011-brainpack-registry

- one canonical registry = VERIFIED
- immutable pack definitions = VERIFIED
- canonical pack families = VERIFIED
- Story specialization in same registry = VERIFIED
- exact parent version refs = VERIFIED
- logical inheritance cycle rejection = VERIFIED
- typed applicability/rules = VERIFIED
- source/license provenance = VERIFIED
- donor adaptation/validation gate = VERIFIED
- registry lifecycle DRAFT/VALIDATED/FROZEN/DEPRECATED = VERIFIED
- lifecycle CAS/history/DB guards = VERIFIED
- schema V4 → V5 migration = VERIFIED
- targeted IMP-011 = 11/11 PASS
- cluster = 33/33 PASS
- Windows full unit suite = 469 PASS / 3 known platform-only failures
- unaffected local regression = 469 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-011_BRAINPACK_REGISTRY_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-011 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-011 MAIN VERIFIED - 2026-09-26

task = IMP-011 BRAINPACK REGISTRY
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = e9347bf7b7b8d34418e268d3bdd11538345c172d
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #16 exact-head = 74f27ad287aa9f87b5acb93bde6d7faebedf1ace
- PR workflow run 36227308533 = SUCCESS
- exact-head review = PASS
- main merge = e9347bf7b7b8d34418e268d3bdd11538345c172d
- local main guard = PASS
- local main targeted IMP-011 = 11/11 PASS
- main push workflow run 36227414264 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-012 PROFILE RESOLVER"


---

## Active Implementation Task - 2026-09-26

task = IMP-012 PROFILE RESOLVER
branch = chatgpt/IMP-012-profile-resolver
base_head = 5b4edba7ef1a7c9da61cb6acc4de75592440d9f3
depends = IMP-011 + IMP-005 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT NEXT

Acceptance:
- one Profile Resolver authority
- exact-version Topic/Domain/BrainPack inputs
- locked facts > hard constraints > allowed project overrides > inherited pack policy > soft preferences > allowed local intent
- hard-hard unresolved conflict = FAIL
- non-allowlisted project override rejected
- every effective field has source/version/precedence/reason trace
- deterministic/reproducible output for exact inputs
- downstream cannot re-resolve pack stack independently
- no provider/model fields
- frozen Master unchanged


---

## IMP-012 Local Verification - 2026-09-26

task = IMP-012 PROFILE RESOLVER
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-012-profile-resolver

- one Profile Resolver authority = VERIFIED
- exact Project/Topic/Domain/BrainPack inputs = VERIFIED
- locked > hard > override > pack > soft > local precedence = VERIFIED
- hard-hard unresolved conflict = FAIL CLOSED
- project/local overrides require allowlist = VERIFIED
- inherited pack composition/override rules = VERIFIED
- all direct/inherited candidate packs require FROZEN = VERIFIED
- immutable ResolutionTrace = VERIFIED
- every field winner/contender has exact source/version/reason = VERIFIED
- all consumed exact source versions persisted in provenance = VERIFIED
- deterministic/reproducible result = VERIFIED
- ActiveProductionProfile remains IMP-013 authority = VERIFIED
- targeted IMP-012 = 15/15 PASS
- Windows full unit suite = 484 PASS / 3 known platform-only failures
- unaffected local regression = 484 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-012_PROFILE_RESOLVER_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-012 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-012 MAIN VERIFIED - 2026-09-26

task = IMP-012 PROFILE RESOLVER
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 99e50aa186222d8ecaefc1db479b15d3343af1b2
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #18 exact-head = dcea5c5338284b4bfb90d503cee39364450e70c1
- PR workflow run 36234288304 = SUCCESS
- exact-head review = PASS
- main merge = 99e50aa186222d8ecaefc1db479b15d3343af1b2
- local main guard = PASS
- local main targeted IMP-012 = 15/15 PASS
- main push workflow run 36234468266 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-013 ACTIVEPRODUCTIONPROFILE"


---

## Active Implementation Task - 2026-09-26

task = IMP-013 ACTIVEPRODUCTIONPROFILE
branch = chatgpt/IMP-013-active-production-profile
base_head = 8942b06a2ebf9b67392a95222fe452ceaea12572
depends = IMP-012 + IMP-005 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT NEXT

Acceptance:
- immutable pinned profile snapshot
- exact upstream/version bindings
- effective policy and path provenance preserved
- no in-place semantic mutation
- successor version on re-resolution
- deterministic changed-path delta
- selective dependency-aware invalidation
- downstream exact profile-version binding
- no pack re-resolution downstream
- frozen Master unchanged


---

## IMP-013 Local Verification - 2026-09-26

task = IMP-013 ACTIVEPRODUCTIONPROFILE
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-013-active-production-profile

- immutable pinned ActiveProductionProfile = VERIFIED
- exact identity/version persistence = VERIFIED
- exact effective-policy provenance snapshot = VERIFIED
- deterministic changed-path delta = VERIFIED
- successor version on re-resolution = VERIFIED
- selective dependency-aware invalidation = VERIFIED
- unrelated profile-path branches preserved = VERIFIED
- forged reachability plan rejected = VERIFIED
- downstream exact profile binding/no re-resolution = VERIFIED
- targeted IMP-013 = 10/10 PASS
- exact-head unaffected regression = 494 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-013_ACTIVE_PRODUCTION_PROFILE_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-013 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-013 MAIN VERIFIED - 2026-09-26

task = IMP-013 ACTIVEPRODUCTIONPROFILE
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 62d4efccbaf940e1b18016d39014ba13ec648e96
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #20 exact-head = f73f85ef31c6bbb33708c59d05bf721760381675
- PR workflow run 36237614198 = SUCCESS
- exact-head review = PASS
- main merge = 62d4efccbaf940e1b18016d39014ba13ec648e96
- local main guard = PASS
- local main targeted IMP-013 = 10/10 PASS
- main push workflow run 36237749060 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-020 IDEA / LOGLINE / PREMISE / ANGLE / THEME"


---

## Active Implementation Task - 2026-09-26

task = IMP-020 IDEA / LOGLINE / PREMISE / ANGLE / THEME
branch = chatgpt/IMP-020-story-intake-core
base_head = c182a8d61261fceee890d4c48efd57240459df74
depends = IMP-002 + IMP-004 + IMP-013 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT NEXT

Acceptance:
- Idea, Logline, Premise, Angle, Theme are distinct canonical artifacts
- exact IDs/versions/provenance
- accepted versions immutable
- semantic change creates successor
- blocking premise/logline defects fail closed
- no project.story shadow authority
- ActiveProductionProfile exact-version binding where policy applies
- provider-neutral contracts
- frozen Master unchanged


---

## IMP-020 Local Verification - 2026-09-26

task = IMP-020 IDEA / LOGLINE / PREMISE / ANGLE / THEME
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-020-story-intake-core

- typed Idea = VERIFIED
- typed Logline = VERIFIED
- typed Premise = VERIFIED
- typed Angle = VERIFIED
- typed Theme = VERIFIED
- immutable VersionRepository persistence = VERIFIED
- exact source/version provenance = VERIFIED
- exact ActiveProductionProfile binding = VERIFIED
- stage-local blocking gates = VERIFIED
- stale parent/profile gate = VERIFIED
- successor history immutability = VERIFIED
- legacy project.story compatibility-only boundary = VERIFIED
- targeted IMP-020 = 13/13 PASS
- Windows full unit suite = 507 PASS / 3 known platform-only failures
- unaffected regression = 507 PASS / 3 deselected
- frozen Master guard = PASS
- evidence = evidence/tests/IMP-020_STORY_INTAKE_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-020 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-020 MAIN VERIFIED - 2026-09-26

task = IMP-020 IDEA / LOGLINE / PREMISE / ANGLE / THEME
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 1ea70be1a6a284009f7c399299c4eab027858d21
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #22 exact-head = ef423abbbfbd26c3e0e4258e60712138995caf5c
- PR workflow run 36257856395 = SUCCESS
- exact-head review = PASS
- main merge = 1ea70be1a6a284009f7c399299c4eab027858d21
- local main guard = PASS
- local main targeted IMP-020 = 13/13 PASS
- main push workflow run 36257937119 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "READ TASK QUEUE AND CLAIM NEXT DEPENDENCY-READY STORY TASK"


---

## Active Implementation Task - 2026-09-26

task = IMP-021 RESEARCH INTELLIGENCE + STORYMATERIAL
branch = chatgpt/IMP-021-research-story-material
base_head = 1e957e900a4d9d5387cdfc8d88a96c7b836d5e7b
depends = IMP-020 + IMP-006 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT NEXT

Acceptance:
- ResearchBrief typed canonical contract
- EvidenceClaim exact source/version provenance
- certainty/dispute/contradiction represented explicitly
- StoryMaterial derived without changing evidence truth
- unsupported synthesis rejected
- immutable versions + exact provenance
- pinned ActiveProductionProfile where consumed
- provider-neutral contracts
- frozen Master unchanged


---

## IMP-021 Local Verification - 2026-09-29

task = IMP-021 RESEARCH INTELLIGENCE + STORYMATERIAL
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-021-research-story-material
base_head = 1e957e900a4d9d5387cdfc8d88a96c7b836d5e7b
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- typed ResearchBrief = VERIFIED
- typed EvidenceClaim with exact source/version provenance = VERIFIED
- explicit certainty/dispute/contradiction semantics = VERIFIED
- typed StoryMaterial transformation without factual-authority uplift = VERIFIED
- unsupported synthesis rejection = VERIFIED
- stale/non-current claim support rejection = VERIFIED
- stale/unlocked ActiveProductionProfile rejection = VERIFIED
- immutable version/successor semantics = VERIFIED
- targeted IMP-021 = 10/10 PASS
- full Windows unit suite = 517 PASS / 3 exact known POSIX-path failures
- unaffected regression = 517 PASS / 3 deselected
- frozen Master guard = PASS
- diff check = PASS
- evidence = evidence/tests/IMP-021_RESEARCH_STORY_MATERIAL_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-021 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-021 Exact-Head Review Repair - 2026-09-29

task = IMP-021 RESEARCH INTELLIGENCE + STORYMATERIAL
status = LOCAL VERIFIED AFTER REVIEW REPAIR / UPDATED PR CI PENDING

- canonical TopicResolution logical identity = VERIFIED
- canonical DomainResolution logical identity = VERIFIED
- exact-current accepted Topic/Domain promotion gates = VERIFIED
- stale/noncanonical Topic/Domain bindings fail closed = VERIFIED
- targeted IMP-021 = 13/13 PASS
- full Windows unit suite = 520 PASS / 3 exact known POSIX-path failures
- unaffected regression = 520 PASS / 3 deselected
- frozen Master guard = PASS
- feature scope remains agent/studio + tests + governance/evidence only

NEXT_EXACT_ACTION = "COMMIT REVIEW REPAIR AND UPDATE PR #24"


---

## IMP-021 MAIN VERIFIED - 2026-09-29

task = IMP-021 RESEARCH INTELLIGENCE + STORYMATERIAL
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 6370e1174b111a69c08f842224f335db42d160ad
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #24 final exact head = 9e39583e8d5b794c30880f69c1d01ecbcf0499ee
- updated-head PR workflow run 36543849753 = SUCCESS
- exact-head review = PASS after exact TopicResolution/DomainResolution authority repair
- main merge = 6370e1174b111a69c08f842224f335db42d160ad
- local main frozen guard = PASS
- local main targeted IMP-021 = 13/13 PASS
- main push workflow run 36544062680 = SUCCESS
- Python 3.10/3.13 full unit CI = SUCCESS

NEXT_EXACT_ACTION = "READ TASK QUEUE / IMPLEMENTATION DEPENDENCY GRAPH AND CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-040 Local Verification - 2026-09-29

task = IMP-040 CANONICAL ENTITY VERSIONING ADAPTER
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-040-canonical-entity-versioning
base_head = 726f44eb8d3c656630e94d2e69e7740340fd56eb
depends = IMP-004 MAIN VERIFIED
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

Acceptance verified locally:
- stable canonical entity logical identity = VERIFIED
- immutable semantic EntityVersion successors = VERIFIED
- current legacy Character/entity mapping = VERIFIED
- project linkage retained = VERIFIED
- reference media/provider-facing prompt excluded from canonical Entity truth = VERIFIED
- no second canonical Entity store/table = VERIFIED
- shared VersionRepository persistence/readback = VERIFIED
- frozen Master unchanged = VERIFIED

Test evidence:
- targeted IMP-040 = 7/7 PASS
- related cluster = 35/35 PASS
- full Windows unit suite = 527 PASS / 3 known platform-only failures
- unaffected regression = 527 PASS / 3 deselected
- evidence = evidence/tests/IMP-040_CANONICAL_ENTITY_VERSIONING_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-040 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-040 MAIN VERIFIED - 2026-09-29

task = IMP-040 CANONICAL ENTITY VERSIONING ADAPTER
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 01830d2a90f37ab4cac86f360798611940c07065
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #25 exact head = ed33a8bb7e2052c765d669d43008df3483d7b448
- PR workflow run 36551985402 = SUCCESS
- exact-head review = PASS
- main merge = 01830d2a90f37ab4cac86f360798611940c07065
- local main frozen guard = PASS
- local main targeted IMP-040 = 7/7 PASS
- main push workflow run 36552171606 = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE"


---

## Active Implementation Task - 2026-09-29

task = IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE
branch = chatgpt/IMP-022-character-state
base_head = 67cb0462c4e67f1dad3f02078358a35722e0a95c
depends = IMP-020 + IMP-021 + IMP-040 MAIN VERIFIED
status = CLAIMED / AUTHORITY AUDIT COMPLETE / IMPLEMENTATION NEXT

Acceptance:
- CharacterModelVersion uses canonical EntityVersion identity and remains separate from visual/reference truth
- psychology fields include want/need/fear/formative pressure/mistaken belief/values/secrets/tactics/boundaries/arc hypothesis where applicable
- RelationshipState has stable participant identity, predecessor chronology and causal change evidence
- CharacterKnowledgeState separates objective truth, knowledge, belief/suspicion/misbelief and optional audience knowledge
- impossible knowledge without acquisition/inference evidence is rejected
- accepted/current parent versions are exact and stale inputs fail closed
- versions are immutable and semantic change creates successors
- provider-neutral contracts
- frozen Master unchanged


---

## IMP-022 Local Verification - 2026-09-29

task = IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE
status = LOCAL VERIFIED / REMOTE CI GATE PENDING
branch = chatgpt/IMP-022-character-state
base_head = 67cb0462c4e67f1dad3f02078358a35722e0a95c
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- canonical CharacterModelVersion = VERIFIED
- canonical RelationshipState = VERIFIED
- canonical CharacterKnowledgeState = VERIFIED
- psychology remains separate from visual Entity/Reference truth = VERIFIED
- pre-core psychology remains DRAFT until exact StoryCore binding = VERIFIED
- objective truth / acquisition / inference / belief / audience tracks = VERIFIED
- impossible knowledge fails closed = VERIFIED
- relationship chronology and causal evidence = VERIFIED
- knowledge chronology and stale evidence rejection = VERIFIED
- dependency edges + durable invalidation on EntityVersion change = VERIFIED
- targeted IMP-022 = 11/11 PASS
- affected regression cluster = 60/60 PASS
- largest valid unaffected regression = 509 PASS / 3 deselected
- local full suite env-blocked by missing ffmpeg plus 3 known Windows/POSIX assertions
- frozen Master guard = PASS
- diff check = PASS
- evidence = evidence/tests/IMP-022_CHARACTER_STATE_EVIDENCE.md

NEXT_EXACT_ACTION = "COMMIT IMP-022 AND RUN REMOTE PR/CI LIFECYCLE"


---

## IMP-022 Exact-Head Review Repair - 2026-09-29

task = IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE
status = LOCAL VERIFIED AFTER POST-MERGE REVIEW REPAIR / FOLLOW-UP PR PENDING

- existing objective/acquisition/inference exact-current gates = REVERIFIED
- EntityKind.CHARACTER gate for psychology/knowledge = VERIFIED
- exact-source preflight before semantic persistence = VERIFIED
- targeted IMP-022 = 13/13 PASS
- affected regression cluster = 74/74 PASS
- largest valid unaffected regression = 511 PASS / 3 deselected
- frozen Master guard = PASS
- compile + diff check = PASS

NEXT_EXACT_ACTION = "PUSH REPAIR BRANCH AND OPEN SEPARATE PR"

---

## IMP-022 Post-Merge Repair Routing - 2026-09-29

task = IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE
status = POST-MERGE REVIEW REPAIR / NEW PR REQUIRED

- original PR #27 = MERGED at 2b1d0cfee1fd636300792266d5dce7473a420fff
- original PR #27 CI = SUCCESS
- main push run 36597573229 = SUCCESS
- review repair HEAD = 114fd87d2d40ca8fbfd53150653e1b4b38482b53
- repair is not yet on main

NEXT_EXACT_ACTION = "PUSH REPAIR BRANCH AND OPEN SEPARATE PR"


---

## IMP-022 MAIN VERIFIED - 2026-09-29

task = IMP-022 CHARACTER PSYCHOLOGY / RELATIONSHIP / KNOWLEDGE
status = MAIN VERIFIED
verified_repository = nguyenkhactang922-bot/flowkit
verified_main_sha = 3bde9b95f3da641c89c7d140d9e261780ad63191
frozen_master_sha = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

- PR #27 feature CI Python 3.10/3.13 = SUCCESS
- PR #28 hardening CI run 36599061352 = SUCCESS
- final exact-head review = PASS
- local final main targeted IMP-022 = 13/13 PASS
- main push workflow run 36599591595 = SUCCESS

NEXT_EXACT_ACTION = "CLAIM IMP-023 STORYCORE + CAUSAL STORYGRAPH + LOCK"

---

## IMP-023 Claim / Resume - 2026-09-30

ACTIVE_TASK = IMP-023 STORYCORE + CAUSAL STORYGRAPH + LOCK
BRANCH = chatgpt/IMP-023-storycore-causal-lock
BASE_HEAD = 0bc64459a5cb3a7e084e8e825381d98ba21b7875
DEPENDS = IMP-020, IMP-021, IMP-022, IMP-005 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
STATUS = ACTIVE
WORKTREE_NOTE = _incoming/ remains untracked and out of task scope

Scope:
- one stable story_core_id with immutable DRAFT and FROZEN_FOR_STRUCTURE successor versions
- typed ConflictModel/StakesModel exact-version boundary required by Frozen Master section 21/22
- typed causal StoryGraph nodes/edges built from exact StoryCore DRAFT
- causal validation evidence with orphan/gap/illegal-cycle fail-closed checks
- lock transition gated by exact current inputs + matching passing graph validation
- dependency registration + selective invalidation on StoryCore revision
- no provider/prompt authority leakage and no second StoryCore truth

NEXT_EXACT_ACTION = "IMPLEMENT IMP-023 CONTRACTS/REPOSITORIES/GATES + TARGETED TESTS"

---

## IMP-023 Targeted Test Checkpoint - 2026-09-30

STATUS = TARGETED TEST PASS
BRANCH = chatgpt/IMP-023-storycore-causal-lock
HEAD = 0bc64459a5cb3a7e084e8e825381d98ba21b7875
TARGETED_COMMAND = uv run --isolated --no-project --python 3.13 --with-requirements requirements.txt --with-requirements requirements-dev.txt python -m pytest tests/unit/test_studio_story_core.py -q
TARGETED_RESULT = 9 passed in 3.89s
TARGETED_EXIT_CODE = 0

NEXT_EXACT_ACTION = "RUN IMP-023 AFFECTED REGRESSION"

---

## IMP-023 Local Verification - 2026-09-30

IMP-023 = LOCAL VERIFIED
BRANCH = chatgpt/IMP-023-storycore-causal-lock
BASE_HEAD = 0bc64459a5cb3a7e084e8e825381d98ba21b7875

Evidence:
- evidence/tests/IMP-023_STORYCORE_CAUSAL_LOCK_EVIDENCE.md
- targeted IMP-023 = 12/12 PASS
- affected regression = 77/77 PASS
- largest valid Windows regression = 523 PASS / 3 known POSIX-path cases deselected
- test_video_reviewer excluded because FileMCP environment has no ffmpeg on PATH (pre-existing IMP-022 environment blocker)
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- exact-head self-review found and repaired character/core + conflict/stakes lineage and stale-graph-validation gaps
- git diff --check = PASS before evidence/state sync
- _incoming/ remains untracked and outside scope

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD → COMMIT IMP-023 → PUSH → PR → UBUNTU CI → EXACT-HEAD REVIEW → MERGE MAIN → VERIFY MAIN"


---

## IMP-023 PR #30 Exact-Head Review Repair - 2026-09-30

PR = #30
PRE_REPAIR_HEAD = 98225f121d71145327ec1fe3fb7a1866b5df87aa
PRE_REPAIR_CI_RUN = 36669953970
PRE_REPAIR_CI = Python 3.10 SUCCESS / Python 3.13 SUCCESS
REVIEW_RESULT = REPAIR REQUIRED

Review finding:
- revision APIs could branch from a historical non-current predecessor;
- frozen StoryCore lock manifest did not schema-reject cross-project StoryGraph/validation IDs.

Post-repair local evidence:
- targeted IMP-023 = 17/17 PASS
- affected regression = 82/82 PASS
- largest valid Windows regression = 528 PASS / 3 known POSIX-path cases deselected
- frozen Master guard = PASS
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

STATUS = REPAIR LOCAL VERIFIED / REPAIR COMMIT+PUSH PENDING
NEXT_EXACT_ACTION = "COMMIT EXACT-HEAD REVIEW REPAIR -> PUSH TO PR #30 -> NEW CI -> FINAL REVIEW -> MERGE MAIN"


---

## IMP-023 MAIN VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-023 STORYCORE + CAUSAL STORYGRAPH + LOCK
FINAL_STATUS = MAIN VERIFIED

Feature branch:
- chatgpt/IMP-023-storycore-causal-lock
- initial feature commit = 98225f121d71145327ec1fe3fb7a1866b5df87aa
- exact-head review repair commit = 83bcc387bcd7116b8312a54e763f2ce745c52d88

Pull request:
- PR #30 = MERGED
- final exact head = 83bcc387bcd7116b8312a54e763f2ce745c52d88
- merge commit / verified main SHA = b0a1663ef5155e7a98711cfddfb5bef264962269
- exact-head PR CI run 36670609338 = SUCCESS
- Python 3.10 = SUCCESS
- Python 3.13 = SUCCESS
- frozen Master baseline step = SUCCESS in both jobs
- full unit tests = SUCCESS in both jobs

Local final main verification:
- frozen Master guard = PASS
- frozen semantic SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- targeted IMP-023 = 17/17 PASS
- affected regression = 82/82 PASS
- worktree = only pre-existing untracked _incoming/

Main push verification:
- workflow run 36670754503
- event = push
- head SHA = b0a1663ef5155e7a98711cfddfb5bef264962269
- conclusion = SUCCESS
- unit (3.10) = SUCCESS
- unit (3.13) = SUCCESS
- Verify frozen Master baseline = SUCCESS in both jobs
- Run unit tests = SUCCESS in both jobs

Exact-head review:
- initial review found character-to-StoryCore / conflict-stakes lineage and stale graph-validation gaps and they were repaired before initial feature commit completion;
- final PR review found stale historical predecessor branching plus cross-project lock-manifest refs and they were repaired in 83bcc387bcd7116b8312a54e763f2ce745c52d88;
- final exact-head review after repair = PASS.

Evidence:
- evidence/tests/IMP-023_STORYCORE_CAUSAL_LOCK_EVIDENCE.md

IMP-023 DONE CRITERIA:
- one stable story_core_id = SATISFIED
- DRAFT -> graph validation -> FROZEN_FOR_STRUCTURE successor = SATISFIED
- no StoryCore/StoryGraph lock cycle = SATISFIED
- causal gap/orphan/cycle gates = SATISFIED
- exact-version provenance and stale-input fail-closed = SATISFIED
- dependency invalidation = SATISFIED
- no second StoryCore authority = SATISFIED

NEXT_EXACT_ACTION = "CLAIM IMP-024 STRUCTUREPROFILE / MACROBEATSHEET / DURATIONBUDGET"


---

## IMP-024 CLAIM / RESUME - 2026-09-30

ACTIVE_TASK = IMP-024 STRUCTUREPROFILE / MACROBEATSHEET / DURATIONBUDGET
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-024-structure-profile-budget
BASE_HEAD = 066ce0f2f0c53943fab2e5147ba8d05f48a02cde
DEPENDS = IMP-023 MAIN VERIFIED + IMP-013 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE = only pre-existing untracked _incoming/ outside task scope

Acceptance:
- StructureProfile is immutable provider-neutral planning policy, not narrative truth.
- MacroBeatSheet is projection/manifest only and does not duplicate canonical MacroStoryBeat truth.
- DurationBudget owns runtime allocation/tolerance only and cannot rewrite narrative facts.
- exact-version ActiveProductionProfile / StoryCore / planning-source provenance.
- profile-driven ranges, no universal fixed-count law.
- parent-child duration allocations reconcile within configured tolerance.
- stale/non-current inputs fail closed.
- revisions use immutable successors + CAS/current-pointer discipline.
- dependency edges/invalidation reuse shared VersionRepository / DependencyGraphRepository / InvalidationRepository.
- no provider/network side effects in canonical persistence transaction.
- frozen Master unchanged.

NEXT_EXACT_ACTION = "READ FULL IMP-024 FROZEN AUTHORITY + AUDIT CURRENT STRUCTURE/PLANNING CODE SURFACE"


---

## IMP-024 Targeted Test Checkpoint - 2026-09-30

STATUS = TARGETED TEST PASS
BRANCH = chatgpt/IMP-024-structure-profile-budget
HEAD = 066ce0f2f0c53943fab2e5147ba8d05f48a02cde
TARGETED_RESULT = 10 passed in 1.88s
TARGETED_EXIT_CODE = 0

Verified:
- StructureProfile range policy and exact ActiveProductionProfile lineage.
- no false-precision target field in CountRange.
- DurationBudget parent/child tolerance fail-closed.
- profile-driven macro allocation count range.
- MacroBeatSheet is ordered reference/budget projection only.
- MacroBeatSheet cannot carry MacroStoryBeat dramatic truth fields.
- FROZEN_FOR_STRUCTURE StoryCore gate.
- StructureProfile revision invalidates planning descendants.
- stale StructureProfile/current predecessor fail closed.
- macro allocation coverage gate.

NEXT_EXACT_ACTION = "RUN IMP-024 AFFECTED REGRESSION"


---

## IMP-024 LOCAL VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-024 STRUCTUREPROFILE / MACROBEATSHEET / DURATIONBUDGET
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-024-structure-profile-budget
BASE_HEAD = 066ce0f2f0c53943fab2e5147ba8d05f48a02cde

Evidence:
- evidence/tests/IMP-024_STRUCTURE_PLANNING_EVIDENCE.md
- targeted IMP-024 = 12/12 PASS
- affected regression = 67/67 PASS
- largest valid Windows regression = 540 PASS / 3 known POSIX-path cases deselected
- local video-reviewer integration excluded because ffmpeg is absent on FileMCP Windows PATH
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- exact-head self-review repaired format/niche/runtime shadow-authority gap before commit
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-024 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-024 PR #32 Exact-Head Review Repair - 2026-09-30

PR = #32
PRE_REPAIR_HEAD = 9da1b2cf344b85d20d4c7abdf4544a8e8b843199
PRE_REPAIR_CI_RUN = 36683179936
PRE_REPAIR_CI = Python 3.10 SUCCESS / Python 3.13 SUCCESS
REVIEW_RESULT = REPAIR REQUIRED

Review repairs:
- delimiter-aware same-project logical-ID boundary;
- exact-current ProjectBootstrapInput / DomainResolution gates;
- exact DomainResolution -> TopicResolution lineage pinned by ActiveProductionProfile;
- zero-count cannot bypass StructureProfile minimum ranges;
- deterministic full planning hierarchy fixture through Shot.

POST_REPAIR_LOCAL:
- targeted IMP-024 = 16/16 PASS
- affected regression = 71/71 PASS
- largest valid Windows regression = 544 PASS / 3 known POSIX-path cases deselected
- frozen Master guard = PASS
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

STATUS = REPAIR LOCAL VERIFIED / COMMIT+PUSH PENDING
NEXT_EXACT_ACTION = "COMMIT IMP-024 REVIEW REPAIR -> PUSH PR #32 -> NEW CI -> FINAL REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-024 MAIN VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-024 STRUCTUREPROFILE / MACROBEATSHEET / DURATIONBUDGET
FINAL_STATUS = MAIN VERIFIED

Feature branch:
- chatgpt/IMP-024-structure-profile-budget
- initial feature commit = 9da1b2cf344b85d20d4c7abdf4544a8e8b843199
- exact-head repair commit = b610f2a2231b2d214932fc652df8d8329f328060

Pull request:
- PR #32 = MERGED
- final exact head = b610f2a2231b2d214932fc652df8d8329f328060
- PR CI run 36685639854 = SUCCESS
- Python 3.10 / 3.13 = SUCCESS
- merge commit / verified feature-main SHA = 1f2d13385c80738177263f84c94c66d220f45be9

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-024 = 16/16 PASS
- affected regression = 71/71 PASS
- worktree = only pre-existing untracked _incoming/

Main push verification:
- workflow run 36685898846 = SUCCESS
- exact head = 1f2d13385c80738177263f84c94c66d220f45be9
- Python 3.10 / 3.13 full unit CI = SUCCESS
- frozen Master baseline = SUCCESS

DONE CRITERIA:
- immutable StructureProfile range policy = SATISFIED
- no universal fixed-count law = SATISFIED
- exact ActiveProductionProfile / Project / Domain lineage = SATISFIED
- DurationBudget hierarchy + tolerance = SATISFIED
- profile minimum ranges fail closed on zero/missing levels = SATISFIED
- MacroBeatSheet remains projection only = SATISFIED
- no MacroStoryBeat narrative duplication = SATISFIED
- exact-current/stale predecessor fail-closed = SATISFIED
- dependency invalidation = SATISFIED
- frozen Master unchanged = SATISFIED

GOVERNANCE_SYNC_BRANCH = chatgpt/IMP-024-main-verified-state
NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-024 GOVERNANCE SYNC -> CLAIM IMP-025"


---

## IMP-025 CLAIM / RESUME - 2026-09-30

ACTIVE_TASK = IMP-025 MACROSTORYBEAT / SEQUENCEPLAN / SEQUENCE / SCENEBUDGET / SCENE / SCENEBREAKDOWN / SCENEDRAMATICBEAT
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-025-narrative-hierarchy
BASE_HEAD = c546378694d97a3b88f8f65bb212548f1040f8fe
DEPENDS = IMP-024 MAIN VERIFIED + IMP-005 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE = only pre-existing untracked _incoming/ outside task scope

Acceptance:
- canonical hierarchy remains StoryCore -> MacroStoryBeat -> Sequence -> Scene -> SceneDramaticBeat.
- no generic persistent Beat authority.
- projection manifests never duplicate narrative truth.
- MacroStoryBeat / Sequence / Scene / SceneDramaticBeat each own exactly one canonical ID/version boundary.
- Scene requires meaningful state change; SceneDramaticBeat requires dramatic microchange.
- exact-version parent/source provenance and bidirectional ancestry support.
- structure/budget planning from IMP-024 constrains expansion but cannot rewrite narrative truth.
- immutable successors + CAS/current-pointer discipline.
- dependency edges/invalidation reuse shared VersionRepository / DependencyGraphRepository / InvalidationRepository.
- provider-neutral contracts; no camera/lens/light/provider payload authority.
- frozen Master unchanged.

NEXT_EXACT_ACTION = "READ FULL IMP-025 FROZEN AUTHORITY + AUDIT CURRENT NARRATIVE HIERARCHY / PLANNING SURFACES"


---

## IMP-025 Targeted Test Checkpoint - 2026-09-30

STATUS = TARGETED TEST PASS
BRANCH = chatgpt/IMP-025-narrative-hierarchy
BASE_HEAD = c546378694d97a3b88f8f65bb212548f1040f8fe
TARGETED_RESULT = 11 passed in 6.39s
TARGETED_EXIT_CODE = 0

Verified:
- no generic persistent Beat canonical entity.
- canonical Scene is distinct from legacy FlowKit operational Scene.
- MacroStoryBeat -> Sequence -> Scene -> SceneDramaticBeat exact-version persistence.
- bidirectional exact-version ancestry via shared DependencyGraphRepository.
- Scene state-change / explicit no-change-purpose gate.
- SceneDramaticBeat resistance-or-reveal + microchange gate.
- SceneListManifest / SceneBreakdownManifest / SceneBudget cannot store canonical narrative shadow truth.
- stale MacroStoryBeat parent fails closed after successor.
- historical non-current revision predecessor fails closed.
- MacroStoryBeat revision emits dependency-reachable invalidation.
- manifest-only successor does not change canonical Scene identity.
- project-prefix collisions are rejected.
- provenance must exactly bind declared source versions.

NEXT_EXACT_ACTION = "RUN IMP-025 AFFECTED REGRESSION"


---

## IMP-025 LOCAL VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-025 MACROSTORYBEAT / SEQUENCEPLAN / SEQUENCE / SCENEBUDGET / SCENE / SCENEBREAKDOWN / SCENEDRAMATICBEAT
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-025-narrative-hierarchy
BASE_HEAD = c546378694d97a3b88f8f65bb212548f1040f8fe

Evidence:
- evidence/tests/IMP-025_NARRATIVE_HIERARCHY_EVIDENCE.md
- targeted IMP-025 = 11/11 PASS
- affected regression = 95/95 PASS
- largest valid Windows regression = 555 PASS / 3 known POSIX-path cases deselected
- first broader invocation classified INTERRUPTED after process check; only broader stage rerun
- local video-reviewer integration excluded because ffmpeg is absent on FileMCP Windows PATH
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- exact-head self-review = PASS
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

Acceptance:
- StoryCore -> MacroStoryBeat -> Sequence -> Scene -> SceneDramaticBeat canonical hierarchy = SATISFIED
- no generic persistent Beat = SATISFIED
- manifests/projections do not duplicate canonical narrative truth = SATISFIED
- canonical Scene distinct from legacy FlowKit Scene = SATISFIED
- state-change / microchange gates = SATISFIED
- exact-version bidirectional ancestry = SATISFIED
- immutable successor + CAS/current predecessor gates = SATISFIED
- dependency invalidation = SATISFIED
- provider-neutral canonical contracts = SATISFIED
- frozen Master unchanged = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-025 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-025 MAIN VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-025 MACROSTORYBEAT / SEQUENCEPLAN / SEQUENCE / SCENEBUDGET / SCENE / SCENEBREAKDOWN / SCENEDRAMATICBEAT
FINAL_STATUS = MAIN VERIFIED

Feature branch:
- chatgpt/IMP-025-narrative-hierarchy
- feature commit = 0582bf9d075008ee54fb7a78c1689eb115447e02

Pull request:
- PR #34 = MERGED
- final exact head = 0582bf9d075008ee54fb7a78c1689eb115447e02
- PR CI run 36695592106 = SUCCESS
- Python 3.10 / 3.13 = SUCCESS
- merge commit / verified feature-main SHA = ce2108a72c2e198ef7a73ef8317195b5f1950b32

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-025 = 11/11 PASS
- affected regression = 95/95 PASS
- worktree = only pre-existing untracked _incoming/

Main push verification:
- workflow run 36695853857 = SUCCESS
- exact head = ce2108a72c2e198ef7a73ef8317195b5f1950b32
- Python 3.10 / 3.13 full unit CI = SUCCESS
- frozen Master baseline = SUCCESS

DONE CRITERIA:
- canonical hierarchy StoryCore -> MacroStoryBeat -> Sequence -> Scene -> SceneDramaticBeat = SATISFIED
- no generic persistent Beat = SATISFIED
- no manifest shadow truth = SATISFIED
- canonical Scene distinct from legacy FlowKit Scene = SATISFIED
- Scene state-change gate = SATISFIED
- SceneDramaticBeat microchange/resistance-or-reveal gate = SATISFIED
- bidirectional exact-version ancestry = SATISFIED
- immutable successor + exact-current CAS gates = SATISFIED
- dependency invalidation = SATISFIED
- provider-neutral canonical contracts = SATISFIED
- frozen Master unchanged = SATISFIED

GOVERNANCE_SYNC_BRANCH = chatgpt/IMP-025-main-verified-state
NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-025 GOVERNANCE SYNC -> CLAIM IMP-026"


---

## IMP-026 CLAIM / RESUME - 2026-09-30

ACTIVE_TASK = IMP-026 DIALOGUE / SETUP-PAYOFF / SCREENPLAY REALIZATION
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-026-screenplay-realization
BASE_HEAD = 0672edaac2c8a8ec8bd39e0dd6fffa9cde1f6c5d
DEPENDS = IMP-025 MAIN VERIFIED + IMP-022 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE = only pre-existing untracked _incoming/ outside task scope

Acceptance:
- screenplay is realization over canonical narrative structure, never a competing Story/Scene truth store.
- DialogueIntent is grounded in exact CharacterKnowledgeState / relationship / SceneDramaticBeat context and cannot leak unknown facts.
- SetupPayoffLink binds exact canonical setup/payoff refs and must fail closed on orphan/missing payoff lineage.
- ScreenplayScene / Screenplay are versioned realizations that reference canonical Scene / SceneDramaticBeat hierarchy exactly.
- realization edits cannot silently mutate locked upstream narrative truth.
- immutable successors + exact-current/CAS discipline.
- dependency edges/invalidation reuse shared VersionRepository / DependencyGraphRepository / InvalidationRepository.
- provider-neutral contracts; no render/provider/camera authority leakage.
- frozen Master unchanged.

NEXT_EXACT_ACTION = "READ FULL IMP-026 FROZEN AUTHORITY + AUDIT CURRENT DIALOGUE/SCREENPLAY SURFACES"


---

## IMP-026 Targeted Test Checkpoint - 2026-09-30

STATUS = TARGETED TEST PASS
BRANCH = chatgpt/IMP-026-screenplay-realization
BASE_HEAD = 0672edaac2c8a8ec8bd39e0dd6fffa9cde1f6c5d
TARGETED_RESULT = 11 passed in 3.48s
TARGETED_EXIT_CODE = 0

Verified:
- DialogueIntent rejects UNKNOWN character knowledge disclosure.
- known/believed epistemic state remains upstream-owned; realization cannot invent unknown claims.
- PAID SetupPayoffLink requires exact StoryGraph SETUP/PAYOFF nodes plus PAYS_OFF trace.
- BROKEN setup/payoff findings cannot enter accepted screenplay realization.
- ScreenplayScene must realize exact SceneBreakdownManifest beat coverage/order.
- ScreenplayDialogueLine cannot realize claims outside declared DialogueIntent disclosure.
- FullScreenplay directly binds canonical Scene + ScreenplayScene realization and rejects mismatch.
- bidirectional exact-version ancestry uses shared dependency graph.
- DialogueIntent revision invalidates dependent ScreenplayScene and FullScreenplay.
- historical non-current revision predecessor fails closed.
- project-prefix collisions fail closed.
- provenance must exactly match declared source versions.

NEXT_EXACT_ACTION = "RUN IMP-026 AFFECTED REGRESSION"


---

## IMP-026 LOCAL VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-026 DIALOGUE / SETUP-PAYOFF / SCREENPLAY REALIZATION
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-026-screenplay-realization
BASE_HEAD = 0672edaac2c8a8ec8bd39e0dd6fffa9cde1f6c5d

Evidence:
- evidence/tests/IMP-026_SCREENPLAY_REALIZATION_EVIDENCE.md
- targeted final = 13/13 PASS
- affected regression final = 114/114 PASS
- largest valid Windows regression = 567 PASS / 3 known POSIX-path cases deselected
- one broader invocation classified INTERRUPTED after process check; only broader stage rerun
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- exact-head self-review = PASS
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

Acceptance:
- screenplay is realization over canonical hierarchy, not a competing story master = SATISFIED
- DialogueIntent exact knowledge/character/relationship discipline = SATISFIED
- UNKNOWN knowledge leakage rejected = SATISFIED
- SetupPayoffLink exact StoryGraph SETUP/PAYOFF + PAYS_OFF trace = SATISFIED
- BROKEN setup/payoff blocked from accepted screenplay realization = SATISFIED
- ScreenplayScene exact SceneBreakdownManifest coverage/order = SATISFIED
- FullScreenplay direct canonical Scene + realization refs = SATISFIED
- immutable successor + exact-current/CAS gates = SATISFIED
- dependency invalidation / ancestry reuse shared repositories = SATISFIED
- provider-neutral authority = SATISFIED
- frozen Master unchanged = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-026 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-026 MAIN VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-026 DIALOGUE / SETUP-PAYOFF / SCREENPLAY REALIZATION
FINAL_STATUS = MAIN VERIFIED

Feature branch:
- chatgpt/IMP-026-screenplay-realization
- feature commit = 01443f365114584b4a62a677b2b904695efb7f98

Pull request:
- PR #36 = MERGED
- final exact head = 01443f365114584b4a62a677b2b904695efb7f98
- PR CI run 36702830926 = SUCCESS
- Python 3.10 / 3.13 = SUCCESS
- merge commit / verified feature-main SHA = 5e8b20b6a2770488cfbe0f8e0b6cf9c8b6173155

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-026 = 12/12 PASS
- affected regression = 114/114 PASS
- worktree = only pre-existing untracked _incoming/

Main push verification:
- workflow run 36703362942 = SUCCESS
- exact head = 5e8b20b6a2770488cfbe0f8e0b6cf9c8b6173155
- Python 3.10 / 3.13 full unit CI = SUCCESS
- frozen Master baseline = SUCCESS

DONE CRITERIA:
- screenplay realization does not create competing story/scene truth = SATISFIED
- DialogueIntent exact epistemic discipline = SATISFIED
- UNKNOWN knowledge leakage rejected = SATISFIED
- SetupPayoffLink causal trace and broken-link blocking = SATISFIED
- ScreenplayScene exact beat realization = SATISFIED
- FullScreenplay exact Scene + realization binding = SATISFIED
- immutable successor + exact-current CAS gates = SATISFIED
- dependency invalidation + ancestry = SATISFIED
- provider-neutral canonical contracts = SATISFIED
- frozen Master unchanged = SATISFIED

GOVERNANCE_SYNC_BRANCH = chatgpt/IMP-026-main-verified-state
NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-026 GOVERNANCE SYNC -> CLAIM IMP-027"


---

## IMP-027 CLAIM / RESUME - 2026-09-30

ACTIVE_TASK = IMP-027 STORY CRITIQUE / ROOT CAUSE / STORY REPAIR / QUALITY GATE / SCRIPTLOCK
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-027-story-quality-lock
BASE_HEAD = fd1ef88f42e53ce34e356821eea44ec7fe64b27f
DEPENDS = IMP-026 MAIN VERIFIED + IMP-006 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE = only pre-existing untracked _incoming/ outside task scope

Acceptance:
- independent critique roles remain evidence producers, not hidden story authority.
- blocking findings cannot be averaged away by aggregate quality scoring.
- root cause points to earliest responsible exact-version source, not only visible downstream symptom.
- StoryRepairPlan preserves accepted preserve-set truth and scopes changed targets explicitly.
- StoryQualityResult aggregates deterministic gates without overriding hard blockers.
- ScriptLockManifest requires all blocking findings resolved and exact accepted upstream versions.
- lock cannot silently rewrite StoryCore / narrative hierarchy / screenplay realization.
- immutable successors + exact-current/CAS discipline.
- dependency edges/invalidation reuse shared VersionRepository / DependencyGraphRepository / InvalidationRepository.
- provider-neutral contracts; frozen Master unchanged.

NEXT_EXACT_ACTION = "READ FULL IMP-027 FROZEN AUTHORITY + AUDIT CURRENT CRITIQUE/REPAIR/QUALITY/LOCK SURFACES"


---

## IMP-027 Targeted Test Checkpoint - 2026-09-30

STATUS = TARGETED TEST PASS
BRANCH = chatgpt/IMP-027-story-quality-lock
BASE_HEAD = fd1ef88f42e53ce34e356821eea44ec7fe64b27f
TARGETED_RESULT = 12 passed in 5.17s
TARGETED_EXIT_CODE = 0

Verified:
- independent critic role cannot equal generator role.
- subjective disagreement cannot auto-escalate to BLOCKER.
- hard-gate critique kinds remain BLOCKER severity.
- aggregate score cannot override unresolved BLOCKER finding.
- root cause must be visible source or exact dependency ancestor.
- repair plan cannot drop diagnosed preserve set.
- hard-gate FAIL forces StoryQualityResult FAIL.
- ScriptLock requires StoryQualityResult PASS.
- resolved blocker can PASS quality and create exact immutable lock.
- quality revision invalidates dependent ScriptLock.
- historical non-current revision predecessor fails closed.
- project-prefix collision / provenance mismatch / human-approval preconditions fail closed.
- dependency reachability comparison uses exact graph node keys, not direct VersionRef equality.

NEXT_EXACT_ACTION = "RUN IMP-027 AFFECTED REGRESSION"


---

## IMP-027 LOCAL VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-027 STORY CRITIQUE / ROOT CAUSE / STORY REPAIR / QUALITY GATE / SCRIPTLOCK
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-027-story-quality-lock
BASE_HEAD = fd1ef88f42e53ce34e356821eea44ec7fe64b27f

Evidence:
- evidence/tests/IMP-027_STORY_QUALITY_EVIDENCE.md
- targeted final = 13/13 PASS
- affected regression final = 127/127 PASS
- largest valid Windows regression = 580 PASS / 3 known POSIX-path cases deselected
- one broader invocation classified INTERRUPTED after process check; only broader stage rerun
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- exact-head self-review = PASS
- git diff --check = PASS
- _incoming/ remains untracked and outside scope

Acceptance:
- independent critique evidence, not hidden story authority = SATISFIED
- subjective disagreement cannot auto-BLOCKER = SATISFIED
- hard blockers cannot be averaged away = SATISFIED
- root cause exact-source / exact-ancestor discipline = SATISFIED
- responsible artifact same-project authority = SATISFIED
- repair preserve-set discipline = SATISFIED
- hard-gate FAIL dominance = SATISFIED
- ScriptLock requires PASS quality + exact accepted refs = SATISFIED
- immutable successor + exact-current/CAS gates = SATISFIED
- dependency invalidation / ancestry reuse shared repositories = SATISFIED
- provider-neutral authority = SATISFIED
- frozen Master unchanged = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-027 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-027 MAIN VERIFIED - 2026-09-30

ACTIVE_TASK = IMP-027 STORY CRITIQUE / ROOT CAUSE / STORY REPAIR / QUALITY GATE / SCRIPTLOCK
FINAL_STATUS = MAIN VERIFIED

Feature branch:
- chatgpt/IMP-027-story-quality-lock
- feature commit = fb607fdaa6ede42e03be3ff4c8bc188542cf2497

Pull request:
- PR #38 = MERGED
- final exact head = fb607fdaa6ede42e03be3ff4c8bc188542cf2497
- PR CI run 36708712848 = SUCCESS
- Python 3.10 / 3.13 = SUCCESS
- merge commit / verified feature-main SHA = 8399fe76a4c7e7dc08010b6f442ef64a0d09bb4c

Local final main verification:
- frozen Master guard = PASS
- targeted IMP-027 = 13/13 PASS
- affected regression = 127/127 PASS
- worktree = only pre-existing untracked _incoming/

Main push verification:
- workflow run 36708995131 = SUCCESS
- exact head = 8399fe76a4c7e7dc08010b6f442ef64a0d09bb4c
- Python 3.10 / 3.13 full unit CI = SUCCESS
- frozen Master baseline = SUCCESS

DONE CRITERIA:
- independent critique evidence, not hidden story authority = SATISFIED
- hard blockers cannot be averaged away = SATISFIED
- exact root-cause ancestry = SATISFIED
- responsible artifact same-project authority = SATISFIED
- exact preserve-set repair discipline = SATISFIED
- hard-gate FAIL dominance = SATISFIED
- ScriptLock exact lineage + PASS quality = SATISFIED
- immutable successor + exact-current/CAS gates = SATISFIED
- dependency invalidation / ancestry = SATISFIED
- provider-neutral canonical contracts = SATISFIED
- frozen Master unchanged = SATISFIED

GOVERNANCE_SYNC_BRANCH = chatgpt/IMP-027-main-verified-state
NEXT_EXACT_ACTION = "COMMIT/PUSH/MERGE IMP-027 GOVERNANCE SYNC -> CLAIM IMP-028"


---

## IMP-028 Resume / Claim - 2026-10-03

SOURCE_OF_TRUTH_RECONCILIATION:
- restored repo root = `E:\FlowKit-Studio-Upgrade`
- verified `main` = `229ccfb227e748f594fb1f9e8d53040095910c9e`
- PR #39 governance sync is already MERGED at that exact SHA
- no active IMP-028 process and no pre-existing remote IMP-028 branch

ACTIVE_TASK = IMP-028 NARRATIVETRACE
STATUS = CLAIMED / AUTHORITY READ + CURRENT CODE AUDIT
BRANCH = chatgpt/IMP-028-narrative-trace
BASE_HEAD = 229ccfb227e748f594fb1f9e8d53040095910c9e
DEPENDS = IMP-025 MAIN VERIFIED + IMP-027 MAIN VERIFIED + IMP-005 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "AUDIT SHARED VERSION/DEPENDENCY/NARRATIVE HIERARCHY SURFACES -> IMPLEMENT IMP-028 NARRATIVETRACE + TARGETED TESTS"


---

## IMP-028 Local Verification - 2026-10-03

IMP-028 = LOCAL VERIFIED
BRANCH = chatgpt/IMP-028-narrative-trace
BASE = 229ccfb227e748f594fb1f9e8d53040095910c9e

Evidence:
- `evidence/tests/IMP-028_NARRATIVE_TRACE_EVIDENCE.md`
- targeted IMP-028 = 13/13 PASS
- affected regression = 98/98 PASS
- largest valid Windows regression = 580 PASS / 3 deselected
- full Windows broad run exposed unrelated `tests/unit/test_setup.py` default-codepage/UTF-8 fixture failures; no out-of-scope diff
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- compileall = PASS
- git diff --check = PASS
- provider/runtime authority leakage check = PASS
- exact-head local review repair: trace exact-source dependency edges added for §63 invalidation propagation

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-028 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE -> VERIFY MAIN"

- PR #40 exact-head review hardening = transitive durable invalidation gap repaired; post-fix targeted 13/13, affected 98/98, broader 580 PASS / 3 deselected, frozen guard PASS.


STATUS = IMP-028 PR #40 REVIEW FIX LOCAL VERIFIED
REVIEW_FINDING = transitive unresolved §63 invalidation was not reflected by trace_state; repaired
POST_FIX_EVIDENCE = targeted 13/13 PASS; affected 98/98 PASS; broader 580 PASS / 3 deselected; frozen guard PASS
NEXT_EXACT_ACTION = "COMMIT/PUSH PR #40 REVIEW FIX -> RERUN UBUNTU CI -> FINAL EXACT-HEAD REVIEW -> MERGE -> VERIFY MAIN"


---

## IMP-028 MAIN VERIFIED - 2026-10-03

IMP-028 = MAIN VERIFIED
FEATURE_PR = #40
FEATURE_HEAD = f18955e68945fe7252443392768233120f129bb9
MAIN_MERGE_SHA = 32e078c7225b27eb54b3ed4536ec0d792efec98d
MAIN_PUSH_WORKFLOW = 37097099717 SUCCESS exact merge SHA
POST_MERGE_TARGETED = 13/13 PASS
POST_MERGE_AFFECTED = 98/98 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE_AT_VERIFICATION = clean
GOVERNANCE_BRANCH = chatgpt/IMP-028-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-028 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-041 Claim - 2026-10-03

SOURCE_OF_TRUTH_RECONCILIATION:
- IMP-028 feature PR #40 merged and MAIN VERIFIED.
- IMP-028 governance PR #41 merged at `80671b9a46b057285e9c1476ae266990e87be6a4`.
- governance push-main workflow `37097429052` SUCCESS exact governance SHA.
- main worktree clean before claim.

ACTIVE_TASK = IMP-041 REFERENCEASSET / REFERENCE RESOLVER
STATUS = CLAIMED / AUTHORITY READ + CURRENT CODE AUDIT
BRANCH = chatgpt/IMP-041-reference-asset-resolver
BASE_HEAD = 80671b9a46b057285e9c1476ae266990e87be6a4
DEPENDS = IMP-040 MAIN VERIFIED + IMP-005 MAIN VERIFIED + IMP-013 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "READ IMP-041 FROZEN AUTHORITY + AUDIT ENTITY/MEDIA/REFERENCE/INVALIDATION SURFACES BEFORE CODE"


---

## IMP-041 LOCAL VERIFIED - 2026-10-03

ACTIVE_TASK = IMP-041 REFERENCEASSET / REFERENCE RESOLVER
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-041-reference-asset-resolver
BASE_HEAD = 80671b9a46b057285e9c1476ae266990e87be6a4

Evidence:
- `evidence/tests/IMP-041_REFERENCE_ASSET_RESOLVER_EVIDENCE.md`
- targeted IMP-041 = 13/13 PASS
- affected regression = 46/46 PASS
- largest valid Windows regression = 593 PASS / 3 deselected
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- compileall = PASS
- git diff --check = PASS
- canonical runtime/authority leakage scan = PASS
- FM-005 successor invalidation bypass found in self-review and repaired before commit

Acceptance:
- ReferenceAsset exact identity/version/hash/role = SATISFIED
- legacy UUID/media compatibility without Entity shadow truth = SATISFIED
- resolver minimal deterministic subset = SATISFIED
- stale/unapproved Entity/Reference fail closed = SATISFIED
- exact resolution provenance + bind-time race revalidation = SATISFIED
- changed ReferenceVersion durable selective invalidation = SATISFIED
- plain successor promotion cannot bypass invalidation = SATISFIED
- reference evidence is not canonical State = SATISFIED
- provider/runtime authority remains downstream = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-041 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-041 MAIN VERIFIED - 2026-10-03

IMP-041 = MAIN VERIFIED
FEATURE_PR = #42
FEATURE_HEAD = e1425ee94147a93fbfc198c9617e7f66f26e154f
MAIN_MERGE_SHA = dd5cf60fffdbcb18035271d0441fbc100538aa6a
PR_CI_RUN = 37105500213 SUCCESS Python 3.10 / 3.13 exact feature head
MAIN_PUSH_WORKFLOW = 37105602945 SUCCESS exact merge SHA
POST_MERGE_TARGETED = 13/13 PASS
POST_MERGE_AFFECTED = 46/46 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE_AT_VERIFICATION = clean
GOVERNANCE_BRANCH = chatgpt/IMP-041-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-041 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-042 Claim - 2026-10-03

SOURCE_OF_TRUTH_RECONCILIATION:
- IMP-041 feature PR #42 merged and MAIN VERIFIED at `dd5cf60fffdbcb18035271d0441fbc100538aa6a`.
- IMP-041 governance PR #43 merged at `55ba8d747db11c52417d6d9dfe1b67a807de604e`.
- governance push-main workflow `37105880072` SUCCESS exact governance SHA.
- main worktree clean before claim.

ACTIVE_TASK = IMP-042 STATESNAPSHOT / CONTINUITYLEDGER / APPROVEDENDSTATE
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-042-state-continuity
BASE_HEAD = 55ba8d747db11c52417d6d9dfe1b67a807de604e
DEPENDS = IMP-041 MAIN VERIFIED + IMP-004 MAIN VERIFIED + IMP-005 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "READ IMP-042 FROZEN STATE/CONTINUITY/APPROVED-END-STATE AUTHORITY + AUDIT MEDIA-CHAIN/ENTITY/INVALIDATION SURFACES BEFORE CODE"


---

## IMP-042 AUTHORITY + SURFACE AUDIT PASS - 2026-10-03

ACTIVE_TASK = IMP-042 STATESNAPSHOT / CONTINUITYLEDGER / APPROVEDENDSTATE
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-042-state-continuity
BASE_HEAD = 55ba8d747db11c52417d6d9dfe1b67a807de604e

LOCKED IMPLEMENTATION DECISIONS:
- StateSnapshot is the sole canonical semantic continuity/world-state payload owner.
- ContinuityLedger owns versioned continuity evidence/constraints/propagation links only; it MUST NOT duplicate StateSnapshot payload.
- ApprovedEndState is an approval designation/reference only; it MUST NOT duplicate StateSnapshot payload.
- only APPROVED/LOCKED StateSnapshot versions may propagate downstream.
- approval requires exact QA/approval evidence refs; provider success alone cannot authorize state propagation.
- Story-owned psychology/relationship/knowledge payloads remain owned by character_state.py and may only be exact-version source refs here.
- legacy parent_scene_id / image_media_id / end_scene_media_id remain execution-conditioning lineage, never canonical StateSnapshot authority.
- state/reference/continuity dependencies use shared VersionRepository + DependencyGraph + durable InvalidationRecord; no second truth store.
- accepted StateSnapshot successor change must selectively invalidate exact bound descendants before replacement becomes downstream current authority.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-042 STATE SNAPSHOT + STATE DELTA + CONTINUITY LEDGER + APPROVED-END-STATE DESIGNATION -> TARGETED TESTS"


---

## IMP-042 LOCAL VERIFIED - 2026-10-03

ACTIVE_TASK = IMP-042 STATESNAPSHOT / CONTINUITYLEDGER / APPROVEDENDSTATE
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-042-state-continuity
BASE_HEAD = 55ba8d747db11c52417d6d9dfe1b67a807de604e

Evidence:
- `evidence/tests/IMP-042_STATE_CONTINUITY_EVIDENCE.md`
- targeted final = 16/16 PASS
- affected regression final = 65/65 PASS
- largest valid Windows regression = 609 PASS / 3 known exclusions deselected
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- compileall = PASS
- git diff --check = PASS
- provider/runtime authority import scan = NONE
- TODO/FIXME/NotImplemented scan = NONE

Acceptance:
- StateSnapshot is sole semantic continuity payload authority = SATISFIED
- generated artifact/media-chain != State = SATISFIED
- Story-owned psychology/relationship/knowledge remain exact refs only = SATISFIED
- payload-free StateDelta = SATISFIED
- only exact current APPROVED/LOCKED snapshot with approved designation propagates = SATISFIED
- ApprovedEndState designation contains no duplicate state payload = SATISFIED
- stale QA/policy/outcome/source inputs fail closed = SATISFIED
- ContinuityLedger constraints/findings refs-only and fact-key validated = SATISFIED
- exact consumer provenance + durable dependency edges = SATISFIED
- StateSnapshot successor selective invalidation = SATISFIED
- replacement snapshot self-invalidation prevented = SATISFIED
- ContinuityLedger successor invalidation bypass closed = SATISFIED
- ApprovedEndState revocation history + durable invalidation = SATISFIED
- frozen Master unchanged = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-042 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-042 MAIN VERIFIED - 2026-10-03

IMP-042 = MAIN VERIFIED
FEATURE_PR = #44
FEATURE_HEAD = b0ce693b28ac9e9b00135b3a938ee73852b3f3bf
MAIN_MERGE_SHA = 22c9975f8296bb40d5e82cc3c698a2e7fc38b062
PR_CI_RUN = 37108150194 SUCCESS Python 3.10 / 3.13 exact feature head
MAIN_PUSH_WORKFLOW = 37108250205 SUCCESS exact merge SHA
POST_MERGE_TARGETED = 16/16 PASS
POST_MERGE_AFFECTED = 65/65 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE_AT_VERIFICATION = clean
GOVERNANCE_BRANCH = chatgpt/IMP-042-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-042 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-042 GOVERNANCE VERIFIED / IMP-030 CLAIM - 2026-10-03

SOURCE_OF_TRUTH_RECONCILIATION:
- IMP-042 feature PR #44 merged and MAIN VERIFIED at `22c9975f8296bb40d5e82cc3c698a2e7fc38b062`.
- IMP-042 governance PR #45 merged at `6ecc99275fe953f65fb1c7f64158e5f438d655a8`.
- governance push-main workflow `37108600449` SUCCESS exact governance SHA.
- frozen Master guard PASS at governance main; semantic SHA `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`.
- main worktree clean before claim.

ACTIVE_TASK = IMP-030 AUDIENCE / DIRECTING / SPATIAL / BLOCKING / CINEMATOGRAPHY
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-030-directing-spatial-cinematography
BASE_HEAD = 6ecc99275fe953f65fb1c7f64158e5f438d655a8
DEPENDS = IMP-025 MAIN VERIFIED + IMP-027 MAIN VERIFIED + IMP-028 MAIN VERIFIED + IMP-042 MAIN VERIFIED + IMP-013 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "READ IMP-030 FROZEN AUDIENCE/DIRECTING/SPATIAL/BLOCKING/CINEMATOGRAPHY AUTHORITY + AUDIT CURRENT NARRATIVE/STATE/CAMERA SURFACES BEFORE CODE"


---

## IMP-030 AUTHORITY + SURFACE AUDIT PASS - 2026-10-03

ACTIVE_TASK = IMP-030 AUDIENCE / DIRECTING / SPATIAL / BLOCKING / CINEMATOGRAPHY
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-030-directing-spatial-cinematography
BASE_HEAD = 6ecc99275fe953f65fb1c7f64158e5f438d655a8

LOCKED IMPLEMENTATION DECISIONS:
- AudienceExperienceTarget is beat-scoped viewer-effect authority and binds exact current SceneDramaticBeat + CURRENT NarrativeTrace; it never becomes generic cinematic style prose.
- DirectingIntent is beat-scoped performance/reveal/staging authority and requires exact LOCKED ScriptLock + AudienceExperienceTarget + SceneDramaticBeat + pinned LOCKED ActiveProductionProfile.
- SceneSpatialDramaticContract is scene-scoped spatial baseline from exact Scene + Beat set + approved/propagatable StateSnapshot; it owns geography/zones/sightlines/constraints, not camera choice.
- BlockingPlan is beat-scoped spatial execution and joins DirectingIntent + scene SpatialContract + approved StateSnapshot; blocking cannot be embedded as cinematography/prompt shadow truth.
- CinematographyObjective is beat-scoped visual-language translation and requires Audience + Directing + Spatial + Blocking + pinned profile; each visual strategy must carry exact upstream decision basis.
- Cinematography schema will expose strategies/objectives, not free-standing exact camera/lens authority; camera/lens/movement/light/composition cannot self-author.
- Story/Scene/Beat/State/Profile payloads remain in their owning repositories; IMP-030 stores exact refs/provenance only.
- ActiveProductionProfile dependencies use `PROFILE_PATH:*` graph edges so IMP-013 selective invalidation remains effective.
- accepted revisions create immutable successors and durable dependency-reachable invalidation before current-pointer advance.
- existing FlowKit prompt/camera/service fields remain downstream compatibility/runtime surfaces only; no transport/provider imports enter canonical directing authority.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-030 PROVIDER-NEUTRAL AUTHORITY CONTRACTS + REPOSITORY -> TARGETED TESTS"


---

## IMP-030 LOCAL VERIFIED - 2026-10-03

ACTIVE_TASK = IMP-030 AUDIENCE / DIRECTING / SPATIAL / BLOCKING / CINEMATOGRAPHY
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-030-directing-spatial-cinematography
BASE_HEAD = 6ecc99275fe953f65fb1c7f64158e5f438d655a8

Evidence:
- `evidence/tests/IMP-030_DIRECTING_AUTHORITY_EVIDENCE.md`
- targeted final = 18/18 PASS
- affected regression final = 117/117 PASS
- largest valid Windows regression = 627 PASS / 3 deselected
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- compileall = PASS
- git diff --check = PASS
- runtime/provider import leakage = NONE
- TODO/FIXME/NotImplemented = NONE

Review hardening:
- directing/performance entities must be declared by canonical Scene;
- spatial participants must be declared by canonical Scene;
- entity-backed spatial anchors must be authorized by Scene or approved StateSnapshot;
- location_entity_ref must be canonical LOCATION;
- Blocking entities must be declared by exact SpatialContract.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-030 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-030 MAIN VERIFIED - 2026-10-03

IMP-030 = MAIN VERIFIED
FEATURE_PR = #46
FEATURE_HEAD = e6ff93f23550d4f650ac3461410f974e56fdfcc6
MAIN_MERGE_SHA = 3dc15e029d6cfb2e3736ee443a72cbbda504c726
PR_CI_RUN = 37111493909 SUCCESS Python 3.10 / 3.13 exact feature head
MAIN_PUSH_WORKFLOW = 37111589949 SUCCESS exact merge SHA
POST_MERGE_TARGETED = 18/18 PASS
POST_MERGE_AFFECTED = 117/117 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
WORKTREE_AT_VERIFICATION = clean
GOVERNANCE_BRANCH = chatgpt/IMP-030-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-030 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-031 CLAIMED - 2026-10-03

ACTIVE_TASK = IMP-031 SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-031-shot-expansion
BASE_HEAD = 2da4d431fd52269cd79039a2f9bb6cf0bd940c91
DEPENDS = IMP-030 MAIN VERIFIED + IMP-028 MAIN VERIFIED + IMP-024 MAIN VERIFIED
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

NEXT_EXACT_ACTION = "READ IMP-031 FROZEN SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM AUTHORITY + ADR-0020 + AUDIT COVERAGE/BUDGET/DIRECTING/NARRATIVE TRACE SURFACES BEFORE CODE"


---

## IMP-031 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-03

ACTIVE_TASK = IMP-031 SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-031-shot-expansion
BASE_HEAD = 2da4d431fd52269cd79039a2f9bb6cf0bd940c91

LOCKED IMPLEMENTATION DECISIONS:
- ADR-0020 is authoritative: ShotListItem is the sole canonical shot_id origin; ShotExpansion is a stateless planning transformation; ShotListManifest is refs/projection only.
- CoverageStrategy and ShotBudget have no separate implementation task, but Frozen Master §§45-46 place them as mandatory canonical planning prerequisites to ShotExpansion and IMP-031 explicitly requires coverage/budget tests. They are implemented in the same Shot Planning boundary without owning Shot identity or narrative truth.
- ShotExpansion candidates are ephemeral and contain no shot_id. shot_id is allocated only after narrative/coverage/budget/redundancy gates pass at the ShotListItem creation boundary.
- ShotListItem immediate narrative parent is exact current SceneDramaticBeat; inherited Scene/Sequence/MacroStoryBeat/StoryCore context is proven through CURRENT NarrativeTrace rather than copied into Shot truth.
- Exact ScriptLock, DirectingIntent, BlockingPlan, CinematographyObjective, CoverageStrategy, ShotBudget, DurationBudget and LOCKED ActiveProductionProfile versions are bound in provenance/dependency edges.
- CoverageStrategy is scene-scoped provider-neutral coverage/editing planning; ShotBudget is scene-scoped count/duration range+rationale planning. Neither may invent narrative or exact provider/camera truth.
- ShotListManifest stores ordered ShotListItem refs + coverage/order metadata only; no duplicated dramatic/basic-shot payload.
- consumers fail closed on stale current pointers and durable unresolved invalidation records.
- accepted revisions persist immutable successors, register exact dependency edges, create durable selective invalidation before current-pointer CAS.
- planning writes have no provider/network side effects; partial item creation before manifest approval is recoverable because Master explicitly permits ShotListItem identities to exist before manifest approval and manifest is a separate projection lifecycle.
- legacy FlowKit Scene/render rows remain downstream compatibility/execution targets only and never allocate canonical shot_id.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-031 SHOT PLANNING CONTRACTS/REPOSITORY + STATELESS EXPANSION SERVICE -> TARGETED TESTS"


---

## IMP-031 LOCAL VERIFIED - 2026-10-03

ACTIVE_TASK = IMP-031 SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM
STATUS = LOCAL VERIFIED
BRANCH = chatgpt/IMP-031-shot-expansion
BASE_HEAD = 2da4d431fd52269cd79039a2f9bb6cf0bd940c91

Evidence:
- `evidence/tests/IMP-031_SHOT_PLANNING_EVIDENCE.md`
- targeted final = 15/15 PASS
- affected regression final = 128/128 PASS
- largest valid Windows regression = 642 PASS / 3 deselected
- frozen Master guard = PASS
- frozen semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
- compileall + git diff --check = PASS
- provider/runtime/network import leakage = NONE
- TODO/FIXME/NotImplemented = NONE

Acceptance:
- ShotExpansion stateless / no candidate shot_id = SATISFIED
- ShotListItem sole canonical shot_id origin = SATISFIED
- exact SceneDramaticBeat parent + CURRENT NarrativeTrace = SATISFIED
- ShotListItem creation/revision always maintains shot NarrativeTrace = SATISFIED
- CoverageStrategy exact current beat-set coverage = SATISFIED
- ShotBudget count/duration reconciliation = SATISFIED
- no redundant/unjustified shot = SATISFIED
- ShotListManifest refs-only / no shadow truth = SATISFIED
- no premature ELIGIBLE bypass before IMP-032 = SATISFIED
- exact-current + unresolved-invalidation fail closed = SATISFIED
- selective dependency invalidation = SATISFIED
- frozen Master unchanged = SATISFIED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-031 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-031 PR #48 REVIEW-FIX LOCAL VERIFIED - 2026-10-03

ACTIVE_TASK = IMP-031 SHOTEXPANSION / SHOTLISTMANIFEST / SHOTLISTITEM
STATUS = PR REVIEW-FIX LOCAL VERIFIED / PUSH NEW HEAD NEXT
BRANCH = chatgpt/IMP-031-shot-expansion
INITIAL_FEATURE_COMMIT = 243f97e6a207a83b3fb5a041c5744b8b37ac3d16
PR = #48

Checkpoint:
- exact-replay recovery hardens ShotListItem + NarrativeTrace crash boundary;
- ShotListItem consumption requires exact CURRENT shot NarrativeTrace;
- exact ShotListManifest replay is idempotent; conflicting replay remains forbidden;
- targeted 17/17 PASS;
- affected 130/130 PASS;
- broader valid Windows 644 PASS / 3 deselected;
- frozen Master guard PASS / semantic SHA unchanged;
- compileall + diff check + import/TODO scans PASS.

NEXT_EXACT_ACTION = "STAGE EXACT REVIEW-FIX SCOPE -> COMMIT REVIEW-FIX -> PUSH NEW HEAD TO PR #48 -> WAIT FRESH CI -> EXACT-HEAD REVIEW/MERGE GUARD -> MERGE MAIN -> VERIFY MAIN"


---

## IMP-031 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

IMP-031 = MAIN VERIFIED
FEATURE_PR = #48
FEATURE_HEAD = 62754bc9655b6732f3fad669c281381ab47ae1ed
MAIN_MERGE_SHA = c6913a2f82c85d05c128824b640f5a17bb635bbf
PR_CI_RUN = 37118314077 SUCCESS Python 3.10 / 3.13 exact feature head
POST_MERGE_TARGETED = 17/17 PASS
POST_MERGE_AFFECTED = 130/130 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
MAIN_PUSH_WORKFLOW = 37118410749 SUCCESS exact merge SHA
GOVERNANCE_BRANCH = chatgpt/IMP-031-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-031 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-031 GOVERNANCE VERIFIED / IMP-032 CLAIMED - 2026-10-03

IMP-031 governance PR #49 merged at `f7ec86c9392be24185d23893cd8b513e281f1c52`.
Governance push-main workflow `37118828928` SUCCESS exact governance SHA.

ACTIVE_TASK = IMP-032 SHOTELIGIBILITYGATE / FULLSHOTSPEC / STATICKEYFRAMESPEC / MOTIONDELTASPEC / SHOTDECISIONTRACE
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-032-shot-eligibility-fullshotspec
BASE_HEAD = f7ec86c9392be24185d23893cd8b513e281f1c52
DEPENDS = IMP-031 MAIN VERIFIED + IMP-042 MAIN VERIFIED + IMP-041 MAIN VERIFIED + IMP-013 MAIN VERIFIED

NEXT_EXACT_ACTION = "READ IMP-032 FROZEN SHOT ELIGIBILITY / FULLSHOTSPEC L1-L8 / STATICKEYFRAMESPEC / MOTIONDELTASPEC / SHOTDECISIONTRACE AUTHORITY + AUDIT CURRENT SHOT/STATE/REFERENCE/PROFILE SURFACES BEFORE CODE"


---

## IMP-032 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-03

ACTIVE_TASK = IMP-032 SHOTELIGIBILITYGATE / FULLSHOTSPEC / STATICKEYFRAMESPEC / MOTIONDELTASPEC / SHOTDECISIONTRACE
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-032-shot-eligibility-fullshotspec
BASE_HEAD = f7ec86c9392be24185d23893cd8b513e281f1c52

Locked boundaries:
- same canonical shot_id from ShotListItem only;
- immutable exact-input ShotEligibilityGate, CURRENT ELIGIBLE required for realization;
- FullShotSpec = provider-neutral detailed realization with exactly semantic L1-L8 and field authority/provenance;
- StaticKeyframeSpec = start/keyframe state only; MotionDeltaSpec = temporal delta only;
- ShotDecisionTrace = explainability evidence bound to exact FullShotSpec version;
- reuse current approved StateSnapshot/designation + exact ReferenceAsset resolution + locked ActiveProductionProfile;
- shared VersionRepository/DependencyGraph/Invalidation only; no provider/runtime authority.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-032 PROVIDER-NEUTRAL REALIZATION CONTRACTS/REPOSITORY + HARD GATES -> TARGETED TESTS"


---

## IMP-032 LOCAL VERIFIED - 2026-10-03

IMP-032 = LOCAL VERIFIED
BRANCH = chatgpt/IMP-032-shot-eligibility-fullshotspec
BASE_HEAD = f7ec86c9392be24185d23893cd8b513e281f1c52
FROZEN_MASTER_SHA = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287

Verified implementation:
- ShotEligibilityGate exact evaluated-input evidence with exact rule/profile/state/reference/directing/cinematography bindings;
- FullShotSpec exactly L1-L8 with field authority/provenance;
- StaticKeyframeSpec static-only start state;
- MotionDeltaSpec temporal-delta-only contract;
- ShotDecisionTrace exact explainability lineage;
- no new shot_id authority and no provider/runtime canonical leakage;
- selective durable invalidation for reference/rule/spec/gate successors;
- crash-safe reference-binding promotion boundary.

Verification evidence:
- targeted = 15/15 PASS;
- affected = 154/154 PASS;
- broader Windows = 659 PASS / 3 deselected;
- frozen guard = PASS;
- semantic SHA unchanged = 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287;
- compileall / diff check / leakage scan / TODO scan = PASS;
- evidence = `evidence/tests/IMP-032_SHOT_REALIZATION_EVIDENCE.md`.

REMOTE STATUS = NOT YET COMMITTED/PUSHED/PR/MERGED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-032 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC -> MAIN VERIFIED -> CLAIM NEXT TASK"


### IMP-032 SIDE-EFFECT GUARD PASS - 2026-10-03

- remote feature branch absent before push;
- no existing PR for `chatgpt/IMP-032-shot-eligibility-fullshotspec`;
- staged index was empty before exact-scope staging;
- transient `.tmp` removed and excluded from scope.

NEXT_EXACT_ACTION = "STAGE EXACT IMP-032 VERIFIED SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


### IMP-032 FEATURE COMMIT / PR CREATED - 2026-10-03

FEATURE_COMMIT = `6e96978bc9596bc4838492532dacabc7c56f1a53`
REMOTE_BRANCH = `origin/chatgpt/IMP-032-shot-eligibility-fullshotspec`
PUSH = SUCCESS
PR = #50
PR_URL = https://github.com/nguyenkhactang922-bot/flowkit/pull/50

Implementation/test content remains exactly the LOCAL VERIFIED head; this state checkpoint is docs-only.

NEXT_EXACT_ACTION = "COMMIT/PUSH IMP-032 PR CHECKPOINT STATE -> WAIT FRESH CI ON FINAL HEAD -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-032 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-03

IMP-032 feature implementation = MAIN VERIFIED
FEATURE_PR = #50
IMPLEMENTATION_COMMIT = `6e96978bc9596bc4838492532dacabc7c56f1a53`
FINAL_PR_HEAD = `78464d03f5dc2a537ddbcce470a59cce71404a1f`
PR_CI_RUN = `37138187600` SUCCESS Python 3.10 / 3.13
MAIN_MERGE_SHA = `bd9ac71117912e5f1f4771eaf2cf128dcb5739a8`
POST_MERGE_TARGETED = 15/15 PASS
POST_MERGE_AFFECTED = 154/154 PASS
FROZEN_MASTER_GUARD = PASS / semantic SHA unchanged
MAIN_PUSH_WORKFLOW = `37138380626` SUCCESS Python 3.10 / 3.13 exact merge SHA
GOVERNANCE_BRANCH = `chatgpt/IMP-032-main-verified-state`

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-032 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-032 GOVERNANCE VERIFIED / IMP-033 CLAIMED - 2026-10-03

IMP-032 governance PR #51 merged at `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`.
Governance push-main workflow `37138826694` SUCCESS Python 3.10 / 3.13 exact governance SHA.
IMP-032 = MAIN VERIFIED.

ACTIVE_TASK = IMP-033 SHOTIR / PRODUCTION COMPILER
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = `chatgpt/IMP-033-shotir-production-compiler`
BASE_HEAD = `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`
DEPENDS = IMP-032 MAIN VERIFIED

NEXT_EXACT_ACTION = "READ IMP-033 FROZEN SHOTIR / PRODUCTION COMPILER AUTHORITY + AUDIT CURRENT SHOT REALIZATION / REQUEST / COMPILER / PROVIDER-BOUNDARY SURFACES BEFORE CODE"


---

## IMP-033 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

ACTIVE_TASK = IMP-033 SHOTIR / PRODUCTION COMPILER
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = `chatgpt/IMP-033-shotir-production-compiler`
BASE_HEAD = `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`

Checkpoint:
- Frozen Master §55 Shot IR + §64 Production Compiler read and reconciled with ADR-0020.
- Task acceptance confirmed: deterministic golden compile, exact input-version bindings, stable hashes/metadata, no provider-specific authority in IR, stale-source rejection.
- No canonical ShotIR/CompiledRequest owner exists in `agent/studio` yet.
- IMP-032 FullShotSpec/StaticKeyframeSpec/MotionDeltaSpec + State/Reference/Profile exact-current authorities are the upstream compile inputs.
- Legacy Flow/Omni prompt/request builders are provider/compatibility surfaces only and remain untouched by IMP-033.
- ProviderProfile/router/capability lowering remains IMP-050; adapter anti-corruption remains IMP-051.
- Frozen Master guard PASS / semantic SHA unchanged.

NEXT_EXACT_ACTION = "IMPLEMENT IMP-033 PROVIDER-NEUTRAL SHOTIR + DETERMINISTIC PRODUCTION COMPILER + PROVENANCE/HASHES -> TARGETED TESTS"


---

## IMP-033 LOCAL VERIFIED - 2026-10-04

IMP-033 = LOCAL VERIFIED
BRANCH = `chatgpt/IMP-033-shotir-production-compiler`
BASE_HEAD = `2f47dc6354e6c5e7a1a0bce7afe9b8e176a6c332`

Verified implementation:
- canonical provider-neutral ShotIR with same existing shot_id;
- deterministic Production Compiler with exact source-version/provenance bindings;
- exact current FullShotSpec / eligibility / StaticKeyframeSpec / MotionDeltaSpec / approved State / locked profile / ReferenceAsset / CompilerRuleSet validation;
- stable input/semantic/static/motion fingerprints;
- provider/runtime request authority excluded from canonical IR;
- immutable successor + durable downstream invalidation + replay-safe promotion.

Verification evidence:
- targeted = 14/14 PASS;
- affected = 169/169 PASS;
- broader Windows = 673 PASS / 3 deselected;
- frozen guard = PASS;
- semantic SHA unchanged = `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`;
- compileall / diff check / leakage scan / TODO scan = PASS;
- evidence = `evidence/tests/IMP-033_SHOTIR_PRODUCTION_COMPILER_EVIDENCE.md`.

REMOTE STATUS = NOT YET COMMITTED/PUSHED/PR/MERGED

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-033 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


### IMP-033 FEATURE COMMIT / PR CREATED - 2026-10-04

FEATURE_COMMIT = `ee0bd4bc04cf8879746a278538540f996d6cd4d5`
REMOTE_BRANCH = `origin/chatgpt/IMP-033-shotir-production-compiler`
PR = #52
PR_URL = https://github.com/nguyenkhactang922-bot/flowkit/pull/52
INITIAL_PR_CI_RUN = 37175035654 / Python 3.10 + 3.13 IN_PROGRESS at checkpoint time

NEXT_EXACT_ACTION = "COMMIT/PUSH IMP-033 PR CHECKPOINT STATE -> WAIT FRESH CI ON FINAL PR HEAD -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-033 FEATURE MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

IMP-033 feature implementation = MAIN VERIFIED
FEATURE_PR = #52
IMPLEMENTATION_COMMIT = `ee0bd4bc04cf8879746a278538540f996d6cd4d5`
FINAL_PR_HEAD = `b1df7a296ac972a5ab92adb5a88cbf7c50623938`
PR_CI_RUN = `37175107218` SUCCESS Python 3.10 / 3.13
MAIN_MERGE_SHA = `a914234410edbc2c6bc651a6177806af10a45c48`
POST_MERGE_TARGETED = 14/14 PASS
POST_MERGE_AFFECTED = 169/169 PASS
FROZEN_MASTER_GUARD = PASS / semantic SHA unchanged
MAIN_PUSH_WORKFLOW = `37175266699` SUCCESS exact merge SHA
GOVERNANCE_BRANCH = `chatgpt/IMP-033-main-verified-state`

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-033 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-033 GOVERNANCE VERIFIED / IMP-050 CLAIMED - 2026-10-04

IMP-033 governance PR #53 merged at `9c6c8a68df6eba566e86aea680d6a892a815eb26`.
Governance push-main workflow `37175814754` SUCCESS exact governance SHA.
Frozen Master guard PASS / semantic SHA unchanged.

ACTIVE_TASK = IMP-050 CAPABILITYREGISTRY / PROVIDERPROFILE / ROUTER
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = `chatgpt/IMP-050-capability-provider-router`
BASE_HEAD = `9c6c8a68df6eba566e86aea680d6a892a815eb26`
DEPENDS = IMP-033 MAIN VERIFIED + IMP-013 MAIN VERIFIED + IMP-006 MAIN VERIFIED
REMOTE_DUPLICATE_GUARD = PASS

NEXT_EXACT_ACTION = "READ FROZEN CAPABILITYREGISTRY / PROVIDERPROFILE / ROUTER AUTHORITY + AUDIT CURRENT FLOW/OMNI/CAPABILITY/ROUTING SURFACES BEFORE CODE"


---

## IMP-050 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

ACTIVE_TASK = IMP-050 CAPABILITYREGISTRY / PROVIDERPROFILE / ROUTER
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE IN PROGRESS
BRANCH = `chatgpt/IMP-050-capability-provider-router`
BASE_HEAD = `9c6c8a68df6eba566e86aea680d6a892a815eb26`

Locked boundaries:
- evidence-versioned ProviderProfile only; UNKNOWN facts are never guessed;
- deterministic side-effect-free Router over exact current ShotIR/Profile/ActiveProductionProfile/rule inputs;
- explicit degradation policy only; no hidden fallback;
- shared version/dependency/invalidation/evidence owners only;
- Flow/Omni operational capability constants stay legacy adapter donors for IMP-051, not canonical authority;
- candidate current-pointer/invalidation and ShotIR constraint-preservation gates are mandatory before ranking.

CODE = `agent/studio/provider_routing.py` materialized / py_compile PASS.

NEXT_EXACT_ACTION = "EXPORT IMP-050 API -> WRITE REAL SQLITE/SHOTIR TARGETED TESTS -> RUN TARGETED"


---

## IMP-050 LOCAL VERIFIED - 2026-10-04

IMP-050 provider capability registry/router implementation is LOCAL VERIFIED on branch `chatgpt/IMP-050-capability-provider-router` from base `9c6c8a68df6eba566e86aea680d6a892a815eb26`.

Verification:
- targeted `tests/unit/test_studio_provider_routing.py` = 13 PASS;
- affected regression = 75 PASS;
- broader valid Windows regression = 686 PASS / 3 deselected;
- Frozen Master guard PASS / semantic SHA unchanged `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`;
- compileall / diff check / forbidden-import scan / TODO scan PASS;
- evidence: `evidence/tests/IMP-050_PROVIDER_ROUTING_EVIDENCE.md`.

Authority/result:
- evidence-versioned ProviderProfile only; UNKNOWN never guessed;
- deterministic provider-neutral route decision over exact current ShotIR/Profile/ActiveProductionProfile/rule inputs;
- no hidden fallback; degradation only by explicit profile policy;
- exact dependency/invalidation truth reused;
- adapter/provider side effects excluded from canonical transaction;
- execution freshness requires explicit timezone-aware `as_of`.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-050 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"

---

## IMP-050 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

IMP-050 = MAIN VERIFIED
FEATURE_PR = #54
FEATURE_HEAD = c0201c0a3795f3ae63c5743a7c73e1c631bd23f0
MAIN_MERGE_SHA = 611318236bd57d4abbf193a59fd6276273345d79
PR_CI_RUN = 37185640898 SUCCESS Python 3.10 / 3.13 exact feature head
POST_MERGE_TARGETED = 13/13 PASS
POST_MERGE_AFFECTED = 75/75 PASS
FROZEN_MASTER_GUARD = PASS / 1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287
MAIN_PUSH_WORKFLOW = 37185793951 SUCCESS exact merge SHA
WORKTREE_AT_VERIFICATION = clean
GOVERNANCE_BRANCH = chatgpt/IMP-050-main-verified-state

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

ACTIVE_TASK = IMP-051 FLOW / OMNI PROVIDERADAPTER ANTI-CORRUPTION
STATUS = LOCAL VERIFIED / SIDE-EFFECT GUARD NEXT
BRANCH = chatgpt/IMP-051-provider-adapter-anti-corruption
BASE_HEAD = 0f8f1387f5aa9b3aacd5efe3ef240f1666306a98

Evidence:
- targeted = 18/18 PASS;
- affected regression = 186/186 PASS;
- broader valid Windows = 659 PASS / 3 deselected;
- complete valid unit-file coverage = 704 PASS / 3 deselected;
- frozen Master guard PASS / semantic SHA unchanged;
- py_compile + compileall + diff check PASS;
- neutral studio layer service/provider import leakage = NONE;
- evidence = `evidence/tests/IMP-051_PROVIDER_ADAPTER_EVIDENCE.md`.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-051 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"


---

## IMP-051 MAIN VERIFIED / GOVERNANCE SYNC - 2026-10-04

IMP-051 = MAIN VERIFIED
FEATURE_PR = #56
FEATURE_HEAD = ed7aff78e0cb35a7d5a44080777683d204d9d38c
MAIN_MERGE_SHA = 6f60c32d73ee447f638fd17775382d420807bdb1
PR_CI_RUN = 37216700657 SUCCESS Python 3.10 / 3.13
POST_MERGE_TARGETED = 18/18 PASS
POST_MERGE_AFFECTED = 186/186 PASS
FROZEN_MASTER_GUARD = PASS
MAIN_PUSH_WORKFLOW = 37216924329 SUCCESS exact merge SHA
GOVERNANCE_BRANCH = chatgpt/IMP-051-main-verified-state

NEXT_EXACT_ACTION = "COMMIT/PUSH/PR/MERGE IMP-051 GOVERNANCE SYNC -> VERIFY GOVERNANCE MAIN -> READ DAG/QUEUE -> CLAIM NEXT DEPENDENCY-READY TASK"


---

## IMP-051 GOVERNANCE VERIFIED / IMP-052 CLAIMED - 2026-10-04

IMP-051 governance PR #57 merged at `abbe70693f9282adf7ba2041deb20a09c6687a9c`.
Governance push-main workflow `37217851883` SUCCESS exact governance SHA.

ACTIVE_TASK = IMP-052 GENERATIONJOB FOUR-AXIS STATE MACHINE
STATUS = CLAIMED / AUTHORITY READ NEXT
BRANCH = chatgpt/IMP-052-generation-job-four-axis
BASE_HEAD = abbe70693f9282adf7ba2041deb20a09c6687a9c
DEPENDS = IMP-003 + IMP-004 + IMP-033 + IMP-051 MAIN VERIFIED

NEXT_EXACT_ACTION = "READ IMP-052 FROZEN GENERATIONJOB FOUR-AXIS / EXACT 62-ROW TRANSITION AUTHORITY + AUDIT CURRENT JOB/QUEUE/TRANSPORT SURFACES BEFORE CODE"


---

## IMP-052 AUTHORITY + CURRENT-SURFACE AUDIT PASS - 2026-10-04

ACTIVE_TASK = IMP-052 GENERATIONJOB FOUR-AXIS STATE MACHINE
STATUS = AUTHORITY + CURRENT SURFACE AUDIT PASS / CODE NEXT
BRANCH = chatgpt/IMP-052-generation-job-four-axis
BASE_HEAD = abbe70693f9282adf7ba2041deb20a09c6687a9c

Locked boundaries:
- exact 62-row closed transition relation = 15 scheduler + 19 provider + 14 artifact + 14 creative;
- four persisted orthogonal axes only; generic status is derived UI evidence;
- migration v6 on shared SQLiteWriteOwner/CAS; no parallel job store/writer;
- immutable exact ShotIR/routing/profile/input/submission identity; provider operation lineage durable;
- one-axis legal transition + full target tuple validation + append-only history + optimistic CAS;
- legacy request.status is compatibility-only;
- no network/provider call inside canonical DB transaction;
- NO RETRY WITHOUT PROOF remains blocking.

NEXT_EXACT_ACTION = "IMPLEMENT PERSISTENCE MIGRATION V6 + GENERATIONJOB TYPED CONTRACT/62-ROW VALIDATOR/REPOSITORY/CAS/HISTORY/DERIVED STATUS -> TARGETED TESTS"


---

## IMP-052 LOCAL VERIFIED - 2026-10-05

ACTIVE_TASK = IMP-052 GENERATIONJOB FOUR-AXIS STATE MACHINE
STATUS = LOCAL VERIFIED / SIDE-EFFECT GUARD NEXT
BRANCH = chatgpt/IMP-052-generation-job-four-axis
BASE_HEAD = abbe70693f9282adf7ba2041deb20a09c6687a9c

Evidence:
- targeted = 20/20 PASS;
- affected regression = 77/77 PASS;
- broader valid Windows regression = 647 PASS / 3 deselected;
- complete valid-unit coverage = 724 PASS / 3 deselected;
- frozen Master guard PASS / semantic SHA unchanged;
- py_compile + compileall + git diff --check PASS;
- exact transition table = 62 unique rows (15 scheduler + 19 provider + 14 artifact + 14 creative);
- provider/runtime/network leakage = NONE;
- evidence = `evidence/tests/IMP-052_GENERATION_JOB_EVIDENCE.md`.

Verified boundary:
- four persisted orthogonal axes are canonical; generic status is derived only;
- immutable exact ShotIR/routing/profile/input/submission identity;
- one-axis transition + full-tuple validation + CAS revision + append-only history;
- durable remote lineage cannot be rebound;
- no network/provider call inside canonical DB transaction;
- NO RETRY WITHOUT PROOF remains blocking.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> STAGE EXACT IMP-052 SCOPE -> COMMIT -> PUSH -> PR -> UBUNTU CI PYTHON 3.10/3.13 -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN -> GOVERNANCE SYNC"

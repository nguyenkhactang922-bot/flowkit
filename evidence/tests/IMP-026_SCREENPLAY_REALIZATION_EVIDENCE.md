# IMP-026 — Dialogue / Setup-Payoff / Screenplay Realization Evidence

Date: 2026-09-30
Branch: `chatgpt/IMP-026-screenplay-realization`
Base HEAD: `0672edaac2c8a8ec8bd39e0dd6fffa9cde1f6c5d`
Frozen Master semantic SHA: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`

## Canonical scope

Implemented provider-neutral, versioned contracts and repository for:
- DialogueIntent
- SetupPayoffLink
- ScreenplayScene
- FullScreenplay

Authority boundaries:
- dialogue owns communicative/subtext intent, not character/story truth;
- screenplay realization references accepted Scene/SceneDramaticBeat truth and cannot become a second Story/Scene master;
- setup/payoff ledger owns linkage/status only;
- legacy prompt/provider/runtime state is not canonical authority.

## Exact authority hardening

Final worktree additionally enforces:
- DialogueIntent speaker EntityVersion is exact-current, belongs to the project, and is EntityKind.CHARACTER;
- disclosed/withheld claim keys must exist in the exact CharacterKnowledgeState and cannot use UNKNOWN character knowledge;
- PAID/non-broken SetupPayoffLink binds exact StoryGraph SETUP/PAYOFF nodes and requires a PAYS_OFF edge;
- BROKEN setup/payoff findings cannot enter accepted screenplay realization;
- ScreenplayScene binds exact SceneBreakdownManifest and must realize its complete beat order;
- ScreenplayDialogueLine cannot realize claims not disclosed by its DialogueIntent;
- FullScreenplay directly binds canonical Scene refs plus ScreenplayScene realization refs and rejects mismatch;
- FullScreenplay setup/payoff refs exactly equal the links used by its screenplay scenes;
- revisions require exact-current predecessor and use immutable successors/CAS;
- dependency-reachable invalidation and ancestry traversal reuse shared repositories.

## Targeted tests

Initial targeted checkpoint before stale-speaker hardening:
- 11/11 PASS.

Final exact-worktree targeted result:
- `12 passed in 4.50s`
- exit code 0.

Covered:
- happy-path persistence + ancestry;
- UNKNOWN knowledge leak rejection;
- stale speaker EntityVersion rejection;
- StoryGraph PAYS_OFF trace;
- BROKEN setup/payoff rejection;
- exact breakdown beat coverage/order;
- dialogue claim realization discipline;
- direct Scene-realization match;
- dependency-reachable invalidation;
- stale historical revision predecessor rejection;
- project-prefix collision rejection;
- exact provenance binding.

## Affected regression

Final exact-worktree result:
- `114 passed in 25.46s`
- exit code 0.

Coverage includes:
- versioning
- invalidation
- entity
- topic/domain
- ActiveProductionProfile
- CharacterState
- StoryCore
- structure planning
- narrative hierarchy
- screenplay realization

## Broader Windows regression

One broader invocation became INTERRUPTED at the bridge boundary. Process inspection found no surviving pytest/uv process and no PASS/FAIL marker, so only that broader stage was rerun.

Final largest-valid Windows result:
- `567 passed, 3 deselected in 30.85s`
- exit code 0.

Known environment exclusions remain unchanged:
- `tests/unit/test_video_reviewer.py` ignored locally because ffmpeg is absent on the FileMCP Windows PATH;
- three previously documented POSIX-path assertions deselected.

## Frozen Master / static review

- `FROZEN_MASTER_GUARD=PASS`
- semantic SHA unchanged: `1ff9383d713dfaab309d3f36cc83cf05e8932c1bc07f68682e2e12a488c77287`
- `git diff --check` = PASS
- no requests/httpx/socket/subprocess/provider credential authority in canonical module
- no TODO/FIXME/NotImplemented placeholders
- exact-current revision gates present
- shared dependency invalidation and ancestry traversal present
- project-scoped IDs use delimiter-aware checks

## Local verdict

**IMP-026 = LOCAL VERIFIED**

Remote commit/push/PR/CI/merge/main verification remain pending.

NEXT_EXACT_ACTION = "SIDE-EFFECT GUARD -> COMMIT IMP-026 -> PUSH -> PR -> UBUNTU CI -> EXACT-HEAD REVIEW -> MERGE MAIN -> VERIFY MAIN"

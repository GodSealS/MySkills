# Oneshot template (attack / cast / hurt / die / jump / dash)

Use for actions with a clear start and end. Do not pass `--loop`; the clip plays once.

## Required slots

- **action verb**: the single decisive motion ("slashes downward", "collapses")
- **beats**: windup -> impact -> recovery, each one clause with its own amplitude
- **impact timing**: which beat carries the peak (drives `--duration`)
- **secondary motion**: weapon trail, cloth snap, dust, sparks, recoil
- **facing**: side / front / three-quarter, stated once
- **end state**: the pose the clip must land on (matters for chaining clips)

## Skeleton (stage form — preferred)

```
阶段1：起始可见状态（<facing>、姿态、道具归属） → <windup> → 蓄力完成的可观察状态。
阶段2：承接蓄力状态 → <impact>（峰值落在片段中段） → 出手后的可观察状态。
阶段3：承接出手状态 → <recovery> → 最终停在<end state>。
<secondary motion>跟随动作强度变化；<实体清单与必要否定>。
```

Each stage ends in a state the next inherits; the impact beat must land inside the
middle third of the clip. Keep the declared end state exact — it is what makes the
clip chainable with the next action.

## Prompt rules

- No parameter words in the context (seconds, fps, resolution, ratio, model names).
- Describe the character by appearance, not by proper name; state prop counts and
  ownership, and negate leakage-prone variants.
- Do not pad: a longer clip expands windup/recovery detail, never adds a new
  character, a repeated strike or a different ending.
- The CLI already adds the locked-camera constraint and the first-frame role.

## Duration guidance

- 2-3 s: hits, hurt flinches, short casts
- 4-6 s: full attack combos, death falls, charged casts
- Longer than 6 s: split into chained clips instead; per-second billing makes one
  long clip the expensive option and chaining keeps each end state controllable.

## Acceptance cues for Phase 7

- the impact beat lands inside the middle third of the clip
- the final frame matches the declared end state (chainability)
- no camera drift; weapon/prop silhouette stays connected to the hand across frames

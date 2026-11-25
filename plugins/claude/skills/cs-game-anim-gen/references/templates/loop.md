# Loop template (idle / walk / run / breathe / float)

Use for any action that must repeat seamlessly. Always pass `--loop`.

## Required slots

- **action verb**: the repeating motion in one clause ("stands breathing",
  "walks in place", "hovers bobbing gently")
- **amplitude**: small / medium / large, named per body part that moves
- **secondary motion**: hair, cloth, cape, props, particles that follow the body
- **facing**: side / front / three-quarter, stated once
- **cycle feel**: relaxed, alert, exhausted, menacing — drives amplitude and tempo

## Skeleton

```
角色以<facing>朝向<action verb>，幅度<amplitude>；<secondary motion>自然跟随。
动作节奏<cycle feel>，全程保持同一姿态基准与画面占比。
<实体清单：每个道具的数量与归属，如“剑始终背在背后，葫芦始终在左手”>
<必要时加否定：武器不是刀，袍色不是红>
```

For a loop with distinguishable beats (a walk cycle's contact / down / pass / up),
use stages instead of one sentence:

```
阶段1：起始可见状态 → 一个具体动作 → 可观察结束状态。
阶段2：承接上一状态 → 一个具体动作 → 回到阶段1的起始状态。
```

## Prompt rules

- No parameter words in the context: never write seconds, fps, resolution, ratio
  or model names — those are CLI arguments.
- Describe the character by appearance, not by proper name.
- Do not pad the cycle: extra duration becomes preparation, pauses and secondary
  motion, never repeated filler or a new character.
- The CLI already adds the locked-camera constraint, the first-frame role and the
  loop-closure instruction; do not repeat them.

## Negatives to fold into the context when the style needs them

camera movement, zoom, pan, cut, scene change, extra characters, background change,
limb stretching, proportion change, face change, costume change

## Acceptance cues for Phase 7

- first and last sampled frames differ only by sub-pixel amounts
  (`metrics.loop_seam_mean_abs_diff` low) and the GIF shows no visible jump
- silhouette returns to its starting outline; secondary motion settles with the body
- background pixels stationary across the contact sheet

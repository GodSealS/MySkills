# Prompt shapes for game audio

English prompts work best (the model's caption training is English-dominant); lyrics
can be any supported language (`--language zh` etc.). Keep parameters (bpm, key,
duration, format) in CLI flags, never inside the prompt text.

## Music prompt = genre + instrumentation + energy/mood + tempo feel + game role + constraints

Combine:

- genre/instrumentation: "orchestral fantasy score", "chiptune 8-bit", "lo-fi hip hop",
  "ambient synth pads", "acoustic guitar and soft strings";
- energy/mood: "calm and hopeful", "tense and urgent", "triumphant", "eerie";
- game role: "main menu background", "village exploration loop", "boss battle",
  "victory stinger", "dungeon ambient bed";
- constraints: "no vocals", "seamless loop feel", "not distracting", "minimal melody,
  texture-focused" when needed.

### Starting points (audition, then adapt to the project's direction)

| Scene | Prompt skeleton | Flags |
|-------|-----------------|-------|
| Menu / village | calm fantasy village menu theme, warm acoustic guitar and soft strings, gentle and hopeful, seamless loop feel | `--duration 30 --bpm 90` |
| Exploration | light adventurous exploration loop, flute and pizzicato strings, curious and upbeat, steady rhythm | `--duration 60 --bpm 110` |
| Battle | intense battle theme, driving percussion and urgent staccato strings, aggressive energy, heroic brass accents | `--duration 60 --bpm 140` |
| Boss | epic boss battle, dark orchestral hits, choir accents, relentless double-kick drums, menacing | `--duration 60 --bpm 150` |
| Dungeon / horror | dark ambient dungeon bed, low drones, sparse metallic echoes, uneasy and cold, no melody | `--duration 60` |
| Victory | short triumphant victory fanfare, bright brass and snare rolls, heroic and conclusive | `--duration 10` |
| Sad / story | melancholic story moment, solo piano with distant strings, tender and sorrowful, slow | `--duration 30 --bpm 70` |
| Sci-fi / cyber | synthwave pursuit, pulsing analog bass, neon arpeggios, tense futuristic energy | `--duration 60 --bpm 120` |

Looping: "seamless loop feel" nudges the arrangement but does not guarantee a clean
loop point — audition the seam (Phase 6) and trim/crossfade downstream.

## Vocal theme songs

Lyrics carry the words and structure; the prompt carries the style. Never duplicate
lyrics in the prompt.

```text
prompt: "uplifting anime-style opening theme, bright electric guitars and synth bells,
         soaring female vocal, hopeful and energetic"
lyrics: "[Verse]\n...(user's words)...\n[Chorus]\n..."
flags:  --lyrics-file theme.txt --language zh --duration 60
```

Preserve user-supplied lyrics as-is; when asked to write lyrics, draft a compact
original structure and get approval before generating. Do not copy lyrics from named
songs or imitate a named living artist.

## SFX prompt = source + action + material/space + perspective + "no music, no melody"

ACE-Step is a music model: describe SFX as concrete physical sounds and explicitly
exclude music. Generate 10 s, then trim the one-shot (`--trim-start/--trim-end`).

| Family | Prompt skeleton | Trim idea |
|--------|-----------------|-----------|
| Weapon hit | single sharp sword clash metal hit, bright transient, short decay, dry close-mic, no music, no melody | 0–2 s |
| Bow / shot | single bowstring release with arrow whoosh, tight transient, dry, no music | 0–2 s |
| Explosion | one deep explosion blast with rumbling debris tail, cinematic, no music, no melody | 0–4 s |
| Magic | single magical sparkle cast, shimmering chime burst with airy tail, fantasy, no music | 0–3 s |
| UI click | single soft UI click blip, clean digital tick, very short, dry, no music, no melody | 0–1 s |
| Footstep | single footstep on gravel, crisp crunch, close-mic, dry, no music | 0–1 s |
| Ambient | forest night ambience, crickets and distant owl, gentle wind in leaves, continuous texture, no music | keep 10 s+ |
| Whoosh | single fast whoosh transition, airy sweep left to right, short, no music | 0–2 s |

Tips:

- "single ... one ..." discourages repeated patterns; audition and re-trim if the
  model produced a rhythmic loop instead of a one-shot.
- Pick the trim window around the transient you hear; dead air at the head breaks
  game feel. Keep tails natural (don't cut a reverb tail mid-decay unless intended).
- For families of effects (hit_01..03), keep the prompt identical and vary `--seed`;
  loudness-match downstream in the engine.
- Dry UI clicks and precise foley are the model's weak spot — if two prompt
  adjustments still read musical, flag the asset for a dedicated SFX tool
  (see the Stable Audio Open route in local-models.md) instead of burning retries.

## Reference-audio prompts

With `--reference-audio`, the prompt should describe the **target** use and energy;
the reference supplies the palette. Example: reference = calm menu theme, prompt =
"intense battle variation, driving percussion and urgent strings, aggressive energy,
same instrumental palette as the reference", `--cover-strength 0.2`, `--bpm 140`.
Raise strength (0.4–0.7) to stay closer to the reference; lower (0.1) for a loose hint.
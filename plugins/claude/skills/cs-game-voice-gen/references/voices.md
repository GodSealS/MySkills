# Voice catalog and audition protocol

Load when picking a character voice. Source: official
[Qwen-Audio-TTS 音色列表](https://platform.qianwenai.com/docs/developer-guides/speech/voice-list/qwen-audio-tts),
checked 2026-11-18. **Voices are model-specific — never mix across models** (see hard
rules below). The old Cherry/Ethan-style catalog belongs to the separate Qwen3-TTS API
family and does NOT apply here.

## qwen-audio-3.0-tts-plus (default model)

System voices (prefer these for stability; both support SSML, instruction control and
word timestamps):

| Voice id | Name | Gender/age | Languages | Timbre |
|----------|------|-----------|-----------|--------|
| `longanlingxin` | 龙安灵心 | female, 25 | Mandarin, English | 知心温暖音 (warm, caring) |
| `longanlufeng` | 龙安鲁风 | male, 25 | Mandarin, English | 明亮开朗音 (bright, cheerful) |

Plus 500+ base voices (voice-cloning derived), named `qwen-audio-3.0-tts-plus-{suffix}`,
called exactly like system voices. Full list is an Excel attachment, not a web table:
[plus 基础音色.xlsx](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20260723/ydwqqz/qwen-audio-3.0-tts-plus%E5%9F%BA%E7%A1%80%E9%9F%B3%E8%89%B2.xlsx)
with a shared [audition audio pack](https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20260720/tuuuqo/%E5%9F%BA%E7%A1%80%E9%9F%B3%E8%89%B2%E8%AF%95%E5%90%AC%E9%9F%B3%E9%A2%91%E5%8C%85.zip)
(match the Excel "预览音频文件名" column to files in the pack). Download and filter these
only when the two system voices cannot cover the character.

## qwen-audio-3.0-tts-flash (character voices, cheaper)

Useful game character voices documented on the same page:

| Voice id | Name | Profile |
|----------|------|---------|
| `longanhuan_v3.6` | 龙安欢 | female flagship |
| `longanyuanfei` | 龙安元妃 | female, haughty concubine |
| `longpaopao_v3.6` | 龙泡泡 | female, 5 y/o, soft cute child |
| `longhuohuo_v3.6` | 龙火火 | male, 8 y/o, naughty boy (game character voice) |
| `longchuanshu_v3.6` | 龙川叔 | male, Sichuan-flavored uncle |
| `longjielidou_v3.6` | 龙杰力豆 | character voice |
| `loongmary` / `loongjohn` / `loongeva_v3.6` | — | English voices; **no instruction/SSML/timestamp support** |

Also `longanfengyue`, `longanlingxi`, `longanxiaoxin` (see the official page).

## qwen-audio-3.1-tts-plus / -flash (newer flagship, token-billed)

Voices carry the `_v3.1` suffix, e.g. `longanlingxin_v3.1`, `longanhuan_v3.1` (flagship
female with exaggerated emotional expression), `longshanshan_v3.1` (dramatic child),
`longanchong_v3.1` (passionate salesman), `longhao_v3.1` (melancholic), `longqiang_v3.1`
(romantic). 3.1-flash adds multilingual/dialect voices with `language_hints` (not wrapped
by the CLI; see provider notes).

## Hard matching rules (provider-enforced)

1. The voice must belong to the selected model. Cross-model use returns
   `InvalidParameter`, e.g. `[cosyvoice:]Engine error [411]: TTS speak operation failed`.
2. Same name ≠ same id: `longanlingxin` (3.0-plus) vs `longanlingxin_v3.1` (3.1).
   Adding/dropping a suffix crosses models.
3. Suffix is not a reliable model indicator: `loongmary`/`loongjohn` have no suffix but
   belong to 3.0-flash; `longanhuan_v3.6` is 3.0-flash, not 3.1. Always take ids from
   the model's own section of the official page.
4. Base voices must carry the full model prefix: `qwen-audio-3.0-tts-plus-{suffix}`.
5. Text language should match the voice's supported languages.
6. Emotion/delivery control needs an instruction-capable voice (both 3.0-plus system
   voices qualify; the English flash voices above do not).

## Archetype suggestions (starting points, not rules)

| Archetype | Candidate (model) | Baseline instruction example |
|-----------|-------------------|------------------------------|
| hero / leading male | longanlufeng (3.0-plus) | 沉稳坚定，语速适中 |
| heroine / leading female | longanlingxin (3.0-plus) | 清亮自然，语气坚定 |
| female in panic / distress | longanlingxin (3.0-plus) | 惊恐颤抖，带哭腔，语速急促断续 |
| villain / haughty female | longanyuanfei (3.0-flash) | 高傲阴冷，慢条斯理 |
| child / sprite | longpaopao_v3.6 (3.0-flash) | 软糯可爱，音调偏高 |
| naughty boy | longhuohuo_v3.6 (3.0-flash) | 顽皮活泼，语速快 |
| comic relief / dialect | longchuanshu_v3.6 (3.0-flash) | 川普方言，夸张俏皮 |
| dramatic female lead | longanhuan_v3.1 (3.1-plus) | 情绪饱满，戏剧化表达 |
| narrator | longanlufeng / longanlingxin (3.0-plus) | 客观平稳，旁白感 |

A character keeps ONE voice across all lines; per-line `instructions` carry the emotion.
The 3.0-plus system voices are warm/companion-oriented by default — strong drama relies
on `instruction`, and the effect must be confirmed by audition (the official page gives
no emotion examples for 3.0-plus).

## Audition protocol

1. Pick 1–2 candidates per character from the tables above (state the assumption when the
   user gave no direction).
2. Generate one signature line per candidate — a line that shows the character's typical
   emotion, e.g. `--name <character>-audition-<voice>`.
3. Play the takes for the user; record the approved voice + baseline instructions as the
   character profile (project voice direction doc or the batch manifest's character entries).
4. Only then batch-dub. Re-audition when the character direction or the model changes.

If the provider rejects a voice with `InvalidParameter`, check the model/voice matching
rules above before trying another id; do not brute-force guessed names.

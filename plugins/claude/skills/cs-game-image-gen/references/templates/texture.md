# Texture Templates (Material Maps)

Load this file only for `texture` requests. Pick one subtype, fill the skeleton,
pass the negative prompt via `--negative`.

**Scope boundary (v1):** these models output color (albedo) images only. Normal,
roughness, AO and height maps must be derived downstream (e.g. Blender tooling,
Materialize). State this to the user instead of pretending a full PBR set was generated.

## Common hard requirements for ALL texture prompts

Always include: `seamless tileable texture, top-down orthographic view, flat uniform
lighting, no shadows, no highlights, no perspective, no objects, surface fills entire frame`

Always include in negative: `lighting, shadows, perspective, objects, border, frame,
watermark, text, vignette`

## Routing

| Subtype | Trigger keywords |
|---------|-----------------|
| organic | 木纹、皮革、布料、皮肤、植被、苔藓、骨质 |
| inorganic | 金属、石材、砖墙、陶瓷、混凝土、锈板 |
| special | 发光、能量、魔法、液体、熔岩、水晶表面 |

---

## organic（有机材质）

**Prompt skeleton**:
1. 材质名称与来源：如"风化橡木板"、"鳄鱼皮"、"粗织亚麻布"
2. 纹理结构：纹路方向（直纹/交错/无序）、密度、尺度
3. 颜色范围：主色 + 变化色（自然色差是可信度关键）
4. 表面瑕疵：节疤、裂纹、磨损、污渍分布
5. 通用硬性要求（见上）
6. 技术要求：`seamless tileable PBR albedo texture, 1:1 aspect ratio`

**必填槽位**：纹路方向、至少两种自然色差。

**推荐参数**：model=wan2.7-image, size=1K, n=4（一次出 4 个候选变体供挑选）

---

## inorganic（无机材质）

**Prompt skeleton**:
1. 材质名称与加工状态：如"拉丝不锈钢"、"凿面花岗岩"、"生锈铁板"
2. 纹理结构：图案规律（砖缝排布/铆钉行列）或随机度（锈斑分布）
3. 颜色范围：基色 + 氧化/污渍色
4. 表面细节：划痕、凹坑、边缘磨损（重点在凸起边缘）
5. 通用硬性要求（见上）
6. 技术要求：`seamless tileable PBR albedo texture, 1:1 aspect ratio`

**必填槽位**：加工状态、图案规律或随机度描述。

**推荐参数**：model=wan2.7-image, size=1K, n=4；砖墙等规则图案在 prompt 中写明
排布方式（如 running bond / herringbone），生成后检查平铺接缝，不 seamless 则重roll

---

## special（特殊/魔法材质）

**Prompt skeleton**:
1. 材质概念：如"熔岩裂纹地表"、"奥术能量表面"、"史莱姆凝胶"
2. 发光逻辑：发光部分的分布规律与颜色（发光将影响下游 emissive 通道）
3. 基础表面：非发光部分的材质质感
4. 流动/动态暗示：静态图中体现流动感的纹路方向
5. 通用硬性要求（见上）
6. 技术要求：`seamless tileable game texture, 1:1 aspect ratio, glowing details on dark base`

**必填槽位**：发光分布规律、基础表面材质。

**推荐参数**：model=wan2.7-image-pro（复杂发光结构需要旗舰模型）, size=1K, n=4

**注意**：发光材质生成后提醒用户——发光区域可作为下游 emissive mask 的参考，
但需要人工分离。

## Verification for all textures

生成后必须检查平铺性：将图片 2x2 平铺预览（可用任意图像工具或让 Agent 生成预览），
接缝明显则调整 prompt 重roll，不得把有明显接缝的图当作 seamless 交付。

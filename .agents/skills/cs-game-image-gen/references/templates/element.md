# Element Templates (Props & Machines)

Load this file only for `element` requests. Pick one subtype, fill the skeleton,
append a style preset, pass the negative prompt via `--negative`.

## Routing

| Subtype | Trigger keywords |
|---------|-----------------|
| prop | 道具、武器、装备、宝箱、消耗品、收集物、任务物品 |
| machine | 机器、装置、引擎、传送门、载具、机关 |

---

## prop（道具/武器/物品）

**Prompt skeleton** (fill in order):
1. 物品类型与用途：武器/防具/药水/钥匙/收藏品 + 游戏内功能
2. 造型语言：形状轮廓（silhouette 优先，保证缩略图可辨识）
3. 材质组合：主材质 + 辅材质（如"生锈铁刃 + 皮革缠柄 + 黄铜护手"）
4. 细节叙事：使用痕迹、附魔发光、所属阵营的纹章/符号
5. 稀有度暗示（可选）：普通/稀有/史诗的视觉等级差异
6. 构图：纯白或深灰简洁背景，居中，轻微 3/4 视角；物品设定图可多件网格排列
7. 技术要求：`game prop concept art, clean background, centered, product-shot lighting`

**必填槽位**：轮廓描述、至少两种材质、一个叙事细节。

**Negative**：`cluttered background, cropped edges, blurry details, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=1K（单件）；物品图标集用 n=4 + sequential

**落地建议**：简洁背景便于抠图进 UI 或转 3D。

---

## machine（机器/装置/载具）

**Prompt skeleton**:
1. 装置类型与功能：做什么用、能量来源（蒸汽/电力/魔法）
2. 结构组成：主体框架、运动部件、连接管线/传动结构
3. 材质与做旧：金属类型、油漆、油污锈蚀、维护痕迹
4. 工作状态（可选）：运转中的发光/蒸汽/电弧效果
5. 比例参照：与人物的尺寸对比
6. 视角：3/4 展示视角或正交多视图
7. 技术要求：`machine design concept art, functional parts visible, hard surface, clean background`

**必填槽位**：功能描述、能量来源、一个运动部件。

**Negative**：`organic shapes, blurry mechanics, impossible assembly, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=2K；大型载具/装置多视图用 n=4 + sequential

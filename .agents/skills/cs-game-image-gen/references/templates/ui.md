# UI Templates (Panels / HUD / Icons)

Load this file only for `ui` requests. Pick one subtype, fill the skeleton,
pass the negative prompt via `--negative`.

**Model rule:** 未指定模型时，带文字的 UI 首选 `qwen-image-3.0-pro`；纯风格探索可用 wan 系。
费用与限流遵循 SKILL.md Phase 2，并按接入方式查询 provider notes。

## Routing

| Subtype | Trigger keywords |
|---------|-----------------|
| panel | 面板、背包、商店、技能树、对话框、设置、主菜单 |
| hud | HUD、血条、小地图、技能栏、战斗界面、准星 |
| icon | 图标、icon、技能图标、物品图标、图标集 |

---

## panel（功能面板）

**Prompt skeleton** (fill in order):
1. 面板类型与用途：背包/商店/技能树/设置 + 玩家在此做什么
2. 布局结构：分区（标题栏/内容区/侧栏/底部按钮），栅格数量（如 6x4 格子）
3. 视觉风格：与游戏世界观匹配（奇幻羊皮纸/科幻全息/卡通描边）+ 主题色
4. 组件清单：按钮、页签、滑条、进度条、关闭钮的样式与位置
5. 文字内容：真实文案（用 qwen 系）或占位符（探索期）；注明字号层级
6. 目标平台与纵横比：移动端竖屏 9:16 / PC 横屏 16:9 / 面板局部 4:3
7. 技术要求：`game UI panel design mockup, clean layout, readable text, flat design`

**必填槽位**：分区结构、主题色、纵横比、文字策略（真实/占位）。

**Negative**：`garbled text, misspelled words, overlapping elements, cropped buttons, watermark`

**推荐参数**：model=qwen-image-3.0-pro, n=1~2；size 使用明确像素尺寸，
如横屏 `1536*864`、竖屏 `864*1536`、局部面板 `1024*768`，以用户指定尺寸为准。

---

## hud（战斗内界面）

**Prompt skeleton**:
1. 游戏类型与视角：FPS/第三人称/MOBA/横版 + HUD 依附的画面
2. 元素清单与锚位：血条(左上)、小地图(右上)、技能栏(底部居中)、buff 图标、准星
3. 视觉风格：半透明玻璃/金属描边/极简线性 + 主题色与警告色
4. 状态表达：满血/残血、技能冷却、受击闪烁的视觉差异
5. 留白原则：屏幕中央保持干净，元素贴边
6. 技术要求：`game HUD design mockup, screen corners anchored, semi-transparent, 16:9`

**必填槽位**：至少 4 个 HUD 元素及其锚位、主题色。

**Negative**：`center clutter, opaque blocks, garbled text, watermark`

**推荐参数**：model=qwen-image-3.0-pro, size=`1536*864`（16:9，用户可指定其他尺寸）, n=1~2

---

## icon（图标/图标集）

**Prompt skeleton**:
1. 图标用途：技能/物品/系统功能，列出具体清单（如"火球术、冰霜新星、治疗"）
2. 网格排版：`NxM grid layout, each icon in its own cell`（推荐 2x2 或 3x2）
3. 统一风格：描边粗细、底色形状（圆角方/圆形/盾形）、光影方向必须一致
4. 辨识度要求：每个图标 silhouette 独特，缩到 64px 仍可区分
5. 技术要求：`game icon set, consistent style, grid layout, clean background per cell`

**必填槽位**：图标清单、网格规格、统一底板形状。

**Negative**：`inconsistent style, mixed shapes, garbled text, watermark, blurry edges`

**推荐参数**：
- qwen-image-3.0-pro 单图网格排版（首选，风格一致性靠同一张图保证）
- 或 wan2.7-image-pro `--n 4 --sequential` 生成同风格多张（每张单图标）

**落地建议**：网格图交付后提示用户需要切图（cell 裁切）才能进引擎。

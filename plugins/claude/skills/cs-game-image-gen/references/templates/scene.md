# Scene Templates

Load this file only for `scene` requests. Pick one subtype, fill the skeleton,
append a style preset, pass the negative prompt via `--negative`.

## Routing

| Subtype | Trigger keywords |
|---------|-----------------|
| environment | 场景、关卡、全景、世界、地形、氛围图、establishing shot |
| architecture | 建筑、城堡、神殿、房屋、塔楼、桥梁、单体结构 |

---

## environment（宏观场景/关卡）

**Prompt skeleton** (fill in order):
1. 场景类型与世界观：自然环境/城市/遗迹/地下城 + 时代与文明水平
2. 空间结构：前景-中景-远景三层各放什么，视线引导路径
3. 地标元素：一个视觉焦点（巨树/瀑布/废墟/山脉）
4. 天气与时间：时段、季节、天气现象（雾/雨/雪/沙尘）
5. 光照氛围：光源方向与颜色、阴影情绪（压抑/希望/神秘）
6. 玩法暗示（可选）：可通过路径、可攀爬点、敌人出没区域
7. 技术要求：`game environment concept art, wide establishing shot, cinematic composition, matte painting quality`

**必填槽位**：三层空间结构、时间天气、一个地标焦点。

**Negative**：`flat lighting, empty composition, watermark, text, ui elements, people in focus`

**推荐参数**：model=wan2.7-image-pro, size=2K；宽幅构图优先（16:9 类尺寸）

---

## architecture（建筑单体）

**Prompt skeleton**:
1. 建筑类型与功能：神殿/城堡/民居/工厂 + 在世界观中的用途
2. 建筑风格：哥特/巴洛克/中式/奇幻/科幻 + 参考文明
3. 结构合理性：承重结构、楼层、屋顶形式、入口位置
4. 材质：石材/木材/金属/混凝土，风化与使用痕迹
5. 尺度参照：与人物或树木的比例，体现体量
6. 视角与光照：3/4 外景视角或剖面图；时段光照
7. 技术要求：`architecture concept art, structurally plausible, scale reference, detailed facade`

**必填槽位**：建筑风格、主材质、一个尺度参照物。

**Negative**：`floating structures, impossible geometry, blurry details, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=2K；需要多视角时用 n=4 + sequential
（正面/侧面/背面/细节）

# Character Templates

Load this file only for `character` requests. Pick one subtype, fill the skeleton,
append a style preset, pass the negative prompt via `--negative`.

## Routing

| Subtype | Trigger keywords |
|---------|-----------------|
| humanoid | 人类、精灵、矮人、骑士、法师、NPC、角色立绘、主角 |
| creature | 动物、怪兽、怪物、龙、坐骑、宠物、Boss 生物 |
| mech | 机甲、机器人、构造体、装甲、载具人 |

---

## humanoid（人形/类人角色）

**Prompt skeleton** (fill in order):
1. 主体：种族/职业/年龄/性别 + 一句话身份定位
2. 体型与姿态：身材特征、标志性姿势、表情气质
3. 服装装备：材质（布料/皮革/金属）、剪裁、磨损程度、配色
4. 细节道具：武器、饰品、携带物
5. 构图：角色设定图排版（正面+侧面+背面三视图）或单体立绘（全身/半身）
6. 光照氛围：主光方向、轮廓光、背景（纯色/简单场景）
7. 技术要求：`character design sheet, full body, clean background, high detail`

**必填槽位**：身份定位、服装主材质、配色方案（至少 2 色）。

**三视图/设定图**：用 `wan2.7-image-pro --n 4 --sequential`，prompt 中写明
"same character, consistent design, front view / side view / back view / detail close-up"。

**Negative**：`extra limbs, extra fingers, deformed hands, asymmetrical eyes, blurry face, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=2K, n=1（单立绘）/ n=4 + sequential（设定图）

---

## creature（动物/怪兽/生物）

**Prompt skeleton**:
1. 主体：物种原型（真实动物/神话生物/杂交）+ 生态定位（掠食者/坐骑/宠物）
2. 解剖与体态：体型参照物（如"肩高约 3 米，相当于大象"）、骨架结构、比例
3. 表皮材质：毛发/鳞片/甲壳/皮肤质感与颜色，磨损或战斗痕迹
4. 动态特征：至少一个动作或姿态（咆哮、潜行、展翅）
5. 镜头构图：全身侧面或 3/4 视角，展示完整轮廓
6. 环境氛围：栖息地暗示、光照
7. 技术要求：`creature concept art, full body, anatomically plausible, clean background`

**必填槽位**：体型参照、表皮材质、一个动态特征。

**Negative**：`anatomy broken, extra limbs, blurry fur, floating parts, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=2K；多姿势表用 n=4 + sequential

**落地建议**：干净背景便于后续抠图；转 3D 时交给 `cs-img2threejs`。

---

## mech（机甲/机器人/构造体）

**Prompt skeleton**:
1. 主体：类型（人形机甲/无人机/魔法构造体）+ 用途定位（战斗/工程/侦察）
2. 硬表面结构：装甲分块、关节暴露程度、机械细节密度
3. 材质面板：金属类型、涂装、做旧/战损、发光部件（能量核心/眼部）
4. 比例参照：高度、与人体对比
5. 构图：正交三视图（front/side/back orthographic）或英雄视角单体
6. 光照：工业打光或能量自发光
7. 技术要求：`mech design sheet, hard surface, orthographic views, panel lines, high detail`

**必填槽位**：装甲分块描述、至少一种材质面板、发光部件位置。

**Negative**：`organic shapes, blurry details, melting parts, watermark, text`

**推荐参数**：model=wan2.7-image-pro, size=2K；三视图用 n=4 + sequential 并在 prompt 写明各视角

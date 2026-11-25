# Style Presets（风格词表，横切维度）

风格与子类模板正交：最终 prompt = 子类骨架 + 风格短语 + 用户描述。
风格来源和未指定风格时的处理遵循 SKILL.md Phase 1；本文件只提供可选短语。

| 风格 | 追加短语 | 适用游戏类型 |
|------|---------|-------------|
| 写实 | `photorealistic, realistic lighting, physically based materials` | 3A、写实射击、生存 |
| 厚涂概念 | `digital painting, concept art style, painterly brushwork` | RPG、通用概念图 |
| 二次元赛璐璐 | `anime style, cel shading, clean lineart, vibrant colors` | 二次元、卡牌、视觉小说 |
| 卡通渲染 | `stylized 3D render, cartoon shading, soft gradients, Pixar-like` | 休闲、家庭向 |
| Low-Poly | `low poly style, faceted geometry, flat shading, minimal detail` | 独立、风格化手游 |
| 像素 | `pixel art, 16-bit / 32-bit sprite style, limited palette, crisp pixels` | 复古、Roguelike |
| 水墨/国风 | `chinese ink painting, brush strokes, negative space, traditional colors` | 武侠、国风题材 |
| 手绘绘本 | `hand-drawn illustration, storybook style, soft textures, warm palette` | 叙事、解谜、儿童向 |
| 暗黑哥特 | `dark gothic style, desaturated palette, dramatic chiaroscuro, grim atmosphere` | 魂类、恐怖 |
| 赛博朋克 | `cyberpunk style, neon lighting, high contrast, rain-slicked surfaces` | 科幻、都市题材 |

## 使用规则

1. 一次只用一个主风格；需要混合时（如"像素+暗黑"）把两者短语拼接并保留各自关键词
2. 整批资产沿用同一风格短语，生成后仍需检查实际一致性
3. 同一系列资产（如整套角色设定）用 `--sequential` 或把首张结果作为后续参考图
4. UI 类慎用重绘画风格（厚涂/水墨会干扰文字渲染），优先 flat design + 风格化边框

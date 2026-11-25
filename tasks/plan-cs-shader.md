# Plan: 迁移 shader-effects-inc/shaders 为 cs-shader 技能

状态：待批准（planning-only）
日期：2026-11-24
上游：https://github.com/shader-effects-inc/shaders （MIT，引擎+组件+skill 内容；
shaders.com 的 presets/编辑器为独立付费条款，不随包迁移）

## 目标

把上游自带的 Agent Skill（`skills/shaders/SKILL.md` + `components.md`）改造为符合本
pack 规范的 `cs-shader`：WebGPU 网页视觉特效（React/Vue/Svelte/Solid/原生 JS）。
默认走免费、无账号的手搓组件路径；厂商 CLI/账号/Pro/MCP 降级为需显式批准的可选分支。

非目标：游戏引擎（Unity/Unreal/Godot/Cocos）着色器；WebGL 回退（上游不支持）。

## 已核实事实（证据）

- 上游 SKILL.md 为指令型：强制先 `npx shaders connect`（登录账号+连远端项目+写 config），
  preset 安装需 Pro 订阅，`install-mcp` 改 MCP 配置，`update --force` 覆盖本地修改。
- `components.md`：200 组件、10 分类、约 20KB；自动生成（Do not edit）；约 98 个
  `(needs input)` 效果型标记；无 Pro 标记；精确 props 需抓
  `https://shaders.com/docs/components/<Name>`（须 `Accept: text/markdown`）。
- 本 pack 规范（参照 `cs-game-image-gen`）：frontmatter name + 双语触发式 description；
  When to Use / Prerequisites / Workflow(Phases) / Core Constraints /
  Recommended Next Steps / Verification 清单；skill-local references 按需加载。
- 权威源 `.codebuddy/skills/`；改后运行 `scripts/build-adapters.ps1` 再生成各平台适配，
  `scripts/test-adapters.ps1` 验证；质量检查用 `cs-skill-review`。

## 设计

### 目录结构（新增，均在 .codebuddy/skills/cs-shader/）

```
cs-shader/
├── SKILL.md                      # 重写，主路径零厂商命令、零账号
└── references/
    ├── components.md             # 上游快照，逐字保留（Do not edit 语义）
    ├── composing.md              # 图层模型/blend/mask/boundingBox/Group/dynamic props/框架 idioms
    ├── recipes.md                # 4 个官方 recipe + 性能规则 + Don'ts
    ├── vendor-workflows.md       # 可选分支：CLI(connect/install/search/preview/update)/MCP/Pro 边界
    └── provenance.md             # 上游 repo + commit SHA + 抓取日期 + MIT 许可声明
```

### SKILL.md 工作流（主路径）

- Phase 1 范围判定：确认是 Web 项目、识别框架与元框架 SSR 约束（Next 'use client' /
  Nuxt ClientOnly / SolidStart clientOnly）；游戏引擎 shader 请求 → 明确不覆盖并路由出去。
  声明 WebGPU 硬前提（无 WebGL 回退，不支持时向用户说明）。
- Phase 2 选组件：读本地 `components.md` 快照；优先 1–2 个组件手搓；精确 props 按需抓
  官方组件文档页（只读网络请求，带 Accept: text/markdown）；禁止臆造 prop。
- Phase 3 装依赖：用项目自身包管理器安装 npm `shaders`（第三方代码，执行前需用户确认）；
  无需账号、无需 connect。
- Phase 4 组合效果：按需加载 composing.md / recipes.md；扁平堆叠、effect 作用于先前图层、
  遮罩/定位/dynamic props 规则；CSS 给 `<Shader>` 定尺寸，绝不样式化内层 canvas。
- Phase 5 验证：起 dev server，用 `cs-browser-test` 实机确认 WebGPU 渲染并截图；
  记录 pass/fail；WebGPU 不可用时如实报告而非静默降级。

### 可选分支（仅用户显式要求时加载 vendor-workflows.md）

- `npx shaders search`（免费只读）→ `preview` → `install <preset>`（Pro 付费）。
- 尊重付费墙：不绕过 Pro；只允许官方水印预览评估（上游原文约束）。
- connect / install-mcp / update --force / --yes / SHADERS_API_KEY 等涉及账号、凭据、
  配置改写、覆盖本地文件的操作：逐项列出副作用，取得用户显式批准后才执行；
  凭据不落仓库、不回显。

### Core Constraints（要点）

- 仅 Web + WebGPU；SSR 禁止渲染 `<Shader>`。
- 库已覆盖的效果不引入 three/@react-three/fiber/ogl/裸 WebGL。
- 快照可能漂移：精确 props 以官方组件页为准；provenance.md 记录快照版本。
- presets/sections 属 shaders.com 独立条款，非 MIT，不得复制进本 pack。
- 厂商副作用命令一律显式批准（对齐 cs-security）。

### Recommended Next Steps

页面集成 → `cs-frontend-ui` / `cs-huashu-design`；实机验证 → `cs-browser-test`；
性能问题 → `cs-perf-opt`。

## 任务切片

### T1 冻结上游资产（依赖：无）
- 产出：`references/components.md` 逐字快照 + `provenance.md`（repo、commit SHA、
  日期、MIT 声明）；抓取上游 SKILL.md 原文留作 T2 改写底稿（临时，不入包）。
- 验收：components.md 含 200 条目/10 分类；provenance 含可追溯 commit；许可文本保留。
- 验证：条目计数核对；`git status` 确认只新增预期文件。
- 文件：`.codebuddy/skills/cs-shader/references/{components.md,provenance.md}`

### T2 编写 SKILL.md 与 references 拆分（依赖：T1）
- 产出：SKILL.md（双语 description、Phases、约束、handoff、Verification 清单）；
  composing.md / recipes.md / vendor-workflows.md。
- 验收：主路径无强制厂商命令/账号；cs-skill-review 六轴无 Critical；
  description 明确限定 Web/WebGPU 触发范围；每个规则只在一处权威存在。
- 验证：`cs-skill-review` 走查；对照 cs-game-image-gen 结构核对章节齐全。
- 文件：`.codebuddy/skills/cs-shader/SKILL.md` + 3 个 references。

### T3 再生成适配并验证（依赖：T2）
- 产出：全平台适配含 cs-shader。
- 验收：`skills/`、`.agents/`、`.claude/`、`.gemini/`、`.codex/` 均出现 cs-shader；
  其余技能 diff 为零（或仅预期的元数据变化）；frontmatter 无 model 键。
- 验证：`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-adapters.ps1`
  → `scripts/test-adapters.ps1`；`git diff --stat` 核对影响面。
- 文件：生成产物（不手改）。

### T4 实机冒烟（可选，依赖：T2；可并行 T3）
- 产出：临时 Web 项目中按 SKILL.md 主路径完成一个 recipe（如 hero background）。
- 验收：npm `shaders` 安装成功、WebGPU 渲染可见、截图留证；临时项目用后清理。
- 验证：cs-browser-test 截图 + 控制台无错误。
- 风险：npm 第三方代码执行，需用户批准后运行。

## 文档影响

- README/Docs 若有技能清单或计数：同步 +1（实施时核对）。
- 顶层 skills/ 等为生成产物，随 T3 自动更新；不新建其他文档。

## 待用户决策

1. 命名：默认 `cs-shader`（description 限定 Web 范围）；备选 `cs-web-shader` 更防误解。
2. 可选分支取舍：默认保留 vendor-workflows.md（门控）；也可完全剔除，做纯离线组合技能。
3. T4 实机冒烟是否执行（涉及 npm 安装第三方包与浏览器验证）。
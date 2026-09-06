# SysDocs 体系约定（sysdocs-system）

本文件是 `cs-sysdocs-init` / `cs-sysdocs-update` / `cs-vibe-coding` 三个 skill 共同引用的**体系约定**。它定义目录结构、状态门闩、frontmatter 载体、歧义杜绝规则、符号反查顺序、文档预算、排除表、生命周期与统一 validator 协议。三个 skill 不得各自实现互不一致的版本。

---

## 1. 目录结构（生成于目标 project root）

```
SysDocs/
├── SYSTEM_ROOT.md             # 总文档（唯一入口）
├── modules/                   # 每个功能模块一个文档
│   ├── <module-id>.md
│   └── <module-id>/<page-id>.md      # 拆分页（可选）
├── .meta/                      # 运行报告、迁移诊断、恢复记录（不参与模块识别）
│   ├── reports/<run-id>.json
│   ├── migrations/
│   └── recovery/
└── VibeCoding/                # 碎片需求临时方案（cs-vibe-coding 产物）
    └── <YYYYMMDD-HHMM>-<slug>[ -N].md
```

硬约束：

- `project root` 是用户显式指定的 workspace 相对目录；缺省为当前 workspace 根。所有 `SysDocs/`、模块 `path`、`source_roots` 和符号引用都相对于该 root，禁止自动向上搜索父目录或向下选择子目录。
- 默认一个 monorepo 维护一套 `SysDocs/`；manifest 可登记多个 package/app 的 `source_roots`，并在 §7 目录树中记录 workspace 边界。
- 若勘察发现多个独立部署单元，先展示 root、部署单元和依赖范围，交互模式要求明确确认；用户选择拆分时，每个 root 各自维护自己的 `SysDocs/`，不得混用 manifest。
- symlink 默认不跟随；只有用户显式允许时才解析其目标，且解析后必须仍在 project root 内。
- spec-only 项目如果未指定 root，只在当前 workspace 根生成骨架，不猜测未来源码目录。
- `.meta/` 不属于模块、页面或用户文档正文；模块扫描、manifest 统计和边界偏差计算必须排除它。

---

## 2. 三态初始化清单（门闩）

**不要用「`SysDocs/` 目录是否存在」当 init 门闩。** 判定三态：

| 状态 | 判定 | 谁处理 |
|---|---|---|
| **未初始化** | `SysDocs/` 不存在、为空、只有 `VibeCoding/`，或尚无任何有效的 `SYSTEM_ROOT.md` / 模块文档 | `cs-sysdocs-init` |
| **部分初始化** | 已留下任一系统文档，但结构不完整或不一致：缺 `SYSTEM_ROOT.md`、缺 `modules/`、frontmatter 无法解析、模块清单与模块文档不一致、或 init 中途失败 | `cs-sysdocs-update` 的 **repair** |
| **已初始化** | `SYSTEM_ROOT.md`、`modules/`、模块清单与模块文档结构完整且一一对应；无代码项目允许模块清单与 `modules/` 均为空 | `cs-sysdocs-update` 增量 |

硬约束：

- `cs-vibe-coding` **禁止**在未初始化时创建 `SysDocs/`。未初始化 → 停下，请用户先跑 init。
- 部分初始化时允许 `cs-vibe-coding` 创建/写入 `SysDocs/VibeCoding/`，但不得创建或补写 `SYSTEM_ROOT.md`、`modules/` 或模块正文，不改变当前状态。
- 空目录 / 只有 `VibeCoding/` = 未初始化，init 可执行。
- `update` 遇到未初始化时不得回调或隐式执行 init，只报告状态并要求先运行 `cs-sysdocs-init`。
- **re-init / 边界重建留在 update 内**（`mode=rebuild-boundaries`），init 保持真·一次性。

### 2.1 机器可解析模块 manifest

`SYSTEM_ROOT.md` frontmatter 维护规范化 `modules` manifest；§3 的 Markdown 模块清单是由该 manifest 生成的给人阅读的视图，不作为状态判定的唯一输入。每个模块文档 frontmatter 必须包含相同的 `module_id`。

```yaml
modules:
  - id: order-service
    path: modules/order-service.md
    description: 负责订单创建、状态流转与持久化
    source_roots: [src/order]
    status: active
    pages: []
```

字段约束：

- `id`：全局唯一的小写短横线 slug，作为模块稳定身份；重命名必须通过显式迁移记录，不能仅改文件名。
- `path`：模块主文档相对于 project root 的路径，必须位于 `SysDocs/modules/` 下。
- `description`：必填、面向人阅读的一句话职责说明；允许 agent 更新，但不得用于模块匹配、数量统计或漂移判定。
- `source_roots`：模块负责的源码目录/包列表；用于影响范围定位和边界复审。
- `status`：沿用文档状态枚举；已归档模块必须从活动模块数量中排除，但仍保留 manifest 记录。
- `pages`：模块拆分页相对于 project root 的路径列表；子页必须显式登记，未登记的 `modules/<id>/` 文件视为结构异常并进入 repair。

状态判定按 `modules[].id`、`path`、`pages` 与磁盘文件逐项比对；Markdown 表格只允许展示 manifest 内容，不得手工维护另一份模块事实源。

---

## 3. frontmatter 载体

术语表、时间戳、置信度、待并入、KB 锁存，全部落在 frontmatter，不另建旁路文件。

```yaml
---
schema: 1
status: draft | active | stale | archived
generated_from: <git sha>      # 内容级漂移的对比基线；无 git 则省略并在正文注明
source_scope: committed | committed+working-tree | unversioned
updated: <ISO-8601>
confidence: high | low
kb: codegraph | understand-anything | graphify | none
owned_by: agent | mixed        # mixed = 含 human 保护区
kb_bootstrap: pending | done   # 仅 SYSTEM_ROOT.md；pending = 降级生成，KB 就绪后 rebuild 一次
---
```

所有文档必须声明 `doc_type`，用于避免仅凭路径猜测文档身份：

```yaml
doc_type: overview | module | page | vibe
```

字段约束：

- `overview` 必须包含 `modules` manifest 和 `kb_bootstrap`；
- `module` 必须包含 `module_id`，且与 overview manifest 的 `id` 精确一致；
- `page` 必须包含 `module_id`、模块内唯一的 `page_id`，并出现在对应模块的 `pages` 列表；
- `vibe` 必须包含稳定的 `vibe_id`、目标模块或 `awaiting-repair` 说明；
- `generated_from`、`source_scope`、`confidence`、`kb` 对源码生成类文档必填；纯 vibe 文档不强制要求 Git 基线。

`page` 不新增独立模板，复用模块模板的章节形状和自检清单，仅增加 `page_id` / `module_id` 及页面归属字段。

拆分页固定为：

```text
SysDocs/modules/<module-id>.md
SysDocs/modules/<module-id>/<page-id>.md
```

子页只能属于一个模块；页面移动或重命名必须先更新 manifest。未登记的页面进入 `repair`，不得静默删除。

### 3.1 schema 迁移协议

`cs-sysdocs-update` 先做 **schema gate**：文档 `schema` < 模板 `schema` → 先迁 frontmatter / 章节标题，再增量改写。

- `schema < 当前模板版本`：按注册的单向迁移步骤逐版本升级；在临时文件中完成 YAML、manifest、human 块和章节校验，成功后再原子替换。
- `schema == 当前模板版本`：正常处理。
- `schema > 当前模板版本`：只读失败，禁止降级、覆盖、删除未知字段或重建该文档；verdict 标 `FAILED`，等待 skill 升级。
- 迁移任一步失败时保留原文件不变，保存诊断信息；重复执行同一迁移不得产生额外 diff。
- 未知 frontmatter 字段默认原样保留；只有迁移规则明确标记废弃时才删除，并记录迁移说明。
- overview、module、vibe 三类专用模板分别声明当前 schema 版本和迁移注册表；page 复用 module 的 schema/迁移规则，不能只修改 frontmatter 中的数字。

---

## 4. 文档状态生命周期

状态转换必须遵循以下语义；skill 不得仅因流程结束就任意设置状态：

| 状态 | 语义 | 可进入条件 | 可离开条件 |
|---|---|---|---|
| `draft` | 生成中、初始化中断、自检未完成，或 vibe 尚未并入 | 新建文档、init 中途失败、vibe 生成 | 完整自检通过 → `active`；明确废弃 → `archived` |
| `active` | 结构完整、manifest 一致、引用校验通过，且内容已基于当前基线生成 | init/update/repair 成功并通过校验 | 检测到源码/符号漂移或 repair 未完成 → `stale`；明确废弃 → `archived` |
| `stale` | 内容可能过期、引用失效、KB 降级待复审、孤儿文档或 repair 未完成 | update 检出漂移；重建失败；多余/无法匹配模块 | 成功刷新并通过校验 → `active`；明确废弃 → `archived` |
| `archived` | 明确废弃或已被新文档替代的历史记录 | 用户确认或有迁移记录 | 仅用户明确恢复并重新校验后 → `draft`；不得静默恢复 |

约束：

- init 只有在所有必需文档和自检完成后才可将文档设为 `active`；中断保持 `draft`。
- update 发现漂移时先将受影响文档设为 `stale`，成功刷新、链接/符号/Mermaid 校验通过后才恢复 `active`。
- repair 不删除多余模块文档；无法匹配 manifest 的文件保留为 `stale` 并写入 orphan 报告，等待用户迁移或归档。
- vibe 合并成功后，目标模块按校验结果保持/恢复 `active`；vibe 原文件保留并设为 `archived`，写入目标模块和合并提交的来源链接。
- `archived` 文件仍参与历史链接解析和审计，但不计入活动模块数量，不作为当前模块边界输入。

### 4.1 人改保护区

人手写的段落用 HTML 注释包起来，agent **只改 agent 段**：

```html
<!-- human:start -->
…人写的约束 / 已知坑 / 业务背景…
<!-- human:end -->
```

存在任一 human 块时 `owned_by: mixed`。human 块只允许成对且不嵌套。

---

## 5. 命名规范

- 模块 `id` / slug：小写短横线（如 `order-service`），长度 1–80。
- vibe 文件名：`<YYYYMMDD-HHMM>-<slug>[ -N].md`；同一分钟两次调用追加 `-2`、`-3`。
- vibe slug 只允许 `[a-z0-9-]`，拒绝空值、`..`、路径分隔符、控制字符和 Windows 保留名。
- 模块文档路径固定 `SysDocs/modules/<module-id>.md`，拆分页 `SysDocs/modules/<module-id>/<page-id>.md`。

---

## 6. 8 条歧义杜绝规则 + 自检清单

读者定位（人 + AI agent 双读）→「人读摘要 + 机器读精确引用」双层结构。每条规则落地到每份文档末尾的自检清单：

1. **引用唯一可定位**：全限定名 + `路径:类名+函数名`，禁代词回指；引用符号须反查命中，查无此符号 = FAILED；匿名结构走豁免。
2. **术语唯一**：仅在 `SYSTEM_ROOT.md` §0 定义一次，模块文档只引用不重定义。
3. **数值具体**：阈值/超时/重试写具体值 + 单位。
4. **枚举穷举**：状态/模式/错误码列全部取值。
5. **强度分级**：MUST / MUST NOT / SHOULD / MAY。
6. **流程写清参与者**：发起者/输入输出/异常分支。
7. **条件写前提与违反行为**。
8. **自检清单逐项打勾**。

匿名结构豁免（规则 1 边界）：执行流程/引用落在匿名结构上（lambda / 闭包 / 回调 / 管道 / 中间件 / 事件 handler）时，退回「最近的具名符号 + 行内上下文描述 + 必要代码片段」。豁免边界写入规则 1 的自检清单。

---

## 7. 符号引用格式与反查顺序

统一组成是：`语言 + project-root 相对路径 + 全限定名 + 参数签名/导出名`；路径不得包含机器绝对路径。

| 语言 | 形式 | 例 |
|---|---|---|
| TypeScript / JavaScript | `语言\|路径:Class.method(参数签名)` 或 `语言\|路径:exportName` | `ts\|src/foo.ts:OrderService.place(string):Order` |
| Python | `语言\|路径:Module.Class.method(参数签名)` | `py\|pkg/mod.py:OrderService.place(str):Order` |
| C++ | `语言\|路径:ns::Type::method(参数签名)` | `cpp\|src/foo.cpp:svc::Order::place(string):Order` |
| C# | `语言\|路径:Namespace.Type.Method(参数签名)` | `cs\|src/Foo.cs:Svc.Order.Place(string):Order` |
| 其他 | 该语言惯用全限定名 + 路径 | 在 §0 术语表注明约定 |

### 7.1 符号反查顺序（`cs-code-query` 知识库 skill **不提供** `findReferences` / `workspaceSymbol` API；不得把它们当作知识库调用接口）

1. 宿主 LSP（若宿主提供 `workspaceSymbol` / `goToDefinition` 则使用）
2. CodeGraph `/understand-chat`：「符号 X 是否存在、定义在哪」
3. `Grep` 全限定名（兜底）

硬约束：

- 引用用符号，不用行号。
- **不做 MD5 指纹**（混淆「符号存活 / 内容一致」，双向失败，且是第二套会漂移的快照）。
- 一次 update **先抽符号清单再批量反查**，禁止对每个引用开一轮 query。有批量查询能力时每批最多 50 个符号。
- 反查结果必须唯一命中：**查无此符号 = 幽灵引用 → 进入修复；多于一个命中 = 歧义引用 → verdict `PARTIAL`，不得由 AI 静默任选一个**。
- 只有唯一候选且路径、语言和签名均一致时才允许自动修复；否则列出候选定义位置和需要用户确认的消歧信息。
- 无法覆盖全部引用时，保留未验证清单并将 verdict 标为 `PARTIAL`，不得伪造 `COMPLETE`。

### 7.2 两类漂移分开

- **符号级**（引用断）→ 符号反查（§7.1）。
- **内容级**（描述旧）→ `git diff --name-status -M <generated_from>..HEAD`（已提交范围）。**不用 mtime**（Windows 不可靠，未提交脏文件会误伤）。SHA 不存在、历史不可达或浅克隆无法取得基线时，不猜测受影响模块，要求重新建立基线或提供文件列表并将 verdict 标 `PARTIAL`。无 git 时必须提供用户指定的文件列表；未提供则只做结构校验、不改写内容，并标 `PARTIAL`。
- 更新成功后刷新 `generated_from` 为当前 `HEAD`；`source_scope` 记录本轮来源：默认 `committed`，显式纳入工作区变更时为 `committed+working-tree`，无 Git 时为 `unversioned`。

### 7.3 知识库能力矩阵

三个 skill 使用同一套后端状态语义；一次操作锁定所选后端，不得静默切换。

| 状态 | 行为 | `kb` / `confidence` | 禁止行为 |
|---|---|---|---|
| `READY` | 只调用该后端已声明支持的 query/update | 实际后端 / `high` | 不安装、bootstrap 或假设不存在的 API |
| `STALE` | 尝试既有查询，失败后降级到 Glob/Grep/Read | 实际后端 / `low` | 不自动安装 CLI |
| `UNINITIALIZED` / `MISSING` | 直接使用源码工具降级 | `none` / `low` | 不创建、不安装知识库 |

后端优先级为 CodeGraph > Understand-Anything > Graphify；用户显式指定
后端时优先，但不可用必须报告并降级。无完整符号覆盖时保留未验证清单并
返回 `PARTIAL`，不得伪造 `COMPLETE`。无 `Task` 时记录
`architect_review: unavailable`；vibe 不能因此进入模块文档。

---

## 8. 文档预算（类引用分级）

**类引用分级**：

| 级别 | 收谁 | 写什么 |
|---|---|---|
| **详写** | 公开 API、跨模块边界类型 | 全限定名、路径、职责、设计思路、公开接口、依赖/被依赖 |
| **一览表** | 模块内部实现类 | 名 + 路径 + 一句话职责 |

禁止「每个类都详写」。单模块文档硬顶：**约 400 行或详写类 ≤ 15 个**（先到为准）。超了拆 `modules/<slug>/` 子页，或标「内部实现详见源码」并给出目录路径。

**双层结构落模板**：每一节先 ≤5 行人读摘要，再跟符号表 / Mermaid。原则写在本文件，形状写在 overview / module 模板里，禁止只写原则不给形状。

---

## 9. 模块识别排除表

策略「目录/包为骨架」仍然成立，但下列路径**默认不是模块**：

- 依赖与构建产物：`node_modules/`、`vendor/`、`dist/`、`build/`、`.git/`
- 生成代码：`generated/`、`*.g.cs`、protobuf/openapi 生成目录（可在 SYSTEM_ROOT 覆盖）
- 宽前端桶：`src/components/`、`src/assets/`、`src/styles/` 不单独成模块，归入所属功能模块
- 纯测试 / 纯资源目录：`__tests__/`、`testdata/`、`fixtures/`、`*.png` 资源包
- 敏感数据来源：`.env`、`.env.*`、密钥/证书文件（`*.pem`、`*.key`、`*.p12`、`*.pfx`）、凭据目录、日志、dump 和带凭据的本地配置；默认不读取、不建模块、不写入文档

`src/components/` 这种宽目录由 AI + 知识库按**功能边界**拆/并，并在模块清单里写理由。不得把整个 `components/` 写成一个模块文档。

---

## 10. 敏感数据处理

init、update、repair、rebuild 和 vibe 对所有进入文档、manifest、architect brief、verdict、日志或临时诊断的数据执行统一脱敏：

- 默认排除 `.env*`、密钥/证书、凭据目录、日志和 dump；除非用户显式提供安全的脱敏文件列表，不读取其内容。
- 对配置、源码、知识库结果和调用参数扫描 API key、JWT、私钥、连接串、密码字段、云凭据及疑似个人数据，统一替换为 `[REDACTED:<类型>]`。
- 检测到疑似秘密时先阻断写盘并报告文件与字段位置；用户确认后也只能写脱敏结果，不能把原值传给 architect 或记录到日志。
- 环境变量只记录变量名和用途，禁止记录值；脱敏规则命中情况写入 verdict，便于审计。

---

## 11. 统一文档 validator 协议

三个 skill 及 `rebuild-boundaries` 共用同一套静态 validator 契约；不得各自实现互不一致的 checklist 解释。每次 init、repair、incremental、vibe 写入或边界重建提交前都必须运行 validator，并输出机器可读报告（文档路径、规则 ID、严重级别、行/字段定位、修复建议）。

validator 本身不得修改源码或绕过 skill 的路径 allowlist。validator 是三个 skill 共同引用的**文档校验协议**，不是随目标项目部署的 runtime。

### 11.1 规则 ID 表

| 规则 ID | 检查项 | 严重级别 |
|---|---|---|
| `SYSDOC-FM-01` | frontmatter YAML 语法可解析 | blocking |
| `SYSDOC-FM-02` | `schema` 版本 ≤ 模板当前版本（大于 = 只读失败） | blocking |
| `SYSDOC-FM-03` | `doc_type` 对应的必填字段齐全 | blocking |
| `SYSDOC-FM-04` | 字段类型正确（如 `modules` 为列表、`pages` 为列表） | blocking |
| `SYSDOC-MAN-01` | manifest 与磁盘模块文档双向一致（无缺、无多余） | blocking |
| `SYSDOC-MAN-02` | 模块文档 `module_id` 与 manifest `id` 精确一致 | blocking |
| `SYSDOC-MAN-03` | `page` 的 `page_id` 出现在对应模块 `pages` 列表 | blocking |
| `SYSDOC-LINK-01` | Markdown 内部链接存在 | blocking |
| `SYSDOC-LINK-02` | workspace 路径边界（不越出 project root） | blocking |
| `SYSDOC-LINK-03` | 归档链接可解析 | warning |
| `SYSDOC-MERMAID-01` | Mermaid 代码块类型为 `flowchart` / `sequenceDiagram` 等合法类型 | blocking |
| `SYSDOC-MERMAID-02` | Mermaid 语法可解析 | blocking |
| `SYSDOC-HUMAN-01` | `human:start/end` 成对 | blocking |
| `SYSDOC-HUMAN-02` | human 块不嵌套 | blocking |
| `SYSDOC-HUMAN-03` | 迁移后 human 块仍完整 | blocking |
| `SYSDOC-REF-01` | 符号引用格式符合 §7 | blocking |
| `SYSDOC-REF-02` | 无重复引用 | warning |
| `SYSDOC-REF-03` | 符号引用零命中（幽灵引用） | blocking |
| `SYSDOC-REF-04` | 符号引用多命中歧义 | blocking |
| `SYSDOC-SEC-01` | 敏感数据扫描（疑似秘密被阻断或脱敏） | blocking |
| `SYSDOC-SEC-02` | 脱敏标记存在（`[REDACTED:<类型>]`） | warning |

### 11.2 校验结果语义

- 所有 blocking 规则通过才允许文档进入 `active` 或执行原子替换。
- 可修复的非阻断问题（warning）可返回 `PARTIAL`。
- 任一 blocking 问题返回 `FAILED` 并保留旧文档。
- 每种 `doc_type` 的必填/允许字段、规则 ID、严重级别和报告格式必须固定，不能由各 skill 自行解释。

---

## 12. 运行报告 schema（.meta/reports）

每次操作至少记录 `run_id`、`operation`、规范化 `project_root`、`source_scope`、Git 基线、`status`、写入/跳过文件、规则问题和脱敏记录。报告中的源码内容、调用参数和秘密必须经过统一脱敏；报告 schema 与文档 schema 同步版本化。

```yaml
schema: 1
run_id: <unique-id>
operation: init | repair | incremental | rebuild-boundaries | vibe
project_root: <normalized path>
source_scope: committed | committed+working-tree | unversioned
baseline:
  git_head: <sha or null>
status: COMPLETE | PARTIAL | FAILED
written: []
skipped: []
issues:
  - rule_id: <id>
    severity: blocking | warning
    path: <project-root relative path>
    field: <optional>
    message: <redacted>
    suggestion: <redacted>
redactions: []
```

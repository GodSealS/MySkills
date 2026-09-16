# SysDocs schema 2 实施与验证

依据：`Idea/sysdocs-knowledge-driven-design-plan.md`（2026-09-16 Grill Review 已完成）。用户随后明确要求开始实施；按该范围执行，不重复请求规划批准。

## 依赖与边界

共享协议与模板 → 校验器及行为样例 → init/update/vibe 与查询路由 → 开发/审查接入 → 平台生成和回归。知识库接口核实可与共享契约并行，读取方统一依赖共享协议，不另建状态平台。

- `.codebuddy/` 是技能、协议、persona 和命令的维护源；生成副本仅通过现有适配器更新。
- 本仓库没有项目知识库或 SysDocs；不为本次修改创建它们。
- 原有 `test-sysdocs.ps1` 在实施前因 `tests/fixtures/sysdocs/initialized/SysDocs/SYSTEM_ROOT.md` 等样例缺失失败。
- 文档影响：共享协议、模板、工作流及 README/路由需要一起更新；设计决策沿用原方案 ADR-SD-01—05。

## 任务

| 任务 | Owner | 依赖 | 验收 | 验证 | 状态 |
|---|---|---|---|---|---|
| T1 共享布局/元数据/迁移契约与摘要模板 | arch | 无 | schema2字段、双布局三态、人工保护、摘要粒度明确 | 架构核对、样例与链接检查 | 完成 |
| T2 结构校验与摘要提取 | arch | T1 | 新旧布局可检查；局部范围/入链、文件覆盖、未知schema、限制报告 | Python真实临时项目行为测试，RED→GREEN | 完成 |
| T3 init/update/vibe | arch | T1 | 按影响更新；显式可恢复迁移；无库降级；无SysDocs可前置方案 | 契约核对、测试样例 | 完成 |
| T4 知识库真实接口 | arch | 无 | 后端来源准确、分别报告可用性/覆盖/新鲜度、不强制创建 | 本机工具源码核查、路由检查 | 完成 |
| T5 设计与开发接入 | arch | T1/T3/T4 | 普通/团队流程不强制无关全库修复；只读审查边界不变 | 全部来源引用检索、集成回归 | 完成 |
| T6 适配器与交付 | arch | T2/T3/T4/T5 | 生成各平台、测试通过、行为与语义核实能力清楚区分 | SysDocs/adapter测试、完整Python回归、diff检查 | 完成 |

## 验证记录

### 已完成检查

- `python -B -m unittest discover -s tests -p test_validate_sysdocs.py`：39项真实临时项目行为测试通过。新行为先在旧实现失败，再逐项修复；覆盖schema1/2、三态、摘要提取/脱敏、局部入链、源码覆盖、路径别名、未知版本只读和畸形输入。
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-sysdocs.ps1` 与 Git Bash 下 `sh scripts/test-sysdocs.sh`：资源校验及39项行为测试通过。
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build-adapters.ps1`：5套技能/引用产物及各平台命令、persona已生成。
- PowerShell及Git Bash的 `test-adapters`：通过，包含新file/flow模板、模型/私有资源边界和Markdown链接保全。
- 完整 `python -B -m unittest discover -s tests`：77项通过；适配器链接修复后的最终全套回归再次77项通过（313.362秒）。
- 8个主要变更技能的正文及Unicode description与5套生成产物一致；26条真实源码文档链接有效（模板中的目标项目示例链接不按技能包路径解释）。
- `git diff --check`通过；独立复核确认两项集成矛盾和适配器链接修复均无剩余必修问题。以工作区差异交付，未提交、未执行全局安装或迁移业务项目。

### 审查修复

独立审查发现并复验关闭R1—R10：旧登记页越界、畸形数据崩溃、局部新增源码漏检、历史Vibe兼容、摘要疑似秘密回显、doc_type绕过、路径别名重复归属、导航/状态误报、ISO时间兼容、无关入链阻断。额外异常输入回归也已通过。Windows没有创建符号链接的权限，越界读取项使用受控真实路径解析模拟及代码检查，读取次数为零；不冒称真实OS链接实测。

跨平台核对发现旧生成器路径正则会吞Markdown链接标签；新增行为断言先失败，再修复两个生成器。另统一spec/ADR命令、模板、persona中的权威位置及schema2字段，避免新旧规则冲突。

### 本轮复审 F1—F7 修复（2026-09-16）

在既有未提交实施上修复，不回滚先前工作；共享协议仍由 `.codebuddy/` 维护，再生成各平台副本。

| 发现 | 修复与回归证据 |
|---|---|
| F1 缺 README 的全量检查误报 COMPLETE | 从已有 architecture/files 事实页识别新布局，缺失入口仍产生阻断问题 |
| F2 跳转页绕过必需元数据与源码覆盖 | 跳转豁免限定旧 SYSTEM_ROOT/modules；三个新布局必需页均有替换跳转的失败用例 |
| F3 旧库拒绝新 schema 2 方案 | specs/decisions/VibeCoding 按各自页面协议验证；旧事实页不隐式升级，未知版本继续拒绝 |
| F4 局部检查遗漏配套模块索引 | 检查指定模块/索引对应页；双向遗漏都阻断，合法成对删除及无关旧缺陷保留回归 |
| F5 cs-build 协议路径错误 | 改为命令层级的 ../references；两套 adapter 测试验证源及四类生成命令的实际引用目标 |
| F6 无关读取错误阻断局部交付 | 指定页、直接引用及必要配套/范围依赖读取失败仍阻断；其余列入 out_of_scope_issues 并声明入链未覆盖 |
| F7 历史 ADR frontmatter 被误判版本 | 未声明 schema/doc_type 的历史规范/ADR 保留原格式；链接检查及显式未知版本 gate 仍有效 |

- 先补复现测试并确认 RED，再修复；SysDocs 测试从 39 项增至 52 项（含参数化边界场景），全部通过。
- PowerShell/Git Bash 的 `test-sysdocs` 均通过；两套 `test-adapters` 均通过；主工作区平台产物已重新生成并核对协议副本与命令引用。
- 完整 `python -B -m unittest discover -s tests`：90 项通过（198.388 秒）；`git diff --check` 通过。
- 独立结构契约核对未发现本轮修复引入的明确缺陷；该核对未替代上述运行结果，也不证明自然语言语义完整性。
- 本轮不执行真实业务项目迁移或知识库刷新；原有语义验证限制继续适用。

### 知识库依据与验证边界

仅只读核查工具源码及help：CodeGraph `6483ceb` 的 query/explore/impact/sync；Graphify `72cf62c` 的 query --graph、update代码范围和extract增量；Understand `04d90c9` 的自有图谱查询及增量流程。Graphify本机skill/package版本不同，因此路由以实际安装能力为准。未创建、刷新项目索引，不宣称完成真实图谱覆盖实验。

静态工具不承担语义推理。摘要正文一致、影响并集完整性、高风险扩大阅读、规范符合性及迁移人工意图保全属于agent协议与内容核实；未以格式测试冒称这些已在真实业务项目端到端验证。迁移交付的是可恢复工作流协议，validator本身只读、不自动执行迁移。原方案要求的维护耗时、Token和遗漏率真实任务对照尚待目标项目执行；完整Mermaid/符号解析、Markdown引用式链接/锚点和工作区证据内容核实仍如实列为工具未覆盖项。

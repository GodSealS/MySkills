# 文件索引模板（sysdocs-files-template）

依据 [共享协议](sysdocs-system.md) 生成 files/README 与模块索引。每个文件只有一个详细职责归属，其他页面通过链接引用，不另建代码—文档映射表。

## files/README.md

```yaml
---
schema: 2
doc_type: files
updated: <ISO 日期>
source_scope: committed
generated_from: <可验证提交 SHA>
source_paths: [<整体源码目录或文件>]
exclusions: [<相对排除路径或 glob>]
---
```

```markdown
# 源码导航

## 检索摘要

- `<实际主要模块/入口>`：<一句话源码职责>。
- 范围边界：<覆盖的业务源码、共享文件归属及明确排除项>。

## 覆盖与排除

<整体范围以本页 source_paths 为准；每项 exclusions 说明理由。依赖/构建/生成/敏感文件默认排除，不能按 components 名称排除业务源码。>

## 模块阅读入口

| 文件索引 | 模块职责及起读位置 |
|---|---|
| <指向 <module-id>.md 的链接> | <一句话职责> |

## 配置、测试和资源

<按阅读价值单列或按目录说明；业务源码仍逐文件覆盖。>

## 来源与覆盖限制

<明确工作区、未验证范围或无源码现状。>
```

## files/<module-id>.md

元数据同上，加 module_id；source_paths 为该模块来源范围，exclusions 统一在 files/README 维护。committed+working-tree 须加 evidence；unversioned 省略 generated_from 并说明限制。source_paths 只接受文件/目录，不接受 glob。

```markdown
# <模块名>文件索引

## 检索摘要

- `<关键类/结构/入口>`：<一句话主要职责>。
- 边界：<模块源码范围与跨模块协作/数据归属>。

## 文件职责

| 源码路径 | 职责 | 模块 |
|---|---|---|
| `src/order/service.ts` | 创建订单并协调库存预留 | `order` |

## 阅读建议

<先读入口再读协作实现；共享文件仅链接其唯一归属索引；回链对应 architecture/modules/<id>.md。>
```

表头与列序固定，路径为项目根相对实际文件，模块列等于本页 module_id；表内示例 order 必须替换为实际值。声明范围内业务文件应全覆盖且无重复归属。没有代码用 source_paths: []，不创建虚构模块表。验证路径、覆盖、排除依据、唯一归属与导航；职责和摘要另以源码核实。

# OpenGameAgent 研读报告（Phase 3 交付物）

> 日期：2026-08-17　|　来源：`f:\LarianModLearn\vendor\OpenGameAgent\`（shallow clone，2026-08-17）
> 版本：**0.3.0-alpha.2**（Apache-2.0）| 要求 .NET SDK 8.0（本机只有 9.0.317，global.json 锁 8.0.400/latestFeature，构建前需装 .NET 8 SDK 或调整 global.json——见"构建验证"）
> 已读：README / README.zh-CN / docs/{architecture, game-integration-patterns, engine-integration, getting-started, deployment-and-security, memory} / examples/OpenGameAgent.Example/Program.cs；源码结构扫描（27 个 src 项目 + 完整测试套件）。

---

## 1. 项目定位

紧凑可修改的 C# Agent Runtime，让游戏角色**观察结构化状态 → 计划 → 调用工具 → 检查权威结果 → 记忆 → 持续完成目标**。关键立场：**模型输出只是提案，每次状态变更由游戏代码裁决**（"game code remains authoritative over every state change"）。不绑定模型/玩法/世界数据模型，不提供人物卡/战斗/世界格式。

- 仓库结构：`src/` 27 项目（Kernel、Models、Memory、Persistence、Providers.*、Server、Client、Extensions、Attachments、Media、Connectors.Mcp、Plugins…）、`docs/` 13 篇、`engines/`（godot、unity）、`examples/OpenGameAgent.Example`、`tests/`（含 PublicApiSurface 测试）
- 中文 README 完整可用（README.zh-CN.md）

## 2. 架构（两层 + 扩展）

```
GameInput(有界 JSON + GameMoment) ──► GameAgentRuntime（游戏坐标层）
  上下文提供者 | Skills | 路由 | 会话/角色 | 队列 | 扩展
        └─► 小型有状态 Agent 内核（模型/工具循环，与游戏无关）
                └─► 可恢复动作派发器 ──► 游戏校验与权威状态
```

- **Kernel**：单一有状态模型/工具循环（8 步：校验消息→组装请求→流式事件→校验工具→执行（冲突键串行）→按源顺序回填结果→steering→直到停止/上限）。不感知 NPC/世界/引擎。`Agent` + `AgentLoop`。
- **Game runtime**：游戏坐标 = `session`、`actor`、`timeline`、`tick`；三路由（QuickResponse / Agent / Workflow）；乐观会话持久化 + 输入去重；同 actor 串行、跨 actor 有界并发；动作/工作流/记忆/调度/邮箱原语。上下文是**不透明 JSON**——不强制世界 schema（对 Larian 异构结构友好）。
- **权威边界**：模型工具调用 → JSON Schema 校验 → 意图记入 journal → 游戏规则/版本校验 → 游戏状态事务 → 回执存储 → 回执返回模型。重放已关闭的操作返回存储回执；参数变化/前置失效则 fail closed。`Uncertain` 状态永不自动重复写。
- **时间**：`GameMoment(timelineId, tick, calendarJson)`——不是墙钟；tick 含义由游戏定义（回合/天/小时/战斗帧均可）。跨时间线不可排序。
- **并发**：每 (session, actor) 一条逻辑通道；`MaxConcurrentActors` 上限；`GameTimeScheduler`/`GameSignal`/`IGameMailbox` 做准入（"大世界不该每帧唤醒每个 NPC，让确定性模拟决定谁需要推理"）。`GameTimeScheduler.CaptureState()` 支持读档不重放。
- **记忆**：`IGameMemoryStore`（scope/kind/tag/importance/owner/游戏时间截断/过期），游戏决定哪些记忆进上下文；可选 `OpenGameAgent.Memory`（模型无关 embedding 契约 + 可重建向量索引 + 词法/向量混合召回 + 游戏时间重排）。**权威存档在 FileGameMemoryStore，向量索引是派生数据**。embedding 失败回退词法召回。
- **路由**：显式 metadata > 类型路由 > 可选分类器 > 兜底（有工具/待办→Agent，否则 QuickResponse）。
- **Skills**：纯指令包（SKILL.md / skill.json），不安装代码、不授权。
- **故障模型**：provider 错误成为终结结果；工具超时必回界；订阅者故障隔离；会话版本冲突显式结果；本地存储写临时文件替换；HTTP 服务 JSON-only、8MB 请求上限。

## 3. 部署形态（三种）

| 形态 | 说明 | 对本项目的适用性 |
|---|---|---|
| 引擎内（local runtime） | netstandard2.1 嵌入游戏进程 | ❌ Larian 引擎是 C++ 非托管，不可嵌入 .NET |
| 游戏服务端内 | 游戏本身是 C# 权威服务端 | ❌ 非此场景 |
| **独立 Agent 服务** | `OpenGameAgent.Server`（.NET 8 HTTP/SSE），客户端发 `GameInput` JSON | ✅ **本项目采用**——Larian 游戏进程外跑服务，SE Lua 作客户端 |

### OpenGameAgent.Server 端点（已确认）
- `GET /healthz`、`GET /v1/capabilities`
- `POST /v1/run`、`POST /v1/run/stream`（SSE 流式）
- `POST /v1/control/steer`、`POST /v1/control/abort`（对活跃 (session,actor) 循环 steering/中止）
- `POST /v1/usage`（持久 usage/成本账本）
- `POST /v1/attachments/read`（图片观察授权读取）
- **`POST /v1/actions/claim` / `stream` / `receipt` / `reconcile`** ← 游戏侧拉取动作 + 回报回执
- 认证：`ServerApiKey` → Bearer；可选 owner authorizer；本地客户端可用顶层 `credential` 字段（绑定主机注册的 PresentingCredentialAuthenticator）
- 模型路由：`ModelRoutes`（如 local Ollama 优先、cloud 兜底），游戏请求不能注入端点/密钥

### Remote game actions（非 C# 权威进程的官方模式——本项目的接入骨架）
```text
Agent 服务（DurableGameActionDispatcher + FileGameActionJournal）
  ──claim──►  游戏侧（外部主机）：校验 operationId / generationId / 规则
  ◄──receipt── 游戏执行并回报：{operationId, status:committed|rejected, result, timelineId, tick, generationId, expectedRevision, stateRevision}
```
- 先 Prepared 再 Dispatched 持久化；重复 claim 返回同一 durable operation；进程重启后 Dispatched 未回执的走 reconcile，绝不盲目重放。
- `generationId` 随存档/世界代次变化，防止旧回执跨档复用。

## 4. 最小集成示例（官方 example 骨架）

`GameAgentRuntime(GameAgentRuntimeOptions(provider, model){ Instructions, ContextProvider, ToolProvider, SessionStore, Limits{MaxConcurrentActors=16, MaxQueuedInputsPerActor=32} })` → `runtime.RunAsync(GameInput(sessionId, actorId, type, payloadJson, moment, inputId))`。
- 工具：`GameActionTool.Create(input, name, desc, jsonSchema, dispatcher, conflictKey, expectedRevision)`；`IGameActionHandler.ExecuteAsync`（重校验+幂等+回执）+ `RecoverAsync`（对账）。
- 上下文：`IGameContextProvider.GetContextAsync(input)` → `GameContextSlice(name, json, priority)` 列表。
- 读档安全：`generationId` + 新 timeline/session 命名空间；"绝不用墙钟判断游戏内记忆先后"。

## 5. 构建验证（本机状态）

- ⚠️ `global.json` 锁 SDK `8.0.400 / latestFeature / no prerelease`；本机 `dotnet --version` = 9.0.317 → **直接构建会失败**。需：安装 .NET 8 SDK（官方下载），或临时改 global.json（不推荐入库）。
- 示例运行需 `OGA_MODEL_ENDPOINT / OGA_MODEL / OGA_API_KEY` 环境变量 + OpenAI-compatible 端点（Ollama 亦可）。
- 测试套件齐全（Memory.Tests 等可按文档 `dotnet test` 单项目跑）。

## 6. 结论（对 Larian 项目）

1. OpenGameAgent 是**引擎无关**运行时，Larian 场景走"独立 Agent 服务 + Remote game actions"官方模式，不碰 Godot/Unity 适配器。
2. 其权威边界设计（游戏校验一切、durable receipts、Uncertain 不重写）与 Larian"Osiris 引擎权威"哲学天然一致。
3. 主要待办：安装 .NET 8 SDK；跑通 Server + claim/receipt 链路（可在无游戏环境下用假 world 验证）
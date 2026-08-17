# 接入方案设计（Phase 4 交付物）
## ——OpenGameAgent × Larian 引擎（BG3 / DOS2）桥接架构

> 日期：2026-08-17　|　依据：前三份报告 + 框架研读。**本方案是设计，不含实现代码**（按计划，M5 评审通过前不写功能）。
> 核心约束回顾：Larian 引擎非托管（不可嵌入 .NET）→ 独立 Agent 服务；两游戏 SE 均无出站 HTTP → 需桥接进程/原生 DLL。

---

## 1. 总体架构

```text
┌───────────────────────── 游戏进程（bg3.exe / EoCApp.exe）─────────────────────────┐
│  Larian 引擎                                                              │
│    ├─ Osiris（规则引擎：事件/DB/flag）                                        │
│    └─ anubis（BG3 行为树）/ Archetype（DOS2 战术 AI）＝ 原生行为兜底层           │
│  Script Extender（注入 DLL）                                                 │
│    ├─ 事件钩子：Ext.(Osiris.)RegisterListener("DialogStarted"|…)            │
│    │            + Tick(BG3) / TimerFinished 心跳(DOS2)                       │
│    ├─ 动作执行：Osi.*（对话/好感/状态/物品/flag…）+ Ext.IO(BG3)               │
│    └─ 桥接客户端：向 Agent 服务收发 JSON（经下方某通道）                        │
└───────────────┬─────────────────────────────────────────────────────────────┘
                │  桥接通道（三选一，见 §3）
                ▼
┌────────────────────────────── 本地进程 ─────────────────────────────────────┐
│  OpenGameAgent.Server（.NET 8，独立服务，localhost）                          │
│    ├─ /v1/run(stream)   ← 游戏事件 → GameInput{session,actor,type,payload,   │
│    │                        moment(timeline,tick,calendar),inputId}          │
│    ├─ agent kernel：模型/工具循环（QuickResponse/Agent/Workflow 三路由）       │
│    ├─ /v1/actions/claim|receipt ← LLM 动作意图 → 游戏执行 → 权威回执          │
│    ├─ 记忆：FileGameMemoryStore（权威）+ 可选向量索引（BGE-M3 local）          │
│    └─ 模型：Ollama（本地，低延迟）优先 / Anthropic 等云端兜底（ModelRoutes）    │
└───────────────────────────────────────────────────────────────────────────────┘
```

**会话身份映射（关键设计）**：
| OGA 概念 | 取值 |
|---|---|
| `sessionId` | 存档标识（BG3: 存档名/槽位；DOS2: 存档槽）——换档即新 session |
| `actorId` | NPC 实例 GUID（两游戏统一主键，见 integration-points §2.1） |
| `timelineId` | 世界/流程时间线（如 "main"）；分支存档用新 timeline |
| `tick` | BG3：自建节拍（游戏小时/长休）；DOS2：游戏小时 |
| `calendarJson` | BG3：`{"day":n,"hour":h}`（自建）；DOS2：`DB_Time` 直供 |
| `generationId` | 读档代次（SE 读档事件时递增）——防旧回执跨档复用 |
| `inputId` | 事件实例唯一 ID（防重放/去重） |

## 2. 游戏侧组件（SE Lua 模组，三模块）

### 2.1 事件桥（观察入口）
- 订阅（两游戏通用清单，见 integration-points §3.2）：`DialogStarted/Ended`、`EnteredTrigger`（感知）、`EnteredCombat/AttackedBy/Died`（危机）、`TimerFinished`（心跳）。
- **过滤聚合**：事件 → SE Lua 侧去抖/限频（如 NPC 每 2s 最多唤醒一次、同事件 5s 内去重）→ 组装有界 JSON 快照（NPC 自身状态+周边 3-5 个实体+好感+时间+当前 flag）→ 发 agent 服务。
- **唤醒策略**（框架官方建议）：确定性条件（距离/重要度/行为状态）决定谁被唤醒；低优先 NPC 用 `GameTimeScheduler` 周期触发（DOS2 直接挂 `NewHour`）。
- 读档：`SavegameLoaded`（BG3 anubis/SE）/`SessionLoaded`（DOS2）→ 通知服务新 generationId + 恢复记忆。

### 2.2 动作执行器（执行出口）
- 从 agent 服务 `claim` 动作意图（`/v1/actions/claim`，带 operationId/generationId/expectedRevision）→ **白名单校验**（工具名+参数范围，危险动作如 Die/TeleportTo/SetFaction 需额外条件）→ 调 `Osi.*`（对话走 `Proc_StartDialog`/`QRY_StartDialog` 族；BG3 待实测 `StartDialog_Internal`）→ 回报 `receipt{status, result, stateRevision}`。
- 引擎权威：动作结果以游戏实际执行为准；被拒（如说话人不可用）回报 rejected，agent 不盲目重试。
- 兜底：LLM 未响应/失败时，BG3 anubis / DOS2 原生 AI 继续接管 NPC 表现（不呆站）。

### 2.3 记忆写回
- 事实（初遇/任务进度）→ 游戏原生（`DB_HasMet`/flag/`SetVarFixedString`——两游戏均有官方惯例）；
- 叙事（对话摘要/LLM 生成）→ agent 服务侧 FileGameMemoryStore（框架层，随 session 存）；
- BG3 附加：`Ext.IO.SaveFile` 可写游戏目录 JSON（不随档，明确标注）。

## 3. 桥接通道（最大技术风险，三方案）

| 方案 | 原理 | 优点 | 缺点 | 优先级 |
|---|---|---|---|---|
| **A. 原生 DLL 桥**（BG3 首选） | BG3SE 原生模组加载器加载 C#/C++ DLL；DLL 内嵌 HTTP 客户端向 localhost 服务发请求，并向 Lua 暴露 `Bridge.Post/Get` 函数 | 实时双向、延迟低、Lua 侧零轮询 | 需写原生代码；SE 版本绑定；DOS2SE 原生模组支持需确认 | BG3 第一验证项 |
| **B. 文件轮询桥**（零注入兜底） | SE Lua 写请求 JSON 文件 → 外部 watcher 进程轮询目录 → 转发 HTTP → 响应写回文件 → SE 读回 | 无需原生代码、跨 SE 版本稳定；**两游戏均可行**（BG3 `Ext.IO.SaveFile` ✅；DOS2 v60+ `Ext.IO.SaveFile` ✅ 写 `Osiris Data`，★二轮修正） | 延迟（百 ms 级）、目录协调复杂 | **DOS2 首选；BG3 备选** |
| **C. Lua 标准库直连** | DOS2SE Lua 若开放 `os/io/socket` 标准库（未文档化）→ 直接 `io.popen`/socket 发 HTTP | 最简单 | 可用性未知；★已非必需（B 方案确认可行） | DOS2 备选 |

**决策树（★二轮修正后简化）**：DOS2 直接采用方案 B（Ext.IO 文件桥，v60+ 已确认，实测实时性）；BG3 先测方案 A（原生 DLL）再退回 B；最终通道对两游戏统一封装成 Lua 侧 `LLMBridge` 模块，上层三模块不感知通道差异。

## 4. 架构原则（对齐框架与游戏哲学）

1. **引擎权威**：LLM 输出=提案；所有状态变更经游戏校验（框架 durable action 流程 + SE 执行层双重校验）。
2. **解耦 OGA API 变动**：0.3.0-alpha，API 会变 → 桥接层定义自己的**稳定 JSON 契约**（事件输入/动作输出格式），OGA 侧适配器隔离升级。
3. **上下文有界**：快照限制在几十 KB；大型数据（对话全文）走 artifact/按需读取。
4. **成本控制**：唤醒节流 + 本地模型优先（Ollama）+ 三路由（闲聊 QuickResponse 一次完成、复杂交互 Agent 循环、日程 Workflow 确定性）。
5. **存档安全**：session=存档；读档事件 → 新 generationId + 记忆恢复 + 未完成动作 reconcile（绝不盲目重放）。

## 5. 两游戏差异处理

| 维度 | BG3 | DOS2 |
|---|---|---|
| 时钟 | 自建（GameTime 采样+昼夜 flag+长休）| `NewHour`+`DB_Time` 现成 |
| 心跳 | `Ext.Events.Tick` | `Ext.Events.Tick`（★二轮修正：存在，server+client）+ 低频 TimerFinished 心跳备选 |
| 对话启动 | `StartDialog_Internal` 待实测；备选复刻 QRY 前置 | `Proc_StartDialog` 完整校验链 ✅ |
| 文件持久化 | `Ext.IO.SaveFile` ✅ | `Ext.IO.SaveFile`（v60+ ✅，★修正）+ PersistentVars（随档）|
| 浮字 | 无现成 API 🟡 | `Osi.DisplayText` ✅（★修正，裸字符串待实测）|
| 原生行为兜底 | anubis 行为树（40 事件）| Archetype 战术层 + charScript |
| 推荐首发 NPC | 任意（对话型 NPC 通用）| 同左；日程型 NPC 更易（时间系统现成）|

## 6. 实施路线（M5 评审后的建议顺序）

```text
S1 环境：安装 .NET 8 SDK；构建 OGA；跑通 Server + claim/receipt（假 world 无游戏验证）
S2 桥接验证（选型）：DOS2 先实测 Ext.IO 文件桥（方案 B，v60+ 确认存在——延迟/轮询频率/写回原子性）；BG3 测原生 DLL（方案 A）或 Ext.IO 文件桥
S3 最小闭环（DOS2 优先）：1 个 NPC × 1 个事件（搭话）→ 快照 → LLM 回复 → 对话启动 → 回执
S4 记忆 + 时间：DB_Time/NewHour 接 GameMoment；PersistentVars 记忆恢复；读档流程
S5 BG3 移植：时钟自建、StartDialog 实测、Ext.IO 持久化
S6 规模化：多 NPC 唤醒节流、目标/日程 Workflow、成本监控
```

> 每个 S 都是独立可验收里程碑；S3 前不引入任何游戏内 LLM 调用。

## 7. 开放问题（需运行时验证，见 game-analysis 两报告的"待验证"节）

1. BG3 `Osi.StartDialog_Internal` 前置条件与真实调用方式
2. DOS2 `Ext.IO` 文件桥实时性（写请求→外部进程→读回响应的延迟、轮询频率、并发写原子性）——S2 第一验证项
3. DOS2 `Osi.DisplayText(char, text)` 裸字符串显示效果（香草传本地化 key）
4. 动态对话文本注入（LLM 台词进对话 UI）的两游戏可行性（DOS2 `DialogSetVariableInt` 存在，String 类待验证）
5. DB 大记忆表对存档性能影响

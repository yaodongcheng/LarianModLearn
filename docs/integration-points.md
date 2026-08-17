# 接入点清单（Phase 2 交付物）
## ——LLM NPC 模组在 BG3 / DOS2 中的挂载位置

> 日期：2026-08-17　|　依据：`docs/game-analysis-BG3.md`、`docs/game-analysis-DOS2.md`（全部结论有文件路径证据）
> 每个接入点标注：位置、读/写、示例调用、验证状态。⚠️ = 需运行时实测；✅ = 文档/反编译已确认。

---

## 1. 三类接入位置总览

| 类别 | BG3 | DOS2 DE |
|---|---|---|
| **NPC 系统** | 实例 GUID 主键（stats/对话/规则/anubis 四系统统一）；对话树 .lsj + Timeline 播放器；anubis 行为树（原生 AI 层） | 实例 CHARACTERGUID + S_ 模板 ID；对话 .lsj（436 个系统对话 + 关卡内角色对话）；Archetype 战术 AI 与剧情层分离 |
| **事件系统** | 1452 个 Osiris goal 反编译（TOP-100 事件表）；anubis 40 种事件订阅；SE `Ext.Osiris.RegisterListener` + `Ext.Events.Tick` | 68 个 goal（648 IF 事件函数表）；SE `Ext.RegisterOsirisListener`；**无帧回调**（TimerFinished 心跳替代） |
| **动作执行** | `Osi.*` 全符号调用（TOP-100 动作表）；anubis `m.action.*`；对话启动 `QRY_StartDialog` 族；`StartDialog_Internal`⚠️ | `Osi.*` 全符号调用（1292 动作表）；`Proc_StartDialog` 完整校验链；`StartVoiceBark`；`StartDialog_Internal`⚠️ |

---

## 2. NPC 系统接入位置

### 2.1 身份与主键（两游戏一致）
- **BG3**：角色实例 GUID（如 `S_Player_ShadowHeart_3ed74f06-...`）贯穿 stats 条目 / 对话 speakerlist / Osiris 常量 / anubis 实体 ✅。SE 侧 GUIDSTRING 参数接受 UUID 或 64 位句柄 ✅。
- **DOS2**：CHARACTERGUID + `S_<区域>_<角色>_<uuid>` 模板 ID；`DB_IsPlayer(char)` 是"玩家队伍"权威标记 ✅。
- **LLM 记忆主键**：直接用 UUID 字符串。✅

### 2.2 对话系统（NPC 交互的载体）
| 项 | BG3 | DOS2 |
|---|---|---|
| 对话资源 | `Mods\Gustav\Story\Dialogs\**`（.lsj JSON，按 NPC/话题命名）+ Timeline 播放器（`Public\Gustav\Timeline\`）| `Mods\Shared\Story\Dialogs\**`（.lsj）+ 关卡内 S_ 角色对话 |
| 对话启动 | `QRY_StartDialog(dialog, speaker, player,...)`（osid 内用户查询）✅；SE 侧 `Osi.StartDialog_Internal(...)` ⚠️ 未文档化 | `Osi.Proc_StartDialog(0\|1, dialogName, npc, player...)` 完整校验链（未死/未战斗/10m）✅；`Osi.StartDialog_Internal` ⚠️ |
| 对话控制 | `DialogRequestStop`、`SetHasDialog(char,0/1)`、`DialogAddActor` ✅ | `DialogRequestStop(instance)`、`ProcForceStopDialog`、`DialogSetVariableInt(instance, var, value)` ✅ |
| 说话/表态 | 无 `Osi.Say` ⚠️；`StartVoiceBark`（语音）✅；`TextEvent` ✅；**浮字需 Ext.UI 叠加或 DebugText**⚠️ | 无 Say/浮动文本 ⚠️；`StartVoiceBark(char, bark)` ✅；台词走对话系统 |
| 动态文本注入 | 对话变量 API（`DialogSetVariable*`）存在但注入 LLM 文本未验证 ⚠️ | 对话变量系统（DialogVariables.lsx）+ 注入路径待验证 ⚠️ |

### 2.3 NPC 原生行为层（LLM 的兜底）
- **BG3 anubis**：`.anc` 配置（每 NPC 指定行为根）+ `.ann` 状态树（事件订阅 40 种 + `StartTimer(me,"name",0.5,-1)` 周期回调 + `Sleep(秒)` 协程）✅。`DEV_EnableAnubis(char, config)` 运行时换行为 ⚠️ 副作用待实测。
- **DOS2**：战术 AI（Archetypes 打分表）与剧情层（Osiris）分离 ✅；charScript 事件脚本（`OnCrimeSensibleAction` 等）。
- **LLM 方案**：LLM 作为"高层意图决策"，游戏原生层（anubis/Osiris）负责低层执行与兜底——与 OpenGameAgent"模型输出是提案、游戏代码是权威"完全一致。

---

## 3. 事件系统接入位置（LLM 唤醒触发器）

### 3.1 SE 钩子（模组的主事件通道）
| 能力 | BG3 | DOS2 |
|---|---|---|
| Osiris 事件钩子 | `Ext.Osiris.RegisterListener("DialogStarted", 2, "after", fn)` ✅ | `Ext.Osiris.RegisterListener("DialogStarted", 2, "after", fn)` ✅（`Ext.RegisterOsirisListener` 为 v56+ 弃用别名，均可） |
| 帧/心跳 | `Ext.Events.Tick:Subscribe`（~30Hz，`e.Time.Time` 毫秒）✅ | **`Ext.Events.Tick:Subscribe` 存在 ✅（★二轮源码修正，e.Time 为 GameTime）**；低频轮询另可用 `TimerLaunch`+`TimerFinished` 心跳 |
| 实体变更监听 | `Ext.Entity.OnChange("EsvCharacter", fn)` ✅ | `Ext.GetCharacter` / `Ext.Entity.GetCharacter(handle)`（v56+ 标准名）✅ |

### 3.2 候选触发器清单（两游戏，按 LLM 场景分组）
| 场景 | BG3 事件 | DOS2 事件 |
|---|---|---|
| 被搭话/对话 | `DialogStarted`/`DialogEnded`(572/2176) | `DialogStarted`/`DialogEnded`(17/72) + `CharacterMoveToAndTalkRequestDialog` |
| 感知玩家 | `EnteredTrigger`(1023)/`LeftTrigger`(516) | `CharacterEnteredTrigger`/`CharacterLeftTrigger`(23/11)、`CharacterSawCharacter`→`DB_Sees` |
| 战斗 | `EnteredCombat`(440)/`LeftCombat`/`CombatEnded`/`TurnStarted`(308)/`AttackedBy`(343) | `ObjectEnteredCombat`/`ObjectLeftCombat`/`ObjectTurnStarted`/`AttackedByObject` |
| 生死 | `Died`(199)/`Dying`/`KilledBy`/`Resurrected`/`HitpointsChanged` | `CharacterDied`/`CharacterDying`/`CharacterKilledBy`/`CharacterResurrected` |
| 世界状态 | `FlagSet`(5156)/`FlagCleared`/`TimerFinished`(744) | `ObjectFlagSet`/`GlobalFlagSet`/`StoryEvent`/`TimerFinished` |
| 物品交互 | `UseStarted`/`UseFinished`/`GameBookInterfaceClosed` | `CharacterUsedItem`/`ItemAddedToCharacter` |
| **游戏时间** | **无时钟事件**；`Ext.Timer.GameTime()`+昼夜 flag+`PROC_LongRest` | **`NewHour(hour)` 事件 + `DB_Time(day,hour,total)`** ✅（每游戏小时 5 真实分钟） |
| 读档 | `SavegameLoaded`（anubis 12 处） | `SavegameLoaded`（SE 有 SessionLoaded） |

### 3.3 事件 → LLM 输入的转化原则
1. 事件先经 SE Lua 过滤/聚合（去抖、限频），再发 agent——**绝不高频直灌**（OpenGameAgent 建议：确定性模拟决定哪些 actor 需要推理，再入队）。
2. 每次推理时**拉取式快照**（位置/好感/状态/flag），事件只作"唤醒铃"。

---

## 4. 动作执行接入位置（LLM 决策 → 游戏动作）

### 4.1 工具面候选（按风险分级）
| 风险 | BG3（Osi/anubis） | DOS2（Osi） |
|---|---|---|
| 低（对话/表现） | `QRY_StartDialog`、`StartVoiceBark`、`PlayAnimation`、`LookAtEntity`、`SetEntityEvent` | `Proc_StartDialog`、`StartVoiceBark`、`PlayAnimation`、`CharacterLookAt`、`ProcFaceCharacter` |
| 中（状态/关系） | `ChangeApprovalRating(char,target,0,v,_)`、`ApplyStatus`、`RemoveStatus`、`SetCanTrade` | `CharacterAddAttitudeTowardsPlayer`、`CharacterSetRelation*`（0-100）、`ApplyStatus`、`SetHasDialog` |
| 高（世界改动） | `SetFlag`/`ClearFlag`、`QuestUpdate`、`TeleportTo`、`SetFaction`、`Die` | `ObjectSetFlag`/`GlobalSetFlag`、`TeleportTo`、`SetFaction`、`CharacterSetImmortal` |
| 记忆写入 | `DB_<Mod>_Memory(...)`、`Ext.Vars`、`Ext.IO.SaveFile` | `Osi.DB_LLM_Memory(...)`、`PersistentVars`、`SetVarFixedString(npc,"LLM_*",v)` |

### 4.2 执行模式
- **BG3**：LLM 输出结构化动作 → SE Lua 白名单校验 → `Osi.动作` 或 anubis 函数 → 结果回执。危险动作（Die/TeleportTo/SetFaction）加额外约束。
- **DOS2**：同上，经 `Osi.*`；对话类动作走 `Proc_StartDialog` 完整校验链最稳。
- 与 OpenGameAgent 的 **durable action receipts** 对齐：游戏侧对每个动作返回"已提交/被拒绝/状态不确定"，agent 层据此决定重试还是放弃。

---

## 5. 时间接入（两游戏差异大）

| 项 | BG3 | DOS2 |
|---|---|---|
| 时钟查询 | `Ext.Timer.GameTime()`（毫秒）✅ | 无 SE 时钟 API ⚠️（`Ext.MonotonicTime()` 是真实毫秒单调钟） |
| 游戏内时间 | 无 Osiris 时钟；昼夜 = `GLO_CAMP_State_NightMode` flag + `DB_Camp_NightMode`；长休 = `PROC_LongRest` | `DB_Time(day,hour,total)` + `NewHour(hour)` 事件（权威时间）✅ |
| LLM 时间感 | 自建：tick 采样 GameTime + 昼夜 flag + 长休事件 | 订阅 `NewHour` + 读 `DB_Time` ✅ |
| OpenGameAgent 映射 | `GameMoment(timeline, tick, calendarJson)` —— tick 可定义为"游戏小时/长休次数"，calendar 存 `{day,hour}` | 同左，DOS2 有现成日历数据 |

---

## 6. 通信接入（关键架构约束）

| 项 | BG3 | DOS2 |
|---|---|---|
| SE 出站 HTTP | ❌ **无**（"no external networking capability"） | ❌ **无**（Ext.Net 仅联机消息通道；无 HttpRequest） |
| 文件 IO | ✅ `Ext.IO.SaveFile/LoadFile`（相对游戏 Data 目录） | ✅ **`Ext.IO.SaveFile/LoadFile/Enumerate`（v60+，★修正；写 `Documents\Larian Studios\DOS2 DE\Osiris Data\`，防路径穿越）** |
| 跨进程方案候选 | a) **BG3SE 原生 DLL 模组**（SE native mod loader 加载 C#/C++ DLL，DLL 内可自由 HTTP，可向 Lua 暴露函数）⚠️ 首选验证；b) 文件轮询（Ext.IO + 外部 watcher 进程）✅ 零注入方案 | a) **文件轮询桥（Ext.IO v60+ + 外部 watcher）✅ 首选**——Lua 写请求 JSON → 外部进程转发 HTTP → 读回响应文件；b) Lua 标准库 os/io（若开放）⚠️ 备选；c) ~~原生 DLL~~（无 Ext.ModLoader，DOS2SE 无原生模组 API）❌ |
| 结论 | **LLM 服务必须在游戏外进程**；桥接层（HTTP/WebSocket）由外部进程或原生 DLL 承担；SE Lua 只做事件钩取与动作执行 | 同左；**DOS2 走 Ext.IO 文件轮询桥**（方案已确认可行，等待实测验证实时性） |

---

## 7. 持久化接入（NPC 记忆）

| 层 | BG3 | DOS2 |
|---|---|---|
| 存档内 | `Ext.Vars`（用户变量，随档、可同步）✅ | `PersistentVars` 表（SessionLoaded 前恢复）✅ |
| Osiris 事实表 | `DB_<Mod>_Memory(npcGuid, key, value)`（SE `Osi.DB_*` 读写，随档）✅ | `Osi.DB_LLM_Memory(npc, key, value)` ✅；原生 `DB_HasMet` 记录初遇 ✅ |
| 每角色 KV | —（可用 flag）| `SetVarFixedString(npc, "LLM_LastTopic", v)` ✅ |
| 文件（不随档） | `Ext.IO.SaveFile("Mods/<Mod>/ScriptExtender/memory.json")` ✅ | `Ext.IO.SaveFile("llm_memory.json")`（v60+，★修正；Osiris Data 目录）✅ |
| 硬事实 vs 叙事记忆 | 硬事实→DB/flag；叙事→文件/JSON | 硬事实→DB；叙事→PersistentVars（JSON 序列化） |
| 注意 | 文件方案不随存档回滚；混合方案最稳 | DB 大表对存档膨胀影响待实测 ⚠️ |

---

## 8. 官方 Toolkit 的可用性（交叉验证通道）

- **BG3 Toolkit**（`G:\...\Baldurs Gate 3 Toolkit`）：官方编辑器——可打开对话/Timeline/flag 工程，验证 LSLib 解包结论；是"模组怎么写"的权威参考。
- **The Divinity Engine 2**（`G:\...\The Divinity Engine 2`）：DOS2 官方编辑器，同样用途。
- 后续写模组时两者用于**打包流程**（story 编译、pak 打包）；本阶段只作参考。

---

## 9. 待运行时验证的接入点（阶段 5 前必须实测）

1. **BG3**：`Osi.StartDialog_Internal` 前置条件；`Ext.Events.Tick` 真实频率；`Ext.IO.SaveFile` 是否随档回滚；anubis `DEV_EnableAnubis` 运行时换行为；BG3SE 原生 DLL 模组能否做 HTTP 桥（本项目最大技术风险）。
2. **DOS2**（★二轮修正后收窄）：`Ext.IO` 文件桥的实时性/并发/目录权限（写请求→外部进程转发→读回响应的延迟与轮询频率）；`Osi.StartDialog_Internal` 直调；`Osi.DisplayText(char, text)` 裸字符串显示效果；`Ext.Events.Tick` 实际频率与 e.Time 字段；`Ext.GetCharacter.Stats` 字段全集。
3. **共同**：DB 大表存档膨胀；对话变量注入 LLM 文本的可行性（`DialogSetVariableInt` 存在，`DialogSetVariableString` 类待验证）。

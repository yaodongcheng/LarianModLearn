# 能力矩阵与限制分析（Phase 4 交付物）
## ——OpenGameAgent 能让 BG3 / DOS2 的 NPC 做到什么

> 日期：2026-08-17　|　依据：`opengameagent-study.md`（框架）+ `game-analysis-BG3.md` / `game-analysis-DOS2.md`（游戏）+ `integration-points.md`（接入点）
> 结论分级：✅ 可行（框架能力+游戏接口均已确认）｜🟡 可行但需运行时实测｜❌ 不可行/不建议

---

## 1. 观察（NPC 能"看到"什么）

| 观察维度 | BG3 | DOS2 | 框架侧 |
|---|---|---|---|
| 对话情境（谁在说什么） | ✅ `DialogStarted(dialog,instance)` → 读 .lsj 说话行 + speakerlist | ✅ `DialogStarted`/`DialogActorJoined` + `DB_DialogNPCs/Players` + 对话 .lsj TaggedTexts | ✅ 任意有界 JSON 上下文切片 |
| 周围环境（感知范围） | ✅ `EnteredTrigger`/`GetPosition`/`GetActiveCharacters`/`CanSee` | ✅ `CharacterSawCharacter`→`DB_Sees`/`CharacterEnteredTrigger`/`GetPosition` | ✅ 上下文快照 |
| 自身状态（HP/职业/等级） | 🟡 `Osi.GetStatString`+`Ext.Stats.Get`；HP 读取途径待实测 | ✅ `Ext.GetCharacter(char).Stats`（Vitality 等）| ✅ 拉取式 |
| 好感/关系 | ✅ `Osi.GetApprovalRating(owner,target)`、`DB_ApprovalRating`、阈值 flag | ✅ `CharacterGetAttitudeTowardsPlayer`、`CharacterSetRelation*` 查询、`DB_CompanionAvatarBond` | ✅ 拉取式 |
| 游戏时间 | 🟡 无引擎时钟：`Ext.Timer.GameTime()` + 昼夜 flag + 长休事件自建 | ✅ `DB_Time(day,hour,total)` + `NewHour` 事件 | ✅ `GameMoment.CalendarJson` |
| 世界状态/flag | ✅ `Osi.GetFlag`/`FlagSet` 事件 | ✅ `GlobalGetFlag`/`ObjectGetFlag`/`StoryEvent` | ✅ 上下文切片 |
| 玩家身份 | ✅ `DialogGetInvolvedPlayer`、`DB_Players` | ✅ `CharacterGetReservedUserID`、`IsTagged("AVATAR")` | ✅ payload JSON |
| 图像观察（截图） | ❌ SE 无截图 API（未发现）；且框架图片输入需要游戏提供图片字节 | ❌ 同左 | 🟡 框架支持（PNG/JPEG 准入+能力预检），但游戏侧无图源 → **文本观察为主** |

## 2. 记忆（NPC 能"记住"什么）

框架提供：`IGameMemoryStore`（scope/kind/tag/importance/owner/游戏时间截断/过期）+ 可选向量索引（BGE-M3 等本地 embedding）+ 词法/向量混合召回。**存档权威在 FileGameMemoryStore，随存档独立保存**。

| 记忆类型 | 示例 | BG3 实现 | DOS2 实现 |
|---|---|---|---|
| 事实记忆（见过谁/说过什么/做过什么） | "见过玩家、讨论过 X" | ✅ `DB_<Mod>_Memory(npcGuid,key,value)` + `Ext.Vars` | ✅ `Osi.DB_LLM_Memory(npc,key,value)` + `SetVarFixedString(npc,"LLM_*",v)` |
| 初遇记录 | 官方机制已有 | ✅ flag（`ORI_*_HasMet` 惯例）| ✅ `DB_HasMet(charA,charB)`（引擎自动记录）|
| 叙事长记忆（对话历史摘要） | LLM 生成的摘要 | ✅ `Ext.IO.SaveFile`（文件，**不随档回滚**⚠️）| ✅ `PersistentVars`（随档）**或 `Ext.IO.SaveFile`（v60+，★修正，Osiris Data 目录）** |
| 语义检索（"他以前提过那条河吗？"） | embedding 向量 | ✅ 框架层（记忆存文件/DB，向量存框架）——**注意：游戏进程重启/读档时需框架侧同步恢复** | 同左 |
| 好感变化历史 | 每次 ApprovalRatingChanged | ✅ 事件订阅→写入记忆 | ✅ 事件订阅→写入记忆 |

**记忆生命周期建议**：游戏时间戳（框架 `GameMoment`）+ 过期策略；读档时 `SavegameLoaded`/`SessionLoaded` 事件触发记忆恢复（框架 `GameTimeScheduler.CaptureState()` 防重放）。

## 3. 执行（NPC 能"做"什么）

框架侧：模型只提动作请求，经 JSON Schema 校验 + 游戏校验后执行，回执返回。游戏侧动作面（见 integration-points §4）：

| 动作类别 | BG3 | DOS2 | 适合度 |
|---|---|---|---|
| 说话（对话启动） | 🟡 `StartDialog_Internal`（未文档化）或复刻 `QRY_StartDialog` 前置 | ✅ `Osi.Proc_StartDialog`（完整校验链）| 核心动作 |
| 一句话台词 | ✅ `StartVoiceBark` | ✅ `StartVoiceBark` | ✅ |
| 表情/姿态 | ✅ `PlayAnimation`/`LookAtEntity` | ✅ `PlayAnimation`/`CharacterLookAt`/`ProcFaceCharacter` | ✅ 表现层 |
| 移动 | ✅ anubis `MoveTo`/`Wander`；Osiris `TeleportTo` | ✅ `CharacterMoveTo`/`TeleportTo` | 🟡 移动类建议引擎原语执行，LLM 只定目标 |
| 好感/态度修改 | ✅ `ChangeApprovalRating` | ✅ `CharacterAddAttitudeTowardsPlayer`/`CharacterSetRelation*` | ✅ 关系动态 |
| 状态修改 | ✅ `ApplyStatus`/`RemoveStatus` | ✅ 同左 | ✅ |
| 物品交互 | ✅ `ToInventory`/`AddGold` 等 | ✅ `ItemToInventory`/`CharacterAddGold` | ✅ 交易/赠礼 |
| 世界事实 | ✅ `SetFlag`/`ClearFlag`/`QuestUpdate` | ✅ `ObjectSetFlag`/`GlobalSetFlag`/`SetStoryEvent` | ✅ 任务/状态 |
| 动态文本注入对话 | 🟡 对话变量 API 存在，注入 LLM 文本未验证 | 🟡 同左 | 待实测 |
| 头顶浮字 | 🟡 `DebugText`/`Ext.UI`（复杂）| ✅★ `Osi.DisplayText(char, text)` 原版函数存在（香草传本地化 key，裸字符串需实测）| 🟡 待实测 |

## 4. 目标、任务、游戏时间、关系、多角色——框架如何用

### 4.1 目标（Goals）
- 框架 `GoalLoopExtension`：actor 拥有语义目标，可等待 tick/事件后继续；`MaximumActiveGoals` 有界。
- **游戏侧落地**：NPC 的"目标"= 游戏内可验证条件（flag/DB 状态）。例：商人目标"今天卖掉 3 件商品"→ agent 循环 → 工具（`SetCanTrade`、对话）→ 回执 → `GameMoment` 推进 → 明天重新调度（`GameTimeScheduler`）。
- **任务清单（Task plans）**：`TaskPlanExtension`——有序检查表，必须宿主验证证据（`GameTaskPlanEvidenceValidator`）才能推进。例：营救任务的步骤（找到钥匙→开门→带人走），每步由游戏侧回执验证。
- **确定性工作流（Workflow）**：固定执行图，如"清晨例行（起床→打招呼→开店→打烊）"用 `DurableGameWorkflow`，节点可等待（检查点持久化，读档可续）。**适合 DOS2 的 `NewHour` 驱动日程**。

### 4.2 游戏时间
- 框架 `GameMoment(timelineId, tick, calendarJson)`：**tick 由游戏定义**。
- **BG3**：tick = `Ext.Timer.GameTime()` 采样节拍或长休次数；calendar = `{day, hour}`（自建自 `GLO_CAMP_State_NightMode` + 长休）。**DOS2**：tick = 游戏小时（`NewHour` 事件驱动）；calendar = `DB_Time(day,hour,total)` 直接喂给 `CalendarJson` ✅。
- 记忆按游戏时间过滤/过期；读档不重放已发生事件（`GameTimeScheduler.CaptureState()`）；**绝不用墙钟判断游戏内先后**（框架明文规则）。

### 4.3 人物关系
- 关系 = 上下文切片（好感/态度/阵营矩阵，见 §1）+ 记忆（关系变化历史）。
- 框架 `GameContextSlice` 带 priority，关系数据可作为高优先级切片。
- **社交场景**（多人对话）：框架建议**每 actor 独立 session、视角过滤上下文**——与 BG3 对话 speakerlist/旁听位（IsPeanutSpeaker）结构吻合：每个 NPC 只看到自己该看到的。
- BG3 好感系统（ApprovalRatings 反应表 + 阈值 flag）与 DOS2 Attitude/阵营矩阵都是**游戏权威**，LLM 不直接改好感数值，而是通过动作（表态/赠礼/拒绝）触发引擎改。

### 4.4 多角色
- 每 (session, actor) 一条通道：同 NPC 串行、跨 NPC 有界并发（`MaxConcurrentActors`）。
- **唤醒策略**（框架明示）：确定性模拟决定哪些 NPC 需要推理 → 生成有界信号 → 按重要度/距离选择 actor → 入队。游戏侧 = SE Lua 事件过滤 + 距离/状态条件，不每帧全量唤醒。
- **邮箱**（`IGameMailbox`）：NPC 不在场时消息持久排队；`GetPendingStatusAsync` 只读查询积压（不 claim 不调模型），用于"预算边界"决策。
- 导演角色（AI director）建议独立 actor，权限最小化——适合"村长/掌权 NPC"统筹型玩法。

## 5. 哪些效果适合这些游戏（可行性矩阵）

| 玩法效果 | 适合度 | 理由 |
|---|---|---|
| **对话型 NPC**（闲聊/询问/讲价/求助，LLM 台词）| ✅ 首选 | 事件触发明确（DialogStarted）、动作面成熟（对话/态度/物品）、观察数据齐全 |
| **NPC 日程与自主行动**（按时作息、主动搭话）| ✅ | DOS2 `NewHour`+`DB_Time` 现成；BG3 需自建时钟但 anubis 定时器可兜底；`CharacterMoveToAndTalkRequestDialog`（DOS2）是"NPC 主动走向玩家对话"现成机制 |
| **关系驱动剧情**（好感变化引发态度/对话改变）| ✅ | 两游戏关系 API 齐全；框架 goals/task plans 承载"好感阈值→新对话解锁" |
| **任务生成/动态支线** | 🟡 | 需先实测"动态对话注入"与 QuestUpdate 的兼容面；低风险版本：LLM 选现有任务组合 |
| **NPC 记忆演化**（记得玩家过往行为并提及）| ✅ | 记忆层 + 事件记录齐全；初遇/对话历史均可持久化 |
| **战斗指挥**（LLM 参与回合决策）| 🟡 不建议初期做 | 两游戏战术 AI 是引擎权威（DOS2 Archetype 打分、BG3 anubis）；框架文档也建议低层战斗留在确定性代码；后续可做"开战前谈判/战后反应" |
| **图像感知**（看屏幕截图决策）| ❌ | 游戏侧无截图通道 |
| **多玩家/联机** | ❌ 初期不做 | SE 钩子本地性 + 存档分歧；框架支持多 session，但 Larian 联机场景复杂 |

## 6. 限制清单（必须正视）

### 6.1 框架侧
1. **0.3.0-alpha**：公开 API 1.0 前可能变动 → 桥接层隔离（见 integration-design.md §4 解耦策略）。
2. **构建需 .NET 8 SDK**（本机未装）。
3. 本地文件存储非加密、非分布式；单机单服务够用。
4. 图片输入需要游戏提供图源（Larian 无）→ 纯文本观察。
5. 每个活跃 actor 消耗 LLM token；多 NPC 成本线性增长 → 唤醒策略 + 本地模型（Ollama）是关键。

### 6.2 游戏侧
1. **两游戏 SE 均无出站 HTTP**（BG3 明确无；DOS2 Ext.Net 仅联机消息）→ 通信桥是**最大技术风险**，但已收窄：**DOS2 走 `Ext.IO` 文件轮询桥（v60+ 确认存在，★二轮修正）**；BG3 走原生 DLL 或 Ext.IO 文件桥（方案见 integration-design.md §3）。
2. **BG3 无 `Osi.Say`/头顶浮字**；动态对话注入未验证 → 初期"LLM 台词"走对话系统（StartDialog 族/StartVoiceBark）。
3. BG3 无引擎时钟 → 时间感自建。
4. 存档/读档：`Ext.IO.SaveFile`（BG3）不随档回滚；`PersistentVars`（DOS2）随档但需 SessionLoaded 后恢复；DB 大表对存档膨胀的影响待实测。
5. **SE 版本与游戏版本强绑定**：BG3SE v32 需匹配当前补丁；游戏更新会破坏模组（这是所有 Larian 模组的常态）。
6. SE 未安装（本计划从未写入游戏目录）——所有 🟡 项需在安装后实测，**该步骤需用户确认**。

### 6.3 方案侧
1. LLM 延迟：单次推理 1-3s（本地）~5-15s（云端）→ 对话响应需"先给引擎占位台词、LLM 决定后续"或流式；anubis 兜底行为避免 NPC 呆站。
2. 上下文预算：每 NPC 每轮观察快照要**有界**（几十 KB 内），框架已内置限界与 artifact 机制。
3. 安全：动作白名单 + 游戏侧二次校验（框架权威边界设计）；不暴露危险工具（Die/TeleportTo 需约束）。

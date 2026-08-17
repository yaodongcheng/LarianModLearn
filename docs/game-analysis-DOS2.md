# 《神界：原罪 2 决定版》游戏结构深度分析报告
### —— 面向"大模型驱动 NPC AI"模组的前置研究

> 分析日期：2026-08-17　|　目标平台：DOS2 Definitive Edition　|　纯分析阶段，未写任何模组代码
>
> 数据来源（全部为已解包原始文件，路径均为绝对路径）：
> - Osiris 规则目标（68 个 goal，780KB 文本）：`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\osid\`
> - 起源模组规则（本次新反编译）：`F:\LarianModLearn\docs\_scratch\osid_origins\`（源：`F:\LarianModLearn\extracted\DOS2\Mods\DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4\Story\story.div.osi`）
> - 对话：`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\Dialogs\`（436 个 .lsj JSON）
> - 阵营：`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\Alignments\Alignment.lsx`
> - 数值：`F:\LarianModLearn\extracted\DOS2\Public\Shared\Stats\Generated\Data\Character.txt` 等
> - AI：`F:\LarianModLearn\extracted\DOS2\Public\Shared\AI\`（Archetypes\*.txt、combos.txt）
> - 脚本：`F:\LarianModLearn\extracted\DOS2\Public\Shared\Scripts\`（*.charScript）
> - 角色模板样本（Divine 转换）：`F:\LarianModLearn\docs\_scratch\characters_cc.lsx`
> - 事件/动作函数统计（awk 全量提取）：`F:\LarianModLearn\docs\_scratch\if_events.tsv`、`then_actions.tsv`

**提取方法**（可复现）：对 osid 全部 68 个 .txt 做单遍 awk——`IF`/`THEN` 行内首个形如 `函数名(` 的标识符，按"IF 条件 / THEN 动作"分类计数，并记录每个函数名首次出现的 `文件:行`。得到 **648 个不同 IF 条件函数、1292 个不同 THEN 动作函数**（去重后），下文表格为按使用次数排序的前 100。

---

## A. NPC 系统：NPC 如何定义

### A.1 角色数值体系（Stats）

角色数值是**分层模板继承**体系，核心文件 `F:\LarianModLearn\extracted\DOS2\Public\Shared\Stats\Generated\Data\Character.txt`（`new entry "<模板名>" type "Character" data "属性" "值"` 格式，`using "<父模板>"` 表示继承）：

| 层级 | 条目示例（文件内行号） | 内容 |
|---|---|---|
| 基础底模 | `_Base`（行 1-64） | 全属性默认值：Strength/Finesse/Intelligence/Constitution=2，Vitality=100，APMaximum=6，Movement=500，Sight=-2，各学派=0，PathInfluence（地形路径偏好）等 60+ 字段 |
| 占位/难度 | `PlaceholderStatEntry`（行 66）、`StoryNPC_Character`（153）、`CasualNPC`（161）、`NormalNPC`（169）、`HardcoreNPC`（172） | 难度模子：StoryNPC_Character 全属性 -40~-50%（护甲/血量/伤害），HardcoreNPC +50% |
| 玩家模子 | `StoryPlayer`（129）、`NormalPlayer`（147） | 玩家加成 |
| 种族 | `_Human`（377）、`_Dwarf`（388）、`_Elf`（399）、`_Lizard`（410）、`_Animal`（434）、`_Skeleton`（459）等 | 种族基础属性 |
| 职业原型 | `_HumanFighter`（723）、`_HumanCleric`（741）、`_HumanRanger`（757）… | `using "_Human"` + 职业专精（如 `data "Talents" "AttackOfOpportunity"`）、抗性 |

**关键结论：NPC 个体模板（`S_` 前缀）不在 Character.txt 中**（`grep 'new entry "S_'` = 0 条），而是内嵌在**关卡 .lsf 资源的 Templates 段**。已验证样本（用 Divine 将 `F:\LarianModLearn\extracted\DOS2\Mods\Shared\Globals\SYS_Character_Creation_A\Characters\_merged.lsf` 转为 `F:\LarianModLearn\docs\_scratch\characters_cc.lsx`），每个 GameObjects 节点包含：

- `Name` = `S_GLO_CharacterCreationDummy_002` / `S_Player_GenericOrigin3`（即 S_ 模板 ID）
- `TemplateName` = stats 模板 UUID（`25611432-e5e4-482a-8f5d-196c9e90001e`）
- `MapKey` = 关卡名；`Alignment` = `"Hero Player7"`（实体阵营名）
- `SpeakerGroup` = 语音组 UUID
- `Scripts/Script/Parameters` = 角色脚本参数，如 `Archetype`=`base`、`AiHint`、`FleeFromDangerousSurface`、`bool_CanCower` 等（对应 `Public\Shared\Scripts\DefaultCharacter.charScript` 里的 EXTERN 变量）
- `Tags`（标签）、`Transform`（初始位置）、`LayerList`

osid 中 S_ 模板 ID 的命名规律（`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\osid\` 全量提取）：`S_<关卡/区域>_<角色>_<uuid前8>`，例如 `S_FTJ_ArenaMaster_4eadc6c7`、`S_FTJ_RingGirl_Helper_2c6f3151`、`S_Player_Fane_02a77f1f-872b-49ca-91ab-32098c443beb`（完整 UUID 常量，见 Origins 的 `GLO_ThePromise_SelfTest.txt:489`）、`S_GLO_CharacterCreationDummy_001_da072fe7`（出现 10 次）。角色对话名 = 模板 ID（见 A.2）。

**角色运行时身份**：每个角色实例有 `CHARACTERGUID`（GUID）；Osiris 中大量函数用 `CharacterGetReservedUserID(char, userID)` / `CharacterGetHostCharacter` 关联"哪个玩家"；`DB_IsPlayer(char)` 是"是否玩家队伍成员"的权威数据库标记（见 F）。

### A.2 对话文件命名规律

`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\Dialogs\` 下共 **436 个 .lsj**，前缀统计：

| 前缀 | 数量 | 含义（据文件名+内容推断） | 例 |
|---|---|---|---|
| CMB_ | 271 | 战斗评论（Combat Comments），含子目录 `GEN_Comments\Combat\` | `CMB_AD_Comment_DEATH.lsj`、`CMB_AD_PC_UseSkill.lsj` |
| GEB_ | 64 | 通用通用对话模板（General Base），大量为犯罪/卫兵系统 | `GEB_AD_Noticed_Theft.lsj`、`GEB_Interrogation.lsj`、`GEB_Warning_Assault.lsj` |
| GEN_ | 56 | 通用对话（General） | `GEN_BrokenTombstone.lsj`、`GEN_AD_DisarmTrap.lsj` |
| GLO_ | 16 | 全局系统对话 | `GLO_NonBondedCompanionDialog.lsj` |
| Sandbox | 23 | 编辑器测试 | - |

另有子目录：`Crimes\`（犯罪系统 60+ 对话）、`GEN_Comments\`、`DialogVariables\DialogVariables.lsx`、`ScriptFlags\ScriptFlags.lsx`、`Test\`。`VoiceBarks\GEN_Comments\` 下是**语音 bark 定义**（JSON：`VoiceBarkData` → `Dialog` 名称 + 标签数组，见 `F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\VoiceBarks\GEN_Comments\GEN_VB_Map_Generic.lsj`）。

**重要：`S_` 角色专属对话不在 Shared 包里**（`find Dialogs -iname "S_*"` 为空）——角色对话资源打包在**关卡 .lsf 内部**，osid 中以模板 ID 字符串引用对话名。系统级对话（犯罪、战斗评论、通用事件）才是 Shared 包的 .lsj。已确认一个对话 JSON 的结构（此前会话已验证）：`save.regions.Dialog` → nodes → `RootNodes`（含 AiPersonalities/Emotion/SoundEvent/CameraTarget 的 GameData）、`TaggedTexts`（带种族标签规则的说话行 handle+value）。

### A.3 LLM 观察一个 NPC 需要的数据（结论清单）

综合 A.1/A.2 与 B/C/D/E/F 各节，运行时观察一个 NPC 至少需要：

1. **身份**：CHARACTERGUID、S_ 模板 ID、MapKey/所在关卡、是否 `DB_IsPlayer`（玩家队伍成员）、`SpeakerGroup`、Alignment 实体名（"Hero Player7" 等）
2. **数值**：stats 模板（基础 + 关卡覆盖）、当前 HP/AP/等级（`CharacterGetHitpointsPercentage`、`CharacterGetLevel`）、当前状态（`HasActiveStatus(char,"FROZEN",0)` 等）、Archetype（AI 原型）
3. **关系**：faction 关系矩阵（0-100）、Attitude 声誉（`CharacterGetAttitudeTowardsPlayer`）、`DB_CrimeAttitudeChange` 表、Alignment 实体
4. **记忆状态**：DB_ 数据库行（`DB_HasMet`、`DB_IsPlayer`、`DB_Dead` 等）、Object/Global flags、角色变量（`SetVarFixedString` "currentState"）、StoryEvent
5. **对话**：可用性（`QRY_SpeakerIsAvailable`：未死/未战斗/未占用/未被禁用/10m 内）、当前/历史对话（`DB_DialogName`、`DB_HasMet`）、voice bark 映射
6. **环境**：位置（`GetPosition`）、所在 trigger/区域（`DB_InRegion`）、看见谁（`CharacterSawCharacter` → `DB_Sees`）、当前游戏时间（`DB_Time`）

---

## B. 事件系统：IF 块中的事件名（去重 Top 100）

全量提取结果（次数 = 在全部 68 个 goal 的 IF 条件中出现次数；例 = 首次出现文件:行）。其中**引擎事件**（由引擎主动触发）与**查询/DB 条件**（被动检查）混合排列，已用"类型"列区分；下节"重点关注"再按业务分类给出真实 IF 块。

| # | 次数 | 名称 | 类型 | 首例（文件:行） |
|---|---|---|---|---|
| 1 | 134 | DB_IsPlayer | DB 条件 | GLO_Follower.txt:90 |
| 2 | 95 | ObjectFlagSet | 事件（对象旗标被置位） | GLO_Arena.txt:30 |
| 3 | 72 | DialogEnded | 事件（对话结束） | GLO_Arena.txt:61 |
| 4 | 65 | StoryEvent | 事件（角色剧情事件） | GLO_Arena.txt:1033 |
| 5 | 44 | DB_CombatCharacters | DB 条件 | GLO_Arena.txt:657 |
| 6 | 39 | DB_DialogNPCs | DB 条件 | GLO_Checkpoints.txt:44 |
| 7 | 37 | DB_DialogPlayers | DB 条件 | ZZZ_LastGoal.txt:47 |
| 8 | 34 | IsTagged | 查询（标签） | Z_Shared_CharacterCreation.txt:305 |
| 9 | 31 | StringConcatenate | 查询（字符串） | GLO_BidirShovelTunnel.txt:10 |
| 10 | 28 | TextEventSet | 事件（调试控制台文本） | _CRIME_Prison.txt:647 |
| 11 | 23 | CharacterEnteredTrigger | 事件（角色进入触发器） | GLO_Follower.txt:115 |
| 12 | 23 | CharacterIsPlayer | 查询 | GLO_Arena.txt:643 |
| 13 | 23 | CharacterUsedItem | 事件（角色使用物品） | _GLOBAL_TeleporterPyramids.txt:24 |
| 14 | 19 | DB_TeleporterPyramid | DB 条件 | _GLOBAL_TeleporterPyramids.txt:8 |
| 15 | 18 | CharacterGetHostCharacter | 查询 | _GLOBAL_Shared_Shapeshifting.txt:150 |
| 16 | 18 | QRY_SpeakerIsAvailable | 查询（说话者可用） | _GLOBAL_TutorialMessages.txt:150 |
| 17 | 17 | DialogStarted | 事件（对话开始） | GLO_Arena.txt:47 |
| 18 | 16 | DB_Dead | DB 条件 | _AAA_FirstGoal.txt:478 |
| 19 | 16 | DB_FollowerOwners | DB 条件 | GLO_Follower.txt:70 |
| 20 | 16 | ObjectGetFlag | 查询 | _CRIME_CrimeTriggers.txt:654 |
| 21 | 15 | CharacterDied | 事件（角色死亡） | _AAA_FirstGoal.txt:543 |
| 22 | 15 | ObjectEnteredCombat | 事件（进入战斗） | GLO_Checkpoints.txt:35 |
| 23 | 14 | SavegameLoaded | 事件（读档） | GLO_Arena.txt:1196 |
| 24 | 13 | CharacterGetReservedUserID | 查询 | GLO_Arena.txt:53 |
| 25 | 13 | CharacterOnCrimeSensibleActionNotification | 事件（犯罪告密通知） | _CRIME_CrimeTriggers.txt:300 |
| 26 | 13 | CharacterReservedUserIDChanged | 事件（玩家认领变化） | GLO_Arena.txt:1295 |
| 27 | 13 | CrimeGetType | 查询 | _CRIME_CrimeTriggers.txt:385 |
| 28 | 13 | DB_CompanionAvatarBond | DB 条件（恋爱/队友绑定） | _GLO_Shared_Origins.txt:443 |
| 29 | 13 | DB_Crime_Assault | DB 条件 | _CRIME_CrimeTriggers.txt:1692 |
| 30 | 13 | DialogGetInvolvedPlayer | 查询（对话参与玩家） | GLO_Arena.txt:51 |
| 31 | 13 | GetTextEventParamString | 查询 | _Greevers_Little_Helpers.txt:1304 |
| 32 | 13 | GlobalGetFlag | 查询 | GLO_Arena.txt:548 |
| 33 | 13 | IntegerSum | 查询 | _AAA_FirstGoal.txt:425 |
| 34 | 13 | ItemAddedToCharacter | 事件（物品进入角色背包） | _GLOBAL_ItemEvents.txt:480 |
| 35 | 12 | DB_InCharacterCreation | DB 条件 | Z_Shared_CharacterCreation.txt:113 |
| 36 | 12 | GetVarInteger | 查询（角色变量） | GLO_Follower.txt:52 |
| 37 | 12 | ObjectLeftCombat | 事件（离开战斗） | _CRIME_CrimeTriggers.txt:1729 |
| 38 | 12 | RegionStarted | 事件（区域加载开始） | GLO_Follower.txt:86 |
| 39 | 11 | CharacterItemEvent | 事件（角色物品交互） | _GLOBAL_ItemEvents.txt:81 |
| 40 | 11 | CharacterLeftTrigger | 事件（角色离开触发器） | GLO_Checkpoints.txt:51 |
| 41 | 11 | CharacterMoveToAndTalkRequestDialog | 事件（走向并对话请求） | _CRIME_CrimeTriggers.txt:940 |
| 42 | 10 | CharacterCreationFinished | 事件 | ZZZ_LastGoal.txt:90 |
| 43 | 10 | CharacterDying | 事件（濒死） | GLO_Arena.txt:599 |
| 44 | 10 | DB_CurrentLevel | DB 条件 | Sandbox.txt:16 |
| 45 | 10 | DB_Dialogs | DB 条件 | _Waypoints.txt:200 |
| 46 | 10 | DB_Followers | DB 条件 | GLO_Follower.txt:9 |
| 47 | 10 | GetTextEventParamInteger | 查询 | _Greevers_Little_Helpers.txt:1284 |
| 48 | 10 | GetUserProfileID | 查询 | GLO_Arena_LMS.txt:438 |
| 49 | 10 | GetVarObject | 查询 | GLO_Follower.txt:39 |
| 50 | 10 | HasActiveStatus | 查询（状态检测） | GLO_Arena.txt:649 |
| 51 | 10 | ObjectIsCharacter | 查询 | _CRIME_CrimeTriggers.txt:1605 |
| 52 | 10 | TimerFinished | 事件（计时器到期） | GLO_Arena.txt:1028 |
| 53 | 9 | CharacterJoinedParty | 事件（入队） | _CRIME_CrimeTriggers.txt:842 |
| 54 | 9 | DB_InRegion | DB 条件 | GLO_Checkpoints.txt:57 |
| 55 | 9 | QRY_VersionIsOlderThan | 查询（版本比对） | _CRIME_CrimeTriggers.txt:4602 |
| 56 | 8 | AttackedByObject | 事件（被攻击） | _CRIME_CrimeTriggers.txt:1688 |
| 57 | 8 | AutomatedDialogEnded | 事件（自动对话结束） | GLO_Arena.txt:1047 |
| 58 | 8 | CharacterGetAttitudeTowardsPlayer | 查询（声誉） | _GLO_Shared_Origins.txt:445 |
| 59 | 8 | CharacterStatusRemoved | 事件（状态移除） | GLO_Arena.txt:1270 |
| 60 | 8 | DB_Arresting | DB 条件 | _CRIME_Prison.txt:179 |
| 61 | 8 | DB_WaypointInfo | DB 条件 | _GLOBAL_TutorialMessages.txt:236 |
| 62 | 8 | DialogGetInvolvedNPC | 查询 | _GLOBAL_ItemEvents.txt:911 |
| 63 | 8 | GlobalFlagSet | 事件（全局旗标置位） | GLO_Arena.txt:123 |
| 64 | 8 | ObjectExists | 查询 | _CRIME_CrimeTriggers.txt:778 |
| 65 | 8 | ObjectTurnStarted | 事件（回合开始） | GLO_Arena.txt:641 |
| 66 | 7 | CharacterKilledBy | 事件（被谁杀死） | _CRIME_CrimeTriggers.txt:2582 |
| 67 | 7 | CharacterResurrected | 事件（复活） | GLO_Arena.txt:612 |
| 68 | 7 | CharacterStatusApplied | 事件（状态施加） | GLO_Arena.txt:678 |
| 69 | 7 | CharacterWentOnStage | 事件（上台/入场景） | GLO_Follower.txt:68 |
| 70 | 7 | GetInventoryOwner | 查询 | _GLOBAL_TeleporterPyramids.txt:131 |
| 71 | 7 | ItemTemplateAddedToCharacter | 事件（模板物品进包） | _GLOBAL_ItemEvents.txt:703 |
| 72 | 7 | ObjectFlagCleared | 事件 | GLO_Checkpoints.txt:158 |
| 73 | 7 | ObjectIsItem | 查询 | _CRIME_CrimeTriggers.txt:3179 |
| 74 | 7 | OnCrimeResolved | 事件（犯罪了结） | _CRIME_CrimeTriggers.txt:720 |
| 75 | 7 | RegionEnded | 事件（区域卸载） | _AAA_FirstGoal.txt:578 |
| 76 | 6 | CharacterIsDead | 查询 | _CRIME_CrimeTriggers.txt:1716 |
| 77 | 6 | ObjectIsInTrigger | 查询 | _GLOBAL_TeleporterPyramids.txt:153 |
| 78 | 6 | OnCrimeConfrontationDone | 事件 | _CRIME_CrimeBribes.txt:278 |
| 79 | 6 | Query_IsPlayerHiding | 查询（潜行/隐身） | _Greevers_Little_Helpers.txt:245 |
| 80 | 6 | RequestPickpocket | 事件（偷窃请求） | _CRIME_CrimeTriggers.txt:2829 |

（完整 648 条见 `F:\LarianModLearn\docs\_scratch\if_events.tsv`；另含 DB_Sees/DB_Subregion/DB_CheckPoint/GetPosition/IntegertoString/ItemIsInCharacterInventory/QRY_GetFairRand 等查询类函数。）

### B.1 重点关注分类（真实 IF 块原文）

**对话开始/结束**（`GLO_Arena.txt:45-55`）：
```
IF
DialogStarted((STRING)_Var1, (INTEGER)_Var2)
AND DB_ArenaMaster(_, _Var1, _, _)
AND DialogGetInvolvedPlayer(_Var2, 1, _Var6)
AND CharacterGetReservedUserID(_Var6, _Var7)
...
```
对话生命周期事件链（`_AAA_FirstGoal.txt:54-103`）：`DialogRequestFailed` / `AutomatedDialogRequestFailed` → `DialogStarted(dialogName, instanceID)` → `DialogActorJoined(dialogName, instanceID, actorGUID)` → `AutomatedDialogStarted`（自动对话）→ `DialogEnded` / `AutomatedDialogEnded` / `VoiceBarkStarted`。对话实例 ID（INTEGER）贯穿全程，配合 `DB_DialogName(_Var1,_Var2)`、`DB_DialogNPCs/DB_DialogPlayers(instance, actor, slot)` 跟踪参与人。

**角色进入/离开/感知**：
```
IF CharacterEnteredTrigger((CHARACTERGUID)_Var1, (TRIGGERGUID)_Var2)   -- GLO_Follower.txt:113-118
IF CharacterSawCharacter((CHARACTERGUID)_Var1, (CHARACTERGUID)_Var2)   -- _AAA_FirstGoal.txt:464-469
  AND DB_IsPlayer(_Var1) → DB_Sees(_Var1, _Var2)                       （看见即记录到 DB_Sees）
```
另有 `CharacterLeftTrigger`、`CharacterLeftRegion(char, region)`（_Global_RunUpAndChat.txt:53）、`RegionStarted/RegionEnded`、`CharacterWentOnStage`（上台进入场景，`GLO_Follower.txt:68`，用于生成"NPC 入席"类事件）。

**死亡**：
```
IF CharacterKilledBy((CHARACTERGUID)_Var1, (CHARACTERGUID)_Var2, (CHARACTERGUID)_Var3)  -- _CRIME_CrimeTriggers.txt:2580-2588
  AND NOT DB_IsPlayer(_Var1) AND CharacterIsPlayer(_Var3, 1) ...
```

**战斗**：
```
IF ObjectEnteredCombat((CHARACTERGUID)_Var1, _)   -- GLO_Checkpoints.txt:35-38
  AND DB_CheckPointGuard(_Var1, _) THEN ObjectClearFlag(_Var1, "GLO_CP_WarningSomeone", 0);
```

**物品**：
```
IF ItemAddedToCharacter((ITEMGUID)_Var1, (CHARACTERGUID)_Var2)   -- _GLOBAL_ItemEvents.txt:480-485
  AND DB_HasStoryEvent(_Var1, _Var3) THEN SetOnStage(_Var1, 1); ProcSetMagicPocketsOwnershipFlag(_Var2, _Var3);
```

**走向对话**（`_CRIME_CrimeTriggers.txt:938-948`）：`CharacterMoveToAndTalkRequestDialog(char, player, _, _, dialogName)` 及 `CharacterMoveToAndTalkFailed(char, _, dialogName)` 事件——NPC 主动走向玩家发起对话的现成机制。

**计时器**（`GLO_Arena.txt:1026-1032`）：`IF TimerFinished("Arena_PlayingVictoryAnimation") THEN Proc_Arena_Win_TeleportOut();`

**游戏时间**：`IF TimerFinished("TimeOfDay") ... NewHour(_Var6);`（见 D 节）。

### B.2 Public\Shared\AI：AI 行为如何定义

`F:\LarianModLearn\extracted\DOS2\Public\Shared\AI\` 全部为可读文本，仅两类文件（无需 LSF 转换）：

1. **`Archetypes\*.txt`** —— 12 个战术原型（base/bazooka/berserker/bomber/healer/mage/melee/ranged/ranger/rogue/warrior，另有 CLASSIC\base、TACTICIAN\base 难度变体）。内容为**评分乘数表**，例如 `Archetypes\base.txt`：`MULTIPLIER_DAMAGE_ENEMY_POS 1.0`、`MULTIPLIER_DAMAGE_ALLY_NEG 1.5`（"打队友看起来太蠢"）；`melee.txt`：`MULTIPLIER_KILL_ENEMY 3.00`（"近战爱杀戮"）、`MULTIPLIER_TARGET_MY_ENEMY 1.20`、`FALLBACK_WANTED_ENEMY_DISTANCE 5.00`。即：**AI 对每个候选动作（伤害/治疗/DOT/控制/增益/移动终点…）按角色-目标关系算分，再乘原型系数选最高分**。
2. **`combos.txt`** —— 元素组合表（`Surface SurfaceWater SurfaceWaterElectrified Electrify` 等），AI 规划 combo 用。

原型绑定方式：角色模板 Script 参数 `Archetype`=`base`（见 A.1 的 characters_cc.lsx），`Public\Shared\Scripts\DefaultCharacter.charScript` 中 `CharacterSetArchetype(__Me,%Archetype)`。Stats 里有空条目 `_Archetypes`（Character.txt:720）。charScript 是引擎脚本语言（INIT/VARS/EVENTS/EVENT X ON 事件 ACTIONS），如 `DefaultCharacter.charScript` 监听 `OnCrimeSensibleAction`、`OnInit`。

**对 LLM 模组的意义**：战术层（打分选择）与剧情层（Osiris）完全分离；LLM 不需要替代战斗 AI，只需在"对话/行为意图→动作"层介入。

---

## C. 动作 API：THEN 块函数目录（去重 Top 100）

| # | 次数 | 名称 | 说明（例：文件:行） |
|---|---|---|---|
| 1 | 191 | DB_NOOP | 查询/动作占位（DB_NOOP(1)）GLO_Arena.txt:700 |
| 2 | 109 | ObjectClearFlag | 清除对象旗标 GLO_Arena.txt:44 |
| 3 | 69 | ObjectSetFlag | 设置对象旗标 GLO_Arena.txt:687 |
| 4 | 64 | Proc_StartDialog | 启动对话（见 C.1）GLO_Arena.txt:1044 |
| 5 | 51 | QRY_SpeakerIsAvailable | 说话者可用性检查 QRY_Characters.txt:20 |
| 6 | 45 | GlobalClearFlag | 清全局旗标 GLO_Arena.txt:92 |
| 7 | 36 | CharacterMakeStoryNpc | 设为"剧情 NPC"（免疫非剧情伤害）_AAA_FirstGoal.txt:114 |
| 8 | 35 | SetOnStage | 上台/入场景 GLO_Arena.txt:27 |
| 9 | 33 | SetStoryEvent | 角色剧情事件标记 GLO_Arena.txt:954 |
| 10 | 30 | SetHasDialog | 开关"可对话" GLO_PartyPresets.txt:157 |
| 11 | 29 | GlobalSetFlag | 置全局旗标 GLO_Arena.txt:137 |
| 12 | 28 | SetTag | 加标签 GLO_Arena.txt:858 |
| 13 | 25 | DebugText | 屏幕调试文本 GLO_Arena.txt:34 |
| 14 | 24 | ProcItemSetInvulnerableForDialog | 对话期间物品无敌 _AAA_FirstGoal.txt:121 |
| 15 | 24 | TeleportTo | 传送 GLO_Arena.txt:569 |
| 16 | 23 | ProcFaceCharacter | 面对面（对话摆位）__GLOBAL_Dialogs.txt:311 |
| 17 | 22 | QRY_PrepForInteractiveDialog | 交互对话前准备 __GLOBAL_Dialogs.txt:289 |
| 18 | 21 | ProcRemovePolymorphsFromPlayer | 解除变形 _GLOBAL_Shared_Shapeshifting.txt:88 |
| 19 | 20 | PlayAnimation | 播放动画 GLO_Arena.txt:1015 |
| 20 | 20 | RemoveStatus | 移除状态 GLO_Arena.txt:1292 |
| 21 | 19 | IsTagged | 标签检查 _CRIME_CrimeTriggers.txt:823 |
| 22 | 18 | ClearTag | 移除标签 GLO_Arena.txt:869 |
| 23 | 18 | DialogRequestStop | 停止对话 GLO_Arena.txt:541 |
| 24 | 18 | RequestProcessed | 确认请求已处理 _CRIME_CrimeTriggers.txt:3835 |
| 25 | 18 | SetVarFixedString | 角色字符串变量 GLO_Follower.txt:11 |
| 26 | 18 | SetVarInteger | 角色整数变量 _AdvancedSneakTriggerSpotter.txt:64 |
| 27 | 16 | ProcObjectTimer | 角色计时器（起）_CRIME_CrimeTriggers.txt:973 |
| 28 | 15 | ProcTriggerRegisterForPlayers | 触发器注册给玩家 _AAA_FirstGoal.txt:616 |
| 29 | 15 | UserSetFlag | 用户旗标 GLO_Arena.txt:119 |
| 30 | 14 | QuestArchive | 任务日志归档 _Global_JournalHelper.txt:486 |
| 31 | 13 | CharacterSetFightMode | 进入/退出战斗姿态 _CRIME_CrimeTriggers.txt:3047 |
| 32 | 13 | CharacterStopCrime | 停止犯罪流程 GLO_Checkpoints.txt:155 |
| 33 | 13 | ItemToInventory | 物品入背包 _GLOBAL_ItemEvents.txt:169 |
| 34 | 12 | CharacterRegisterCrime | 登记犯罪 _CRIME_CrimeTriggers.txt:231 |
| 35 | 12 | CharacterSetRelationFactionToFaction | 阵营-阵营关系 _Greevers_Little_Helpers.txt:909 |
| 36 | 12 | QRY_StartDialog | 启动对话查询（C.1 链）__GLOBAL_Dialogs.txt:201 |
| 37 | 12 | SetFaction | 设阵营 GLO_Arena.txt:571 |
| 38 | 12 | SetVarObject | 角色对象变量 _AdvancedSneakTriggerSpotter.txt:34 |
| 39 | 12 | StartDialog_Internal | 引擎级启动对话 __GLOBAL_Dialogs.txt:205 |
| 40 | 12 | TimerLaunch | 启动计时器 GLO_Arena.txt:1025 |
| 41 | 11 | CharacterLookAt | 看向目标 _CRIME_CrimeTriggers.txt:753 |
| 42 | 11 | CharacterMoveTo | 移动至 _Greevers_Little_Helpers.txt:1220 |
| 43 | 11 | DB_IsPlayer | 入队标记（见 F）GLO_PartyPresets.txt:155 |
| 44 | 11 | DebugBreak | 调试中断 _CRIME_CrimeTriggers.txt:4415 |
| 45 | 11 | QRY_GetFairRand | 公平随机 _Greevers_Little_Helpers.txt:387 |
| 46 | 10 | CharacterDisableAllCrimes | 禁用全部犯罪反应 _CRIME_CrimeTriggers.txt:125 |
| 47 | 9 | CharacterAddAttitudeTowardsPlayer | 加声誉（如 -100）_CRIME_CrimeTriggers.txt:3519 |
| 48 | 9 | CharacterPurgeQueue | 清动作队列 GLO_Follower.txt:16 |
| 49 | 9 | CharacterSetRelationIndivFactionToIndivFaction | 个体-个体关系 _GLO_Shared_PartyMembers.txt:555 |
| 50 | 9 | FireOsirisEvents | 调试：重发挂起事件 GLO_PartyPresets.txt:195 |
| 51 | 9 | MakePlayerActive | 激活为当前玩家角色 GLO_Arena.txt:659 |
| 52 | 9 | TriggerUnregisterForCharacter | 注销触发器 GLO_Follower.txt:112 |
| 53 | 8 | ApplyStatus | 施加状态（见 C.4）GLO_Arena.txt:636 |
| 54 | 8 | CharacterMakePlayer | 设为玩家角色 GLO_PartyPresets.txt:169 |
| 55 | 8 | CharacterSetTemporaryHostileRelation | 临时敌对 _Attitude.txt:16 |
| 56 | 8 | PartySetFlag | 队伍旗标 GLO_Arena.txt:120 |
| 57 | 8 | SetInArena | 竞技场标记 GLO_Arena.txt:570 |
| 58 | 8 | TriggerRegisterForCharacter | 注册触发器 GLO_Follower.txt:103 |
| 59 | 8 | UserClearFlag | 用户旗标清除 GLO_Arena.txt:72 |
| 60 | 7 | CharacterRegisterCrimeWithPosition | 登记犯罪（带位置）_CRIME_CrimeTriggers.txt:245 |
| 61 | 7 | CharacterSetImmortal | 不死开关 GLO_Arena.txt:26 |
| 62 | 7 | DialogSetVariableInt | 设置对话变量（见 C.2）_AAA_FirstGoal.txt:205 |
| 63 | 7 | ItemTemplateAddTo | 模板物品添加 _GLOBAL_ItemEvents.txt:177 |
| 64 | 7 | PlayEffect | 特效 _Global_Procedure.txt:402 |
| 65 | 7 | PlaySound | 音效 _GLO_Shared_Origins.txt:943 |
| 66 | 7 | ProcForceStopDialog | 强制结束对话 Shared_CombatDialogs.txt:18 |
| 67 | 7 | ProcRemoveAllDialogEntriesForSpeaker | 清空该角色的对话条目 GLO_PartyPresets.txt:156 |
| 68 | 6 | CharacterSetRelationFactionToIndivFaction | 阵营-个体关系 _GLO_Shared_PartyMembers.txt:538 |
| 69 | 6 | CharacterSetRelationIndivFactionToFaction | 个体-阵营关系 _GLO_Shared_PartyMembers.txt:537 |
| 70 | 6 | CharacterGiveQuestReward | 任务奖励 _Global_JournalHelper.txt:746 |

（完整 1292 条见 `F:\LarianModLearn\docs\_scratch\then_actions.tsv`。）

### C.1 如何启动对话（完整链路，核心发现）

统一入口是 **`Proc_StartDialog(mode, dialogName, 参与者...)`**（Osiris 侧包装，64 次调用），真实调用链路（`__GLOBAL_Dialogs.txt:136-330`）：

```
Proc_StartDialog(0|1, dialogName, NPC, [player1..player6])
  → QRY_StartDialog(...)
     → QRY_SpeakerIsAvailable(eachSpeaker)     // 未死/未战斗/未占用/未被禁用
     → [mode=0 时] QRY_PrepForInteractiveDialog(speaker)
     → StartDialog_Internal(dialogName, interactiveFlag, speaker..., 1)   // 引擎级函数
  → Proc_DialogFlagSetup(dialogName, speakers...)   // 预置对话旗标
  → CharacterMakeStoryNpc(speaker,1); ProcItemSetInvulnerableForDialog(speaker)
  → DB_HasMetCharactersToCheck(speaker1, speaker2)   // 记录"见过"
```

- **mode=1 自动对话**：`QRY_StartDialog(1, ...)`，仅需说话者可用（如 `_Greevers_Little_Helpers.txt:1586` 等大量调用）。
- **mode=0 交互对话**：额外要求 `QRY_PrepForInteractiveDialog`，并自动 `CharacterMakeStoryNpc`（使 NPC 免疫非剧情伤害）、物品无敌、面对面。
- 实例例（Origins，`F:\LarianModLearn\docs\_scratch\osid_origins\ARX_Barracks.txt:252`）：
  `Proc_StartDialog(0, "ARX_Barracks_InjuredPaladin01", S_ARX_Barrkacks_InjuredPaladin01_dc70b319-aff7-4a0d-abda-45db9063b2f1, _Var2);`
- **停止对话**：`DialogRequestStop(instanceID)`（18 次）或 `ProcForceStopDialog(char)`（7 次）。
- **对话内变量**：`DialogSetVariableInt(dialogInstance, dialogVarName, value)`（`_AAA_FirstGoal.txt:205` 等）——Osiris 在对话运行中改对话状态量，可用于让 LLM 选择后续分支。
- 说话者占用机制：`IsSpeakerReserved(speaker, 0)` 查询 + `QRY_SpeakerIsAvailable`（`QRY_Characters.txt:66-77`），防止角色同时进两个对话。
- "走向并对话"：`ProcCharacterMoveToAndTalk(char, target, dialogName, ...)` → 引擎函数 `CharacterMoveToAndTalk(...)`（`_Global_RunUpAndChat.txt:1-45`），失败/取消事件 `CharacterMoveToAndTalkFailed`、`CharacterMoveToAndTalkRequestDialogFailed`（被攻击、离开区域时触发），请求事件 `CharacterMoveToAndTalkRequestDialog`；另有 `CharacterLeftRegion(char, region)` 事件（`_Global_RunUpAndChat.txt:53`）。

### C.2 如何让角色说话

- **语音 bark（一句话台词）**：`StartVoiceBark(character, barkDialogName)`（`_Greevers_Little_Helpers.txt:1586/1610/1623`、`__GLO_Shovel.txt:209`、`__OneshotDialogs.txt:310`），配合事件 `VoiceBarkStarted/VoiceBarkEnded/VoiceBarkFailed`（`__OneshotDialogs.txt:313-324`）；bark 内容由 `VoiceBarks\GEN_Comments\*.lsj` 定义（Dialog 名 + 标签组）。
- **对话台词**：走 `StartDialog` 的 .lsj 对话资源（TaggedTexts 带种族标签规则）。
- **注意：Shared osid 中没有任何 `Say(`、`DisplayFloatingText`、`Shout` 调用**（全量 grep 无命中）——浮动文本类功能引擎可能存在（待 G 节 SE 文档确认 `Ext.DisplayFloatingText`），但香草 Osiris 层不用它说话，只用 StartVoiceBark + 对话。

### C.3 如何给物品

`ItemToInventory(item, char)`（13）、`ItemTemplateAddTo`（7）、`TransferItemsToCharacter(from,to)`、`MoveAllItemsTo`、`CharacterGiveQuestReward(char, quest, ...)`（`_Global_JournalHelper.txt:746`）、`CharacterGiveReward`（`__PROC.txt:9-11`）、`CreateItemTemplateAtPosition("CONT_..._uuid", x,y,z, newItem)`（`_GLO_Shared_PartyMembers.txt:662`）、`CharacterAddGold(char, amount)`（可负）。监听端事件：`ItemAddedToCharacter` / `ItemTemplateAddedToCharacter` / `CharacterUsedItem` / `CharacterItemEvent`。

### C.4 如何改状态/关系/标签

- 状态：`ApplyStatus(char, "UNCONSCIOUS", -1, 1)`（`GLO_Arena.txt:636`）、`ApplyStatus(char, "PERMANENT_BLIND", -1, 1)`（:1267）、`RemoveStatus`（:1292）、`HasActiveStatus` 查询；`CharacterSetFightMode`、`CharacterSetImmortal`、`CharacterDie`、`CharacterResurrect`。
- 关系：`CharacterSetRelationIndivFactionToIndivFaction(a,b,100)`（同盟）、`CharacterSetTemporaryHostileRelation`（`_Attitude.txt:16`）、`CharacterAddAttitudeTowardsPlayer(npcs, player, -100)`（`"Story Npcs.txt":27`，MakeAttackable 流程）、`SetFaction`。
- 标签/旗标/变量：见 F 节。

---

## D. 时间系统：游戏时间如何进入规则引擎

完整机制在 `_AAA_FirstGoal.txt`：

```
// INITSECTION（_AAA_FirstGoal.txt:5-8）
DB_Time(1, 10, 10);        // 游戏时间：(天, 时, 总小时数) = (1, 10, 10)
DB_HalfHour(20, 20);
DB_GameHour(300000);       // 每游戏小时 = 300000ms = 5 真实分钟（一天 ≈ 2 真实小时）
StartTimeOfDayTimerLoop();

// 循环本体（_AAA_FirstGoal.txt:411-462）
PROC StartTimeOfDayTimerLoop() AND DB_GameHour(_Var1)
  THEN TimerLaunch("TimeOfDay", _Var1);                 // 启动 5 分钟定时器

IF TimerFinished("TimeOfDay")
  AND DB_GameHour(_Var1) AND DB_Time(_, _Var3, _)
  AND IntegerSum(_Var3, 1, _Var5) AND IntegerModulo(_Var5, 24, _Var6)
  THEN TimerLaunch("TimeOfDay", _Var1);  NewHour(_Var6);   // 每到整点触发 NewHour 事件

PROC NewHour(0) AND DB_Time(_Var1, _, _) THEN UpdateTime(_Var1+1, 0);   // 跨天
PROC NewHour(h) [h≠0] AND DB_Time(_Var2, _, _) THEN UpdateTime(_Var2, h);
PROC UpdateTime(day, hour) ... THEN NOT DB_Time(day,hour,total); DB_Time(day, hour, total');  // 推进 DB_Time
```

**结论**：
1. 游戏时间以**引擎定时器事件驱动**进规则引擎：`TimerLaunch("TimeOfDay", ms)` → `TimerFinished("TimeOfDay")` → `NewHour(hour)` 事件广播给所有 goal。
2. 唯一权威时间存储是 **`DB_Time(天, 时, 总小时)`**；`DB_GameHour`（毫秒/小时）、`DB_HalfHour` 为配置。**没有** `GetCurrentTime`/`CurrentTime`/`Wait()`（全量 grep 无命中）——规则引擎里只有 DB_Time + NewHour。
3. 时间被业务使用示例：商人刷新 `GenTradeItems` 要求距上次生成 ≥12 小时（`_Trade.txt:62-66`，读 `DB_Time(_,_,_Var6)` 总小时数）。
4. 短延时统一用计时器：`TimerLaunch(name, ms)`/`TimerFinished(name)` 全局计时器，或 `ProcObjectTimer(char, name, ms)`/`ProcObjectTimerFinished(char, name)` 角色计时器（`_CRIME_CrimeTriggers.txt:973` 起 4500ms 恢复审讯、:1852 1500ms 攻击计时器），`ProcObjectTimerCancel` 可取消。
5. SE 侧若要"每帧/tick"或真实时钟，须走 SE 的 tick 事件（见 G），Osiris 层无此能力。

---

## E. 关系系统

### E.1 Alignment.lsx 全貌（`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\Alignments\Alignment.lsx`，630 行 XML）

三个区域：

1. **Alignments**（12 个阵营实体，行 8-47）：`AnimalBase, Arena, Companion, Evil, GLO_NoxiousBulbs, GameMaster, Generic_Companions, Good, Hero, Neutral, PVP, Story`
2. **Entities**（行 48-287）：把**具体实体名**映射到阵营。例：`Animal_Bear→AnimalBase`…全部动物；`Evil NPC→Evil`、`Good NPC→Good`、`Neutral NPC→Neutral`、`NeutralGoodNPC→Good`、`Story NPC→Story`；玩家槽位 `Hero Player1..8→Hero`；`PVP_1..4→PVP`；`Companion1..9→Companion`；`Generic_Companions_1..4→Generic_Companions`。角色模板的 `Alignment` 属性（characters_cc.lsx 中 `"Hero Player7"`）直接引用这里的实体名。
3. **Relations**（行 288-625）：**全对两两关系矩阵，值 0-100**。要点：
   - `AnimalBase→*` 全 50（中立）
   - `Evil→Companion/Good/Hero` = **0（敌对）**；`Evil→Neutral/NeutralGoodNPC/Story` = 50
   - `Companion→Hero/Good/Story` = **100（同盟）**；`Companion→Evil` = 0
   - `Good→Companion/Hero` = 100，`Good→Evil` = 0；`Hero→Companion/Good/Story` = 100，`Hero→Evil` = 0
   - `Neutral→*` 全 50（含自身）；`PVP→PVP` = 0；`Story→Hero` = 50（剧情阵营对玩家中立偏友好）
   - 方向性：如 `Arena_TeamA→TeamB` = 0（行 331-359 竞技场对抗）。

即：**阵营关系 = 实体级 0-100 矩阵 + 个体级动态覆盖**（引擎函数 `CharacterSetRelation*Faction*` 系列覆盖），0=敌对、50=中立、100=同盟。

### E.2 声誉系统（Attitude / Reputation）

Osiris 中不叫 Reputation 而叫 **Attitude**（`grep Reputation` 在 Shared osid 无命中）：

- **犯罪→态度惩罚表**（`_CRIME_CrimeTriggers.txt:68-82`）：`DB_CrimeAttitudeChange("Murder", -30)`、`"Assault", -20`、`"Steal", -5`、`"PickPocket", -10`、`"Vandalise", -10`、`"Trespassing", -5`、`"UseForbiddenItem", -5`、`"SourceMagic", -5`、`"AttackAnimal", -5` 等——这是"大众对玩家行为的集体看法"。
- **应用**：`ProcCheckAdjustAttitude(玩家, 目击者..., 改变值)` → `CharacterAddAttitudeTowardsPlayer(char, player, delta)`（`_CRIME_CrimeTriggers.txt:3507-3511`）。
- **读取**：`CharacterGetAttitudeTowardsPlayer(char, player, value)`（`_GLO_Shared_Origins.txt:445`）。
- **后果**：低态度 → 战斗（`ProcCrimeCheckIfAttitudeCauseCombat`）；态度低禁对话（`DB_NoLowAttitudeDialog`）；`"Story Npcs.txt"` 的 `MakeAttackable` = `CharacterSetTemporaryHostileRelation + CharacterAddAttitudeTowardsPlayer(-100)`。
- **态度→交易价格**（`_Trade.txt:5-25`）：`DB_DoubleAttitudePrice(态度值, 价格倍率)`：1→2 倍、10→15、15→40、21→100——**声誉直接决定物价**。

### E.3 队友招募规则（Recruit）

- **入队核心**（`_GLO_Shared_PartyMembers.txt:123-147`，`PROC_GLO_PartyMembers_Add`）：
  `CharacterRecruitCharacter(companion, avatar)` + `SetFaction(companion, 默认阵营)` + **`DB_IsPlayer(companion)`（入队=加 DB_IsPlayer 行）** + `CharacterAttachToGroup` + `CharacterAssignToUser(userID, companion)` + 禁用犯罪 + `DB_GLO_PartyMembers_InPartyDialog(companion, dialogName)`（记住入队时对话）。
- **招募对话选择**（`_GLO_Shared_Origins.txt:40-130`）：区域→招募地点→对话，全链路 DB：`DB_OriginRecruitmentLocation_Region(region, npc, pos, state)` → `DB_OriginRecruitmentLocation(npc, pos)` → `QRY_Origin_GetRecruitmentDialog(npc)` → `DB_OriginRecruitmentDialog/DB_NewOriginRecruitmentDialog(npc, dialogName)` → `ProcRemoveAllDialogEntriesForSpeaker(npc)` 然后挂上招募对话；`SetVarFixedString(npc, "currentState", state)` 记录招募状态机。
- **特定伙伴**（Origins 反编译，`osid_origins\GLO_ThePromise_SelfTest.txt:489`）：`CharacterRecruitCharacter(_Var1, CHARACTERGUID_S_Player_Fane_02a77f1f-872b-49ca-91ab-32098c443beb);`——用 **S_ 常量 GUID** 直引伙伴模板（同格式：`CHARACTERGUID_S_Player_Lohse_bb932b13-8ebf-4ab4-aac0-83e6924e4295`，`osid_origins\FTJ_Origins_Lohse.txt:812`）。
- **起源专属反应对话**：`DB_OriginMomentTag(triggerName, "LOHSE", dialogName)` 系统（`osid_origins\FTJ_Origins_Lohse.txt:5-12`）——把"某场景事件 × 某起源角色"映射到专属对话（如 `FTJ_Saheila` 触发 Lohse 专属台词），这是官方"NPC 对特定人物有特定反应"的现成模式，LLM 模组可仿照做"记忆→反应"路由。
- **开除**（`_GLO_Shared_PartyMembers.txt:239-241, 544-556`）：`CharacterDetachFromGroup` + `CharacterRemoveFromParty` + `CharacterMakeNPC` + `SetTag("BLOCK_RESURRECTION")` + 关系互设 -100 + `SetStoryEvent(npc, "GLO_PartyMembers_Kicked")`；开除后回归招募点（`DB_OriginRecruitmentLocation` 复活流程）。
- **恋爱/关系对话**（`_GLOBAL_Shared_RelationshipDialogs.txt:14-103`）：`DB_CompanionAvatarBond(companion, avatar)` 记录绑定；玩家与绑定伙伴距离 <30m 且关系对话未完成时触发 `Proc_RelationshipDialog` → 排队 `DB_RelationshipDialog_Queue` → `TimerLaunch("Test_RelationshipDialog_Queue", 1500)` → `Proc_StartDialog` 关系对话；结束记入 `DB_RelationshipDialogsFinished`；可被全局旗标 `"GLO_DisableRelationshipDialogsPermanently"` 整体关闭（`_GLOBAL_Shared_RelationshipDialogs.txt:9`）。
- **用户级战争/同盟**（`_PlayerAlignments.txt:140-171`）：`UserMakeWar(user1, user2, 0|1)` 事件 ↔ `DB_UserAlign(user1, user2, value)`；`CharacterSetRelationIndivFactionToIndivFaction(playerA, playerB, 100|50|0)`。

---

## F. 持久化机制（可被模组用于 NPC 记忆）

### F.1 DB_ 数据库（Osiris 的事实表）

- 命名规律：`DB_<子系统>_<语义>`，如 `DB_IsPlayer(char)`、`DB_DialogPlayers/DialogNPCs(instance, actor, slot)`、`DB_CombatCharacters`、`DB_OriginRecruitmentLocation_Region(...)`（多级下划线分层）、`DB_GLO_PartyMembers_InPartyDialog`（模组内部按 goal 前缀）。Top 高频（全量统计）：`DB_GLO_CharacterAnimation` 384、`DB_IsPlayer` 298、`DB_NOOP` 191、`DB_Arena_PlayerParticipants` 100、`DB_CombatCharacters` 77、`DB_TutorialInfo` 67、`DB_DialogPlayers/NPCs` 59、`DB_CompanionAvatarBond` 26、`DB_CurrentLevel` 24、`DB_Dead` 23、`DB_Dialogs` 23、`DB_HasMetCharactersToCheck` 19、`DB_CrimeAttitudeChange` 19、`DB_Sees`、`DB_Time`、`DB_CheckPoint`、`DB_HasMet`、`DB_InRegion`、`DB_Followers`、`DB_Subregion` 等（完整见 `_scratch\if_events.tsv`）。
- 语法：INITSECTION 里预置行；THEN 块中**裸 `DB_X(...)` = 插入**，`NOT DB_X(...)` = **删除**；IF 中作为条件（存在性匹配）。查询"是真"用 `DB_NOOP(1)`/`DB_NOOP(0)` 作返回通道；查询返回值写 `DB_QRYRTN_*` 专用库（`QRY_Characters.txt:166-181`）。计数：`SysCount("DB_IsPlayer", 1, _Var1)`（`_GLO_Shared_PartyMembers.txt:42`）。
- **DB_ 行随存档持久化**（Osiris 语义），是 NPC 长期记忆的首选载体（如 `DB_HasMet(charA, charB, "")` 即"两人见过面"的记忆）。

### F.2 旗标（Flag）

五级旗标，命名均为**大写蛇形字符串**（全量提取 TOP：`AVATAR`、`ANIMAL`、`SNEAKING`、`INVISIBLE`、`SUMMON`、`FUGITIVE`、`BLOCK_RESURRECTION`、`PERMANENT_BLIND`、`UNCONSCIOUS`、`GENERIC`、`NOT_MESSING_AROUND`…）：

| 层级 | 函数（事件 = IF 侧） | 例 |
|---|---|---|
| 全局 | `GlobalSetFlag("NAME")` / `GlobalClearFlag` / `GlobalGetFlag("NAME", default)` / IF: `GlobalFlagSet` | `"GEN_SoloPlayer"`（_GLO_Shared_PartyMembers.txt:46）、`"SetupUserAlignments"`（_PlayerAlignments.txt:110）、`"GLO_DisableRelationshipDialogsPermanently"` |
| 对象 | `ObjectSetFlag(obj,"NAME",0)` / `ObjectClearFlag` / `ObjectGetFlag` / IF: `ObjectFlagSet` / `ObjectFlagCleared` | `"GLO_CP_WarningSomeone"`（GLO_Checkpoints.txt:38）、`"GLO_CompanionHasBeenRecruited"`（GLO_PartyPresets.txt:99）、`"OriginRemoveFromPartyAfterDialog"`（:80） |
| 用户 | `UserSetFlag` / `UserClearFlag`（GLO_Arena.txt:119/72） | 玩家账号级 |
| 队伍 | `PartySetFlag`（GLO_Arena.txt:120） | 队伍级 |
| 剧情事件 | `SetStoryEvent(char, "NAME")` + IF: `StoryEvent(char, "NAME")` + 查询 `DB_HasStoryEvent` | `"GLO_PartyMembers_Kicked"`（_GLO_Shared_PartyMembers.txt:569,665）；DB_HasStoryEvent 用于物品（_GLOBAL_ItemEvents.txt:481） |

### F.3 角色变量（每角色键值 namespace）

`SetVarFixedString(char, "key", value)` / `SetVarInteger` / `SetVarObject` / `SetVarFloat` / `SetVarFloat3` + 同名 `GetVar*`。例：招募状态机 `SetVarFixedString(_Var2, "currentState", _Var4)`（`_GLO_Shared_Origins.txt:69`）、犯罪位置 `SetVarFloat3(_Var1, "CrimePos", ...)`（`_CRIME_CrimeTriggers.txt:863`）。**这是"每 NPC 一张 KV 表"的原生机制，适合存 LLM 记忆的紧凑元数据**（上限/性能待验证）。

### F.4 其他

- `TextEventSet("name")`：控制台文本事件（可当调试触发器）；`QuestArchive`：任务日志；Journal 原型在 `F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\Journal\`（quest_prototypes.lsx、questcategory_prototypes.lsx、groups.xml、Goals\、story_header.div）。
- `SavegameLoaded` 事件 + `QRY_VersionIsOlderThan`（`_CRIME_CrimeTriggers.txt:4602`）——SE 可借此做存档版本迁移（`_Global_SavegamePatching.txt` 是官方补丁机制的独立 goal）。

---

## G. SE 接入点：DOS2 Script Extender（Norbyte）Lua API 核实结果

> 核实方法：① 官方 Lua 文档 `https://github.com/Norbyte/ositools/blob/master/Docs/LuaAPIDocs.md`（及 Osiris 新函数文档 `Docs/APIDocs.md`）；② SE 源码树逐目录核对（`ScriptExtender/Lua/Server`、`Lua/Shared/Proxies`、`Lua/Shared`、`Extender/Server`、`LuaScripts/Libs`）。两者交叉，凡源码中不存在的模块直接判"不存在"，避免臆造。
>
> 模块打包约定（文档确认）：Lua 脚本位于 `Mods/<模组UUID>/Story/RawFiles/Lua/`，入口 `BootstrapClient.lua` / `BootstrapServer.lua`，其余文件用 `Ext.Require("相对路径")` 加载（**只能在模块启动期调用**）。游戏侧需 `OsirisExtenderSettings.json`（EnableLuaDebugger / LuaDebuggerPort=9998 / DeveloperMode 等）。SE 保持**多个独立 Lua 状态**（server 一个、每个 client 一个），互不共享全局。
>
> **⚠️ 勘误（2026-08-17 二轮源码级调研后修正）**：本 G 节初版基于 LuaAPIDocs.md + 源码树枚举，其中 3 处结论**被后续按源码（LuaBinding.cpp / Libs/*.inl / ReleaseNotesv56-60）+ 解包故事脚本交叉验证推翻**，见下表标注「★修正」：
> 1. ★`Ext.Events.Tick` **存在**（server+client 均有，`LuaBinding.cpp` 的 `State::OnUpdate` → `ThrowEvent("Tick", TickEvent{.Time=time})`；另有 `Ext.OnNextTick(fn)`）；初版"DOS2SE 无 Tick"错误。
> 2. ★`Ext.IO.SaveFile/LoadFile/Enumerate` **存在**（v60 新增，`Libs/IO.inl`，目录为 `Documents/Larian Studios/Divinity Original Sin 2 Definitive Edition/Osiris Data/`，拒绝 `..` 穿越）；初版"无文件 IO"错误。
> 3. ★原版 Osiris `DisplayText(GUIDSTRING, STRING)` **存在**（解包故事 14 处使用，如 `FTJ_SoulJar_Puzzle.txt`），可经 `Osi.DisplayText(char, text)` 从 Lua 调用（香草传本地化 key，裸字符串行为未验证）；初版"浮动文本无 API"改为"有原生函数待实测"。
> 另确认：Lua 解释器 **5.3.6**；协程支持；`Ext.ModLoader` 不存在（BG3SE 专属）→ DOS2SE 原生 DLL 模组加载**无官方 API**（桥接通道重点转向 Ext.IO 文件桥）；`Ext.Vars.RegisterUserVariable`（v56+）与 `PersistentVars` 并存；文档旧名（`Ext.RegisterOsirisListener`、`Ext.GetCharacter`）为 v56+ 弃用别名，仍可用。

| # | 需求 | 核实结果 | 来源 |
|---|---|---|---|
| 1 | 钩子对话开始/结束 | ✅ **`Ext.RegisterOsirisListener(name, arity, event, handler)`**，event ∈ {"before","after","beforeDelete","afterDelete"}。支持捕获 Osiris 事件、内置查询、数据库、用户 PROC/QRY。用法：`Ext.RegisterOsirisListener("DialogueStarted", 2, "after", function(dialogName, instance) ... end)`（arity 须与事件签名一致；据 osid 反编译 `DialogStarted((STRING),(INTEGER))` 为 2 参数）。会话级引擎事件另用 `Ext.RegisterListener("SessionLoaded", fn)` 等。 | LuaAPIDocs.md |
| 2 | 每帧/tick 回调 | ✅★修正 **`Ext.Events.Tick:Subscribe(function(e) ... end)`**（server+client 均有；事件对象 `e.Time` 为 `GameTime`，源码 `LuaBinding.cpp` `State::OnUpdate` → `ThrowEvent("Tick", ...)`；快捷函数 `Ext.OnNextTick(fn)` 下一 tick 执行一次）。旧式 `Ext.RegisterListener("Tick", fn)` 弃用但可用。低频轮询仍可用 Osiris `TimerLaunch` + `TimerFinished` 心跳（`Ext.Osiris.RegisterListener("TimerFinished", ...)`） | LuaAPIDocs.md + LuaBinding.cpp + BuiltinLibrary.lua |
| 3 | 读角色状态 | ✅ **`Ext.GetCharacter(ref)`**（server 上下文；接受 GUID/NetID/ObjectHandle，找不到返回 nil）。属性：`MyGuid`、`NetID`、`WorldPos`(number[3])、`Stats`、`Dead`、`InParty`、`IsPlayer`、`TeamId`、`StillInCombat`、`InDialog`、`HasOsirisDialog`、`HasDefaultDialog`；血量经 stats 读（如 `char.Vitality` / `char.MaxVitality`）。**声望/职业/态度未文档化** → 用 Osi 查询替代：`Osi.CharacterGetAttitudeTowardsPlayer(char, player)`、`Osi.CharacterGetLevel(char)` 等（Osi 表含全部 Osiris 符号，见 #4）。物品：`Ext.GetItem(ref)`。SE 新增数值函数：`NRD_CharacterGetStat`、`NRD_StatGetInt/Exists`、`NRD_CharacterIterateSkills`（APIDocs.md）。 | LuaAPIDocs.md + APIDocs.md |
| 4 | 调用 Osiris 函数 | ✅ **`Osi.函数名(...)` 全局表**（"Lua server 上下文有一个特殊全局表 `Osi`，包含每一个 Osiris 符号"）：普通调用 `Osi.CharacterResetCooldowns(player)`；查询 `local x,y,z = Osi.GetPosition(char)`；**数据库**：读 `Osi.DB_名称:Get(nil, nil)`（nil=通配，列数须一致）、插入 `Osi.DB_名称(...)`、删除 `Osi.DB_名称:Delete(...)`。**无 `Ext.Osiris.Call`**（那是 BG3 命名，文档与源码均无）。 | LuaAPIDocs.md |
| 5 | HTTP 请求 | ❌ **不存在 `Ext.Net.HttpRequest`**（全仓库 grep `HttpRequest\|WinHttp\|UrlOpen` 无命中；`Ext.Net` 仅是客户端↔服务端消息通道：`BroadcastMessage/PostMessageToClient/PostMessageToServer/NetMessageReceived`）。**桥接通道已改判**：v60 起 **`Ext.IO.SaveFile` 存在**（见 #6）→ **文件轮询桥对 DOS2 可行**（SE Lua 写请求 JSON 到 `Osiris Data`，外部 watcher 进程转发 HTTP）——替代"赌 Lua 标准库"的方案。 | 源码树 + IO.inl |
| 6 | 持久化 | ✅ **`PersistentVars` 表**：`Mods[模块表].PersistentVars`（或 mod 表内直接声明 `PersistentVars = {}`）内容随存档保存，`SessionLoaded` 触发前恢复。✅★修正 **`Ext.IO.SaveFile(path, content)` / `Ext.IO.LoadFile(path)` / `Ext.IO.Enumerate("")` / `IsFile` / `IsDirectory`**（v60 新增；目录 = `Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Osiris Data\`，仅安全相对路径，拒绝 `..`）。✅ **`Ext.Vars.RegisterUserVariable`**（v56+；`{Server=true, Persistent=true, SyncToClient=true...}` 随档）+ `Ext.Vars.RegisterModVariable/GetModVariables/SyncModVariables`。JSON：`Ext.Json.Parse` / `Ext.Json.Stringify`（`Ext.JsonParse/Stringify` 为弃用别名）。`Ext.MonotonicTime()` 毫秒单调钟。 | LuaAPIDocs.md + ReleaseNotesv60.md + Vars.inl |
| 7 | 浮动文本/说话 | ✅★修正 原版 Osiris **`Osi.DisplayText(char, text)`** 存在（解包故事 14 处使用，如 `FTJ_SoulJar_Puzzle.txt`；香草传**本地化 key**，裸字符串行为未验证 ⚠️）。无 `Ext.DisplayFloatingText`（BG3SE 专属）。`Osi.StartVoiceBark(char, barkDialogName)` 一句话台词（香草大量使用）；正式台词走对话系统。 | 解包故事 + 源码树 |
| 8 | 开始/注入对话 | ⚠️ 无 `Ext.StartDialog` / `Ext.Dialog.*`（BG3SE 专属）。可用路径：a) **`Osi.Proc_StartDialog(0\|1, "dialogName", npcGuid, playerGuid...)`**——官方完整校验链（`QRY_SpeakerIsAvailable` 未死/未战斗/10m + `QRY_PrepForInteractiveDialog`，见 C.1）；b) **`Osi.StartDialog_Internal(dialogName, interactiveFlag, 参与者..., 1)`** 引擎内部函数（香草 `__GLOBAL_Dialogs.txt:205` 调用，需运行时验证从 Lua 直调是否过引擎校验）；c) **动态台词注入候选**：对话 .lsj 的 TaggedText 支持变量/旗标引用（`DialogVariables\DialogVariables.lsx`），`DialogSetVariableInt(instance, var, value)` 存在（story 7 处），是否有 `DialogSetVariableString` 类函数待验证。前置：对话须已注册 `DB_Dialogs(char, "dialogName")`。 | 解包故事 + LuaAPIDocs.md |
| 附 | 其他确认 | Lua 解释器版本：文档标题 "Lua API v53" 为 API 修订号；**解释器版本未明示**（大概率 5.3，未确认）。`Ext.Print/PrintError`（调试台）、`Ext.Debug.IsDeveloperMode()`、`Ext.MonotonicTime()`。SE 新增 Osiris 函数统一 `NRD_` 前缀（stats/status/hit/游戏动作/字符串/数学：`NRD_ForLoop`、`NRD_Random`、`NRD_RegexMatch`、`NRD_IsModLoaded` 等，APIDocs.md）。 | 文档 |

**总体结论**：DOS2SE 的 Lua 面比 BG3SE 薄：**没有**网络（Ext.Net 仅联机消息）、对话注入/浮动文本模块（但有原生 `DisplayText` 与完整对话启动链）；**但有**：完整 Osiris 桥（事件钩子 + Osi 全符号调用 + DB 读写）、角色/物品句柄、**tick 回调（★修正）**、**文件 IO（★修正，v60+）**、PersistentVars/UserVars 存档持久化、JSON 编解码。LLM 模组架构应围绕"Osiris 事件 → Lua 处理 → Osi 动作"闭环，把"与 LLM 服务通信"作为独立子系统——**DOS2 首选桥接通道 = Ext.IO 文件轮询桥（v60+，已确认存在，需实测定时/并发行为）**，标准库方案仅作备选。

---

## 对 LLM NPC 模组的意义（候选方案清单）

### 观察输入（Observation → LLM 上下文）

| 类别 | 来源（全部已验证） |
|---|---|
| 对话事件 | `DialogStarted(dialogName, instance)`、`DialogActorJoined`、`DialogEnded`、`AutomatedDialogStarted/Ended`、`VoiceBarkStarted/Ended` |
| 对话内信息 | `DB_DialogName`、`DB_DialogNPCs/Players`、`DialogGetInvolvedPlayer/NPC`、对话 .lsj 的 TaggedTexts（说话内容） |
| 相遇记忆 | `DB_HasMet(charA, charB, "")`（__GLOBAL_Dialogs.txt:47-68 自动记录） |
| 感知 | `CharacterSawCharacter` → `DB_Sees(观察者, 目标)`（_AAA_FirstGoal.txt:464-469） |
| 移动/区域 | `CharacterEnteredTrigger/LeftTrigger`、`RegionStarted/Ended`、`CharacterWentOnStage`、`DB_InRegion`、`GetPosition` |
| 死亡/状态 | `CharacterDied/Dying/KilledBy/Resurrected`、`CharacterStatusApplied/Removed`、`HasActiveStatus` |
| 战斗 | `ObjectEnteredCombat/LeftCombat`、`ObjectTurnStarted`、`AttackedByObject`、`DB_CombatCharacters` |
| 物品 | `ItemAddedToCharacter`、`CharacterUsedItem`、`CharacterItemEvent`、`ItemIsInCharacterInventory` |
| 犯罪/行为评价 | `CharacterOnCrimeSensibleActionNotification`、`OnCrimeResolved`、`DB_CrimeAttitudeChange` 表、`CharacterGetAttitudeTowardsPlayer` |
| 时间 | `NewHour(hour)` 事件、`DB_Time(day, hour, totalHours)` |
| 世界事件 | `StoryEvent`、`GlobalFlagSet`、`ObjectFlagSet`、`TimerFinished` |
| 玩家身份 | `CharacterGetReservedUserID`、`CharacterIsPlayer`、`IsTagged("AVATAR")`、`UserMakeWar` |
| 基础数值 | stats 模板（Character.txt + 关卡 S_ 模板）、`CharacterGetLevel`、`CharacterGetHitpointsPercentage`、Archetype |

### 记忆键（Memory Key）候选

1. **SE 侧大记忆**：`PersistentVars` 表（随存档保存、SessionLoaded 前恢复）存对话历史/向量摘要等大文本，JSON 用 `Ext.JsonStringify/JsonParse` 序列化（G 节 #6）。
2. **Osiris 侧 DB 表**（规则引擎可见、随存档持久）：`Osi.DB_LLM_Memory:Insert(npc, key, value)` 风格（仿 `DB_HasMet`/`DB_GLO_PartyMembers_InPartyDialog` 命名）；"首次见面"天然用 `DB_HasMet`（引擎自动记录）。
3. **角色变量**（每 NPC KV）：`Osi.SetVarFixedString(npc, "LLM_LastTopic", ...)` 仿 `"currentState"`。
4. **对象旗标**：`Osi.ObjectSetFlag(npc, "LLM_Quest_<Name>", 0)` 仿 `"GLO_CompanionHasBeenRecruited"`。
5. **StoryEvent**：`Osi.SetStoryEvent(npc, "LLM_Event_<Name>")` 仿 `"GLO_PartyMembers_Kicked"`。

### 动作面（LLM 决策 → 引擎动作）

- **说话**：SE 侧 `Osi.Proc_StartDialog(0, dialogName, npc, player)`（完整校验链）或 `Osi.StartVoiceBark(npc, bark)`（一句话）；动态台词候选=既有对话模板 + 对话变量注入（G 节 #8c，待验证）。
- **对话控制**：`Osi.DialogRequestStop(instance)`、`Osi.ProcForceStopDialog`、`Osi.DialogSetVariableInt(instance, var, value)`。
- **态度/关系**：`Osi.CharacterAddAttitudeTowardsPlayer`、`Osi.CharacterSetRelationIndivFactionToIndivFaction(a,b,0..100)`、`Osi.CharacterSetTemporaryHostileRelation`、`Osi.SetFaction`。
- **状态**：`Osi.ApplyStatus/RemoveStatus`、`Osi.CharacterSetImmortal`、`Osi.CharacterResurrect/CharacterDie`、`Osi.SetOnStage`、`Osi.TeleportTo`、`Osi.CharacterMoveTo`。
- **物品**：`Osi.ItemToInventory`、`Osi.ItemTemplateAddTo`、`Osi.CharacterAddGold`、`Osi.TransferItemsToCharacter`。
- **标记**：`Osi.SetTag/ClearTag`、`Osi.ObjectSetFlag`、`Osi.GlobalSetFlag`、`Osi.SetStoryEvent`、`Osi.SetHasDialog`。
- **表现**：`Osi.PlayAnimation`、`Osi.PlaySound`、`Osi.PlayEffect`、`Osi.CharacterLookAt`、`Osi.ProcFaceCharacter`、`Osi.DebugText`。
- **计时**：`Osi.TimerLaunch` + `Ext.RegisterOsirisListener("TimerFinished", ...)` 心跳（SE 无帧回调，见 G 节 #2）。
- **招募**：`Osi.CharacterRecruitCharacter` + `Osi.DB_IsPlayer(...)`（入队标记）。

### 事件触发器（LLM 唤醒条件）候选

`Ext.RegisterOsirisListener` 钩：`DialogStarted/DialogEnded/AutomatedDialogStarted/AutomatedDialogEnded/VoiceBarkStarted/VoiceBarkEnded`、`CharacterEnteredTrigger/CharacterLeftTrigger`、`CharacterMoveToAndTalkRequestDialog`、`CharacterSawCharacter`、`CharacterDied/CharacterKilledBy`、`ObjectEnteredCombat/ObjectLeftCombat`、`ItemAddedToCharacter`、`CharacterUsedItem`、`NewHour`（游戏整点）、`TimerFinished`（自定义心跳）、`SavegameLoaded`（恢复记忆）、`StoryEvent`、`TextEventSet`（调试指令）。

### 架构要点（SE 侧能力约束）

- SE Lua **无 HTTP/文件 IO/帧回调/浮动文本/对话注入 API**（G 节核实）；"LLM 通信子系统"必须外置或依赖标准库（待运行时实测），Osiris 桥是唯一全功能通道。

## 待验证问题

1. **S_ 角色对话的确切打包位置与格式**：确认存在于关卡 .lsf 内（当前解包未见关卡文件）；后续需用 LSLib 解一个关卡样本验证对话节点结构、以及 SE 读取/注入对话的可行路径。
2. **DisplayFloatingText / Say 类函数**：Shared osid 无任何调用；SE 官方文档与源码均无 `Ext.DisplayFloatingText`；需在运行时枚举引擎导出表确认是否存在原生函数。
3. **Attitude 与 Faction Relation 的关系换算**：-100 的 `CharacterAddAttitudeTowardsPlayer` 与 0-100 relation 的联动规则（"Story Npcs.txt" MakeAttackable 三连：MakeStoryNpc(0) + TemporaryHostileRelation + Attitude-100）；`DB_NoLowAttitudeDialog` 的阈值。
4. **DB_/角色变量的持久化边界**：DB_ 行随存档；角色变量、StoryEvent、五级 flag 各自的存档/读档行为需在游戏内实测（SE 可查询存档内容验证）。
5. **SE 侧运行时验证项**（文档之外的实测清单）：
   - `Osi.StartDialog_Internal(...)` 与 `Osi.Proc_StartDialog(...)` 能否从 Lua 直调并过引擎校验；
   - Lua 环境是否开放标准库 `os`/`io`/`socket`（HTTP 方案可行性第一关）；`io.popen` 是否可用；
   - `Ext.RegisterOsirisListener` 对 `DialogueStarted/DialogueEnded/TimerFinished/NewHour` 的实际钩取（arity 匹配）；
   - 是否有引擎原生 `DisplayFloatingText`、`DialogSetVariableString` 类函数（对话变量注入台词）；
   - `Ext.GetCharacter` 的 `Stats` 表字段全集（读声望/职业的替代查询）。
6. **Osiris 规则注入方式**：新增 goal（story.div）由模组 .pak 加载的打包流程（Story\story.div + story.div.osi 编译），以及 SE 的 `Ext.Osiris.RegisterListener` 能否完全替代自定义 goal。
7. **性能**：DB_ 查询/`TimerFinished` 心跳频率上限；`QRY_SpeakerIsAvailable` 系列在大量 LLM NPC 下的负载；`Ext.RegisterOsirisListener` 回调每事件触发开销。
8. **`CharacterMoveToAndTalkRequestDialog` 的触发条件**（`_Global_RunUpAndChat.txt` 完整规则）与 `SetHasDialog(char, 0)` 的交互。
9. **多玩家/竞技场隔离**：`IsInArena`、`DB_UserAlign`、`ProcFixPlayerAlignments` 对单机 LLM 模组的影响面。
10. **`FireOsirisEvents`**（GLO_PartyPresets.txt:195）具体语义——疑似调试用"重发挂起事件"，SE 侧是否有等价物。

---

### 附录：关键文件路径速查

- 规则引擎全量文本：`F:\LarianModLearn\extracted\DOS2\Mods\Shared\Story\osid\`（68 goals）
- 对话管线（启动/停止/HasMet）：`osid\__GLOBAL_Dialogs.txt`
- 说话者可用性/预留：`osid\QRY_Characters.txt`
- 招募/开除/入队：`osid\_GLO_Shared_PartyMembers.txt`、`osid\_GLO_Shared_Origins.txt`、`_scratch\osid_origins\`（起源模组，含 Sebille/Loshe/Fane 具体规则）
- 时间系统：`osid\_AAA_FirstGoal.txt`（5-8 行初始化，411-462 行循环）
- 声誉/犯罪态度：`osid\_CRIME_CrimeTriggers.txt`（68-82 态度表）、`osid\_Trade.txt`（态度→价格）
- 恋爱关系对话：`osid\_GLOBAL_Shared_RelationshipDialogs.txt`
- 阵营矩阵：`Mods\Shared\Story\Alignments\Alignment.lsx`
- 基础数值：`Public\Shared\Stats\Generated\Data\Character.txt`
- 角色模板结构：`_scratch\characters_cc.lsx`（Divine 转换自 `Mods\Shared\Globals\SYS_Character_Creation_A\Characters\_merged.lsf`）
- 战术 AI：`Public\Shared\AI\Archetypes\*.txt`、`combos.txt`
- 角色脚本：`Public\Shared\Scripts\DefaultCharacter.charScript` 等 258 个
- 事件/动作全表：`F:\LarianModLearn\docs\_scratch\if_events.tsv`（648 条）、`then_actions.tsv`（1292 条）

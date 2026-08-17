# BG3 游戏结构深度分析报告
## ——为"大模型驱动 NPC AI"模组的前置研究

- 日期：2026-08-17
- 数据来源：`f:\LarianModLearn\extracted\BG3\`（BG3 游戏 pak 定向解包）
  - 反编译 Osiris goals：`Mods\Gustav\Story\osid\`（382 个）、`Mods\GustavDev\Story\osid\`（935 个）、`Mods\SharedDev\Story\osid\`（135 个），合计 1452 个 goal，约 35 万行语句
  - 对话：`Mods\Gustav\Story\Dialogs\`（.lsj）、`Mods\GustavDev\Story\DialogsBinary\`（.lsf）
  - 数值：`Public\Gustav\Stats\Generated\Data\Character.txt` 等
  - 时间线：`Public\Gustav\Timeline\`、`Public\GustavDev\Timeline\`
  - 好感：`Public\GustavDev\ApprovalRatings\`（2102 个 Reaction 文件，本身已是 .lsx XML）
  - flag：`Public\Gustav\Flags\`（UUID 命名的 .lsf）
  - 行为树（anubis）：`Scripts\anubis\`（config .anc / module .anm / node .ann）与 `Mods\Shared\Scripts\anubis\`
- 分析方法：状态机 awk 对全部 osid 文本分类（IF 条件 / THEN 动作 / INITSECTION 种子），按"引擎事件 = 非 DB_/QRY_/PROC_ 前缀的条件名""引擎动作 = 非 DB_/PROC_ 前缀的动作名"归类；Divine.exe 转换 6 个 .lsf 样本为 .lsx；子代理联网调研 BG3SE API（源码+官方文档+社区镜像）。

---

## A. NPC 系统

### A1. 数值定义：Character.txt

文件：`f:\LarianModLearn\extracted\BG3\Public\Gustav\Stats\Generated\Data\Character.txt`（1883 行，另有 GustavDev/Shared/Honour/SharedDev 四个同名文件）。格式为 `new entry "条目名" / type "Character" / using "基类" / data "字段" "值"`。

典型 NPC 条目（节选）：

- 提夫林领袖 Zevlor（`DEN_TieflingLeader`，同上文件）：
  ```
  new entry "DEN_TieflingLeader"
  type "Character"
  using "Tiefling_Melee"
  data "Strength" "16" ... data "Charisma" "17"
  data "Vitality" "36"
  data "XPReward" "4ee02692-eb98-43a6-803f-2da645364568"
  data "SpellCastingAbility" "Charisma"
  data "ActionResources" "ActionPoint:1;BonusActionPoint:1;Movement:9;ReactionActionPoint:1;Interrupt_HellishRebukeTiefling_Charge:1"
  data "Passives" "AttackOfOpportunity;DarknessRules;Tiefling_HellishResistance;FightingStyle_Defense;Tough"
  data "Progressions" "8726b2c4-edc0-4905-b82f-60a4baba0733"   (职业/等级成长表 GUID)
  data "Proficiency Group" "MartialWeapons;MediumArmor;SimpleWeapons;LightArmor;HeavyArmor"
  ```
- 营地小孩 Mirkon（`DEN_Mirkon`）：`using "Tiefling_Child"` + `DifficultyStatuses`（按难度给 BUFF）。
- 教学关角色（`TUT_GithGuide`、`TUT_Elf_Victim_Spellcaster`）：`using "POC_Player_Fighter"`、`data "Passives" "FeyAncestry;DarknessRules;Darkvision"`。

**实例↔数值的关联**：地图上的 NPC 实例（等级文件中放置）引用 Character.txt 条目名；Osiris 侧的模板常量为带 GUID 的 `S_` 名。证据：`Mods\Gustav\Story\osid\GLO_Journal.txt:82` 中 `DB_GLO_TadpoleQuest_Druid_HalsinLeaderEntries(S_DEN_TieflingLeader_475200ee-cc3c-4dbe-84b1-1820c02ea26a, ...)` —— 同一 NPC（Zevlor）在 stats 侧叫 `DEN_TieflingLeader`、在 Osiris 侧叫 `S_DEN_TieflingLeader_<uuid>`。

### A2. Osiris 实例常量（S_ 前缀）

- 反编译文本中所有角色/触发区/物件都以**具名 GUID 常量**出现，如 `S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679`。该名字由 StoryDecompiler 从编译期常量表内联而来；**解包文本里没有常量定义段**（grep `S_Player_ShadowHeart_... = ` 零命中，只有使用处），映射关系藏在编译后的 .osi 数据里。对模组而言：**直接用 UUID 字符串即可**（见 G 节，SE 的 GUIDSTRING 参数同时接受 UUID 与句柄）。
- 命名规律：`S_Player_<Origin角色名>_<uuid>`（起源角色）；`S_<区域>_<物件/地点>_<uuid>`（S_CHA_ChapelBox、S_DEN_ShadowHeartSphere）；`S_<区域>_<NPC>_SUB_<uuid>`（副本/替身，如 `S_DEN_TieflingLeader_SUB_f667e6fe-...`，Act1a_Camp.txt:37）。
- **该 GUID 与对话文件 speakerlist 中的 GUID 一致**，证据：`Dialogs\Companions\Astarion_Recruitment.lsj` 的 speakerlist 中 index 0 → `list: c7c13742-bacd-460a-8f65-f864fe41f255`，与 osid 中 `S_Player_Astarion_c7c13742-bacd-460a-8f65-f864fe41f255` 完全相同。因此**角色实例 GUID 是贯穿 stats/对话/规则/行为树四个系统的统一主键**。

### A3. 对话文件命名与结构

- 目录 `Mods\Gustav\Story\Dialogs\` 下按区域分子目录（Act1 下再分 Chapel/DEN/Forest/Goblin/...；另有 Companions/Generics/Global/Camp 等），文件命名 `<NPC>_<话题>.lsj`：如 `Astarion_Recruitment.lsj`、`Laezel_Recruitment_Crash.lsj`、`GLO_ShadowHeart_AD_SuccessfulCombat.lsj`；GustavDev 的 `DialogsBinary\` 下同名 .lsf 二进制（同一套对话的另一份拷贝）。
- .lsj 结构（`Dialogs\Companions\Astarion_Recruitment.lsj`）：
  - 顶层：`UUID`（对话资源 GUID，供 DialogStarted/QRY_StartDialog 引用）、`TimelineId`（指向时间线资源的 GUID，如 `7586fe9c-e55f-6413-579e-6c53789db648`）、`category`（如 "Companion Dialog"）、`DefaultAddressedSpeakers`、`DefaultSpeakerIndex`
  - `nodes` → `RootNodes`（树节点）；节点含 `GroupID/GroupIndex`、`speaker`（int32 索引）、`TaggedTexts`（行文本，`LineId` 为文本 GUID，`TagText` 内含字幕文本）、`GameData`（LookAts、AiPersonalities 等）、`setflags`（**对话节点可设置 flag**——入队/离队即由此驱动，见 E 节）
  - `speakerlist`：`SpeakerMappingId` + `index` + `list`（**角色实例 GUID**）；`IsPeanutSpeaker` 表示旁听角色（多人对话吃瓜位）
- 说话文本本身存放在本地化文件（`Localization`），对话文件通过 `LineId` GUID 引用。

### A4. NPC 行为：anubis 行为树（重点）

BG3 的 NPC"AI"是 Lua 行为树引擎 anubis，全部在 `Scripts\anubis\`：

- **config（.anc）**：每个 NPC/模板一个配置，指定行为根。`Mods\Shared\Scripts\anubis\config\DefaultCharacter.anc`：
  ```
  game.configs.DefaultCharacter = Config{
      root=StateRef{game.roots.DefaultCharacter,
          combat = StateRef{game.states.DefaultCombat},
          combatCowerState = StateRef{game.states.CombatCower},
          genericBehaviours = StateRef{game.states.CrimesHumanoid},
          idle = StateRef{game.states.Dummy},
      }
  }
  ```
  具体 NPC 可覆盖 idle 状态：`Scripts\anubis\config\Act1\DEN\DEN_AdventurerLeader.anc` 把 `idle` 换成 `game.states.DEN_AdventurerLeader`。
- **state（.ann）**：`game.states.X = State{function() ... end}`，内部是 `Selector / ImmediateSelector / Proxy / Sequence` 节点树 + `Valid()` 条件 + `params` 参数声明（`EParamType.State/String/...`）。例：`node\Act1\CAMP\CAMP_Astarion.ann`（阿斯塔隆营地行为，用 `Flag("GLO_CAMP_NightMode_<uuid>")` 读昼夜）、`node\Act2\Town\TWN_MasonsGuild_Pusher.ann`。
- **module（.anm）**：`local m = AnubisModule()`，`m.action.X = function(entity,...)` 定义可复用动作；内部可调用引擎函数（MoveTo、Wander、PlayAnimation、LookAtEntity、Sleep、StartAutomatedDialog、UseSpell、SetEntityEvent、GetActiveCharacters、GetDistanceTo、CanSee、HasLineOfSight、IsTagged、DebugText、RequestPassiveRoll 等），且有 `try/catch`（`error.MovementFailed`、`error.UseSpellFailed`）。例：`Scripts\anubis\module\gustav\Act1\TollhouseRefugee.anm`、`ZhentShipment.anm`。
- **osid↔anubis 桥**：`Mods\Gustav\Story\osid\__GLOBAL_AnubisConfigs.txt` 定义 `PROC_SetAnubisConfig(char, config)` → `DEV_EnableAnubis(_Var1, _Var2)`（Osiris 直接给角色指派行为配置）；`GetAnubisConfig(char, config)` 可查询当前配置。
- 实体对象模型：Lua 侧 `entity.Character.IsDead`、`entity.OnStage`、`entity.Position`、`entity.Name`、`item.Item.IsDestroyed` 等。

### A5. "LLM 观察一个 NPC"所需数据（候选清单）

| 数据 | 获取途径 | 证据 |
|---|---|---|
| 实例 GUID | 对话 speakerlist / S_ 常量 / 地图 | A2、A3 |
| stats 条目名 | `Osi.GetStatString(char)` → `Ext.Stats.Get()`（六维、等级、HP 上限） | G 节 |
| 位置 | `Osi.GetPosition(char)`；osid `GetPosition` 事件参数 | G3；osid 例 Act1_DEN_DruidAttack.txt:383 |
| 存活/状态 | `Osi.HasActiveStatus`；事件 Died/Dying/Resurrected；`StatusApplied/Removed` | B 节表 |
| 好感 | `Osi.GetApprovalRating(owner, target)`；`DB_ApprovalRating` | G3；E 节 |
| 行为配置 | `Osi.GetAnubisConfig` / `DEV_EnableAnubis` | A4 |
| 在队/入队 | `DB_PartyMembers` / `DB_Players` / `ORI_*_State_IsInParty` flag | E3 |
| 对话状态 | `DB_Dialogs(char, dialog)`、`DialogStarted/Ended` 事件 | B 节 |
| flag 状态 | `Osi.GetFlag(flag, char)`；anubis `Flag()`/`GetFlag` | F 节 |

---

## B. 事件系统

### B1. osid 事件统计方法

用状态机 awk 扫描全部 1452 个 goal：`IF`/`AND`/`OR`/`NOT` 后的条件行计为"条件"，`THEN` 后的行计为"动作"，`INITSECTION` 计为"种子"。条件中非 `DB_/QRY_/PROC_` 前缀的即**引擎事件**。全库共分类 349,646 行语句。TOP-100 引擎事件（次数为全库条件出现次数，例子为首次出现位置，文件路径相对 `extracted\BG3\Mods\`）：

| # | 事件名 | 次数 | 例子(文件:行) | 示例片段 |
|---|---|---|---|---|
| 1 | `FlagSet` | 5156 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:24` | `FlagSet(CRA_HarperBooster_Event_RockMovable_731541b8-b2d0-4477-b0fd-132bec81e83f,` |
| 2 | `TimerFinished` | 744 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:30` | `TimerFinished("CRA_HarperRock_Movable")` |
| 3 | `WentOnStage` | 215 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:41` | `WentOnStage(S_CRA_ScaredBoar_e352fae8-f49a-4f1d-b131-ea10af7591c9,` |
| 4 | `EntityEvent` | 1897 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:46` | `EntityEvent(S_CRA_ScaredBoar_e352fae8-f49a-4f1d-b131-ea10af7591c9,` |
| 5 | `GameBookInterfaceClosed` | 157 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:65` | `GameBookInterfaceClosed(S_CRA_HarperScroll_0203a6ff-5dbe-40d4-84b2-738e846a9543,` |
| 6 | `IsInTrigger` | 819 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:74` | `IsInTrigger(_Var2,` |
| 7 | `TextEvent` | 2403 | `Gustav/Story/osid/Act1_CRA_Boosters.txt:81` | `TextEvent("TUT_Helm_AddDeadGuide")` |
| 8 | `DialogEnded` | 2176 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:36` | `DialogEnded(Astarion_Recruitment_56bc2c0c-f02d-ec4c-ea0b-e7ceac19779a,` |
| 9 | `GetFlag` | 1898 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:52` | `GetFlag(ORI_Astarion_HasMet_7c64a986-6bfd-ae42-ba29-b35b7f2cd6cf,` |
| 10 | `DialogStarted` | 572 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:59` | `DialogStarted(Astarion_Recruitment_56bc2c0c-f02d-ec4c-ea0b-e7ceac19779a,` |
| 11 | `Died` | 199 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:70` | `Died(S_Player_Astarion_c7c13742-bacd-460a-8f65-f864fe41f255)` |
| 12 | `StatusApplied` | 645 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:81` | `StatusApplied(S_Player_Astarion_c7c13742-bacd-460a-8f65-f864fe41f255,` |
| 13 | `CharacterGetOwner` | 183 | `Gustav/Story/osid/Act1_CRA_AstarionRecruitment.txt:83` | `CharacterGetOwner(_Var1,` |
| 14 | `GetFaction` | 423 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:139` | `GetFaction(_Var1,` |
| 15 | `AttackedBy` | 343 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:144` | `AttackedBy((CHARACTER)_Var1,` |
| 16 | `TurnStarted` | 308 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:165` | `TurnStarted((CHARACTER)_Var1)` |
| 17 | `IsTagged` | 1119 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:177` | `IsTagged(_Var3,` |
| 18 | `AutomatedDialogStarted` | 98 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:184` | `AutomatedDialogStarted(CRA_Escape_PAD_FirstIntellectDevourerCombat_6ec32daf-8cd3-d721-d2f4-e03f73472a15,` |
| 19 | `QuestUpdateIsUnlocked` | 587 | `Gustav/Story/osid/Act1_DEN_AdventurersQuest.txt:32` | `QuestUpdateIsUnlocked(_Var1,` |
| 20 | `LeftTrigger` | 516 | `Gustav/Story/osid/Act1_DEN_AdventurersQuest.txt:63` | `LeftTrigger((CHARACTER)_Var1,` |
| 21 | `AutomatedDialogEnded` | 375 | `Gustav/Story/osid/Act1_DEN_AdventurersQuest.txt:170` | `AutomatedDialogEnded(DEN_AdventurersQuest_AD_LeavingCorpses_1810594b-3b36-7eee-4cb7-03afac0cb99b,` |
| 22 | `EnteredTrigger` | 1023 | `Gustav/Story/osid/Act1_DEN_AdventurersQuest.txt:200` | `EnteredTrigger((CHARACTER)_Var1,` |
| 23 | `ObjectTimerFinished` | 1132 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:50` | `ObjectTimerFinished((CHARACTER)_Var1,` |
| 24 | `DialogRequestFailed` | 95 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:106` | `DialogRequestFailed(CRA_Crash_c6870e25-3c45-386c-0264-965c48731036,` |
| 25 | `GetReservedUserID` | 293 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:151` | `GetReservedUserID(_Var1,` |
| 26 | `Random` | 190 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:184` | `Random(1500,` |
| 27 | `IntegerSum` | 522 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:186` | `IntegerSum(_Var2,` |
| 28 | `StatusRemoved` | 573 | `Gustav/Story/osid/Act1_CRA_Escape_Mindflayer.txt:86` | `StatusRemoved(S_CRA_Escape_Mindflayer_d5385cd0-f371-43dc-a0a2-50381fc50ea4,` |
| 29 | `KilledBy` | 131 | `Gustav/Story/osid/Act1_CRA_Escape_Mindflayer.txt:108` | `KilledBy(S_CRA_Escape_Mindflayer_d5385cd0-f371-43dc-a0a2-50381fc50ea4,` |
| 30 | `IsDestroyed` | 154 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:174` | `IsDestroyed(S_DEN_StorageDoor_e2911d4f-2b43-48e4-a1c2-5c4cc53bae8d,` |
| 31 | `IsLocked` | 137 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:176` | `IsLocked(S_DEN_StorageDoor_e2911d4f-2b43-48e4-a1c2-5c4cc53bae8d,` |
| 32 | `CrimeGetNewID` | 180 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:364` | `CrimeGetNewID(_Var5)` |
| 33 | `GetPosition` | 629 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:383` | `GetPosition(S_DEN_SilvanusIdol_a841d36c-9a00-4a26-943e-c0af6895bb16,` |
| 34 | `CharacterOnCrimeSensibleActionNotification` | 94 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:489` | `CharacterOnCrimeSensibleActionNotification((CHARACTER)_Var1,` |
| 35 | `IsEnemy` | 120 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:524` | `IsEnemy(_Var2,` |
| 36 | `CrimeGetType` | 143 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:549` | `CrimeGetType(_Var3,` |
| 37 | `GetDistanceTo` | 342 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:760` | `GetDistanceTo(_Var1,` |
| 38 | `EnteredCombat` | 440 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:912` | `EnteredCombat((CHARACTER)_Var1,` |
| 39 | `CombatEnded` | 246 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:962` | `CombatEnded((GUIDSTRING)_Var1)` |
| 40 | `CanSee` | 139 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1000` | `CanSee(_Var2,` |
| 41 | `SysCount` | 225 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1426` | `SysCount("DB_DEN_DruidAttack_DruidsMovingToPosition",` |
| 42 | `IsOpened` | 95 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1579` | `IsOpened(S_DEN_PrisonMainDoor_c166068b-38dd-4891-b811-c4b2fde19e1c,` |
| 43 | `GetRelation` | 105 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1655` | `GetRelation(_Var4,` |
| 44 | `DestroyedBy` | 256 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1701` | `DestroyedBy(S_DEN_PrisonMainDoor_c166068b-38dd-4891-b811-c4b2fde19e1c,` |
| 45 | `Unlocked` | 102 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:1710` | `Unlocked(S_DEN_PrisonMainDoor_c166068b-38dd-4891-b811-c4b2fde19e1c,` |
| 46 | `GetHostCharacter` | 1044 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:2199` | `GetHostCharacter(_Var1)` |
| 47 | `IsOnStage` | 347 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:2241` | `IsOnStage(_Var1,` |
| 48 | `UseStarted` | 589 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:146` | `UseStarted((CHARACTER)_Var1,` |
| 49 | `UseFinished` | 250 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:155` | `UseFinished((CHARACTER)_Var1,` |
| 50 | `GetEquippedItem` | 122 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:379` | `GetEquippedItem(S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679,` |
| 51 | `GetTemplate` | 149 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:381` | `GetTemplate(_Var3,` |
| 52 | `FlagCleared` | 302 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:530` | `FlagCleared(CRA_ShadowheartRecruitment_State_Unconscious_a461603e-1423-4c54-a270-82f38ee470af,` |
| 53 | `LeftCombat` | 237 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:544` | `LeftCombat(S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679,` |
| 54 | `HasActiveStatus` | 884 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:556` | `HasActiveStatus(S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679,` |
| 55 | `Dying` | 125 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:184` | `Dying(S_DEN_WoundedBird_200bc56e-f3e1-445b-8b75-a5ddb541e123)` |
| 56 | `Opened` | 107 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:346` | `Opened((ITEM)_Var1)` |
| 57 | `Exists` | 331 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:855` | `Exists(_Var1,` |
| 58 | `IsInInventory` | 131 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:1109` | `IsInInventory(S_DEN_AntidoteRecipeBook_6557e2a7-ee82-4c5a-a26b-9056e4eb03df,` |
| 59 | `RemovedFrom` | 87 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:1117` | `RemovedFrom((ITEM)_Var1,` |
| 60 | `IsInInventoryOf` | 173 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:1160` | `IsInInventoryOf(S_DEN_Antidote_3d02e275-1530-455c-9d58-bfac847e105a,` |
| 61 | `DialogActorLeft` | 127 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1152` | `DialogActorLeft(DEN_AttackOnDen_LairDoor_bdb3218d-bd21-d32a-e5f7-8df82e2e37a6,` |
| 62 | `SwitchedCombat` | 86 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1383` | `SwitchedCombat((CHARACTER)_Var1,` |
| 63 | `GetCombatGroupID` | 97 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1427` | `GetCombatGroupID(_Var1,` |
| 64 | `RelationChanged` | 98 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:2836` | `RelationChanged(ACT1_DEN_AttackOnDen_NPC_08f28bce-a261-35e2-9914-6aa8b3eea155,` |
| 65 | `AddedTo` | 317 | `Gustav/Story/osid/Act1_DEN_Graves.txt:255` | `AddedTo(S_DEN_KanonBag_34f15197-44e7-4e5c-afd4-11a3c6b6c1b4,` |
| 66 | `DualEntityEvent` | 210 | `Gustav/Story/osid/Act1_DEN_AttackOnDen_Combat.txt:258` | `DualEntityEvent((CHARACTER)_Var1,` |
| 67 | `CastedSpell` | 199 | `Gustav/Story/osid/Act1_DEN_AttackOnDen_Combat.txt:472` | `CastedSpell((CHARACTER)_Var1,` |
| 68 | `IsCharacter` | 341 | `Gustav/Story/osid/Act1_DEN_AttackOnDen_Combat.txt:476` | `IsCharacter(_Var1,` |
| 69 | `QuestIsAccepted` | 96 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:64` | `QuestIsAccepted(_Var1,` |
| 70 | `AutomatedDialogRequestFailed` | 98 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:271` | `AutomatedDialogRequestFailed(DEN_CapturedGoblin_AD_b1b82bdf-7608-d578-e71d-80e1ae6e0924,` |
| 71 | `GetClosestAlivePlayer` | 103 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:539` | `GetClosestAlivePlayer(S_DEN_CapturedGoblin_783d7572-a846-455f-b686-247a95263ebb,` |
| 72 | `IsSpeakerReserved` | 123 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:745` | `IsSpeakerReserved(S_DEN_Griefling_7ce0afc2-e8f2-4f2e-82d8-27df98acc3d8,` |
| 73 | `HitpointsChanged` | 86 | `Gustav/Story/osid/Act1_DEN_GoblinScouts.txt:360` | `HitpointsChanged(S_DEN_ScoutCaptive_f5b5819f-1636-4f2e-82bb-709522cc399f,` |
| 74 | `IsDead` | 179 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:151` | `IsDead(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12,` |
| 75 | `UsingSpellOnTarget` | 95 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:329` | `UsingSpellOnTarget(_,` |
| 76 | `Resurrected` | 124 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:352` | `Resurrected(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12)` |
| 77 | `GetOwner` | 106 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:1062` | `GetOwner(S_CHA_CageBottom_S_LT_PLT_CHA_CageBottom_106fde0f-c09d-8920-3204-dc169a0ef008,` |
| 78 | `QuestUpdateUnlocked` | 170 | `Gustav/Story/osid/Act1_DEN_DruidLair.txt:449` | `QuestUpdateUnlocked((CHARACTER)_Var1,` |
| 79 | `HasAppliedStatus` | 192 | `Gustav/Story/osid/Act1_DEN_Misc.txt:960` | `HasAppliedStatus(_Var1,` |
| 80 | `IntegerSubtract` | 205 | `Gustav/Story/osid/Act1_DEN_HarpyMeal.txt:510` | `IntegerSubtract(_Var7,` |
| 81 | `HasActiveStatusWithGroup` | 87 | `Gustav/Story/osid/Act1_DEN_RaidingParty.txt:1152` | `HasActiveStatusWithGroup(S_DEN_GoblinRaider_Captain_22d80f21-7f31-4240-b981-9137d53ad77d,` |
| 82 | `GetTextEventParamInteger` | 102 | `Gustav/Story/osid/Act1_DEN_ShadowDruid.txt:101` | `GetTextEventParamInteger(1,` |
| 83 | `LevelLoaded` | 211 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:12` | `LevelLoaded(_)` |
| 84 | `OnCrimeInvestigatorSwitchedState` | 95 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:802` | `OnCrimeInvestigatorSwitchedState((INTEGER)_Var1,` |
| 85 | `RealSum` | 146 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:877` | `RealSum(_Var2,` |
| 86 | `IsInCombat` | 129 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1110` | `IsInCombat(S_CHA_FL1_BanditGuard_4000f859-71fe-49ef-8400-da44b6fef92a,` |
| 87 | `GUIDToString` | 264 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1806` | `GUIDToString(_Var1,` |
| 88 | `DialogGetInvolvedPlayer` | 101 | `Gustav/Story/osid/Act1_FOR_BottomlessWell.txt:53` | `DialogGetInvolvedPlayer(_Var1,` |
| 89 | `IsControlled` | 138 | `Gustav/Story/osid/Act1_FOR_BottomlessWell.txt:374` | `IsControlled(_Var1,` |
| 90 | `Concatenate` | 671 | `Gustav/Story/osid/Act1_FOR_BottomlessWell.txt:448` | `Concatenate(_Var4,` |
| 91 | `GetInventoryOwner` | 89 | `Gustav/Story/osid/Act1_DEN_VoloTravel.txt:79` | `GetInventoryOwner(S_DEN_VoloGSS_30bf3988-8704-4e0d-88ec-be1eb6dd31c2,` |
| 92 | `IsItem` | 141 | `Gustav/Story/osid/Act1_FOR_Boosters.txt:294` | `IsItem(_Var1,` |
| 93 | `IsStatusFromGroup` | 99 | `Gustav/Story/osid/Act1_FOR_Boosters.txt:628` | `IsStatusFromGroup(_Var1,` |
| 94 | `IsPartyMember` | 195 | `Gustav/Story/osid/Act1_FOR_SchoolOgres.txt:415` | `IsPartyMember(_Var2,` |
| 95 | `CreateAtObject` | 89 | `Gustav/Story/osid/Act1_GOB_DrowCommander.txt:71` | `CreateAtObject(WPN_HUM_Mace_A_0_3186796d-3ab3-4d49-bfc2-cba1aff0cf5a,` |
| 96 | `GetTextEventParamString` | 94 | `Gustav/Story/osid/Act1_HAG_Hag.txt:769` | `GetTextEventParamString(1,` |
| 97 | `ChangeApprovalRating` | 87 | `Gustav/Story/osid/Act1_PLA_GithChokepoint.txt:1159` | `ChangeApprovalRating(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12,` |
| 98 | `GetHandlingCrimeID` | 112 | `Gustav/Story/osid/Act1_UND_PanicRoom.txt:75` | `GetHandlingCrimeID(S_GLO_HiddenGnome_6cacd488-c479-47a9-9a39-1cfb2bf6836e,` |
| 99 | `TagSet` | 109 | `Gustav/Story/osid/DebugItem.txt:406` | `TagSet((GUIDSTRING)_Var1,` |
| 100 | `GetRegion` | 124 | `Gustav/Story/osid/GLO_FactionTagging.txt:48` | `GetRegion(_Var1,` |

### B2. 关键事件族说明（LLM 触发器候选）

- **对话**：`DialogStarted(dialog, instanceID)` / `DialogEnded(dialog, instanceID)`（都有两个参数，实例 ID 是整数索引）；`AutomatedDialogStarted/Ended`（旁白 AD，参数 dialog+instanceID）；`DialogRequestFailed`；`DialogActorLeft`；`DialogGetInvolvedPlayer(instanceID, idx, player)`；SE 侧另可监听 `DialogStartRequested`（见 G1）。
- **进入/离开**：`EnteredTrigger(char, trigger)` / `LeftTrigger` / `IsInTrigger`；`EnteredRegion/LeftRegion`；`LevelLoaded(level)`（进图）。
- **战斗**：`EnteredCombat(char, group)` / `LeftCombat` / `CombatEnded(group)` / `TurnStarted(char)` / `SwitchedCombat` / `AttackedBy` / `Died` / `Dying` / `KilledBy` / `Resurrected` / `HitpointsChanged` / `DestroyedBy`。
- **状态**：`StatusApplied(char, status, caster, ...)` / `StatusRemoved` / `HasActiveStatus`；`FlagSet(flag, char, idx)` / `FlagCleared` / `GetFlag` / `TagSet` / `IsTagged`；`EntityEvent(char, "事件名")` / `DualEntityEvent`（**规则间自定义事件通道**，也是 osid 与 anubis 通信的通道）。
- **时间**：`TimerFinished(timerName)`、`ObjectTimerFinished(char, timerName)`、`RealtimeObjectTimerFinished`、`ObjectQuestTimerLaunch`（详见 D 节）。
- **物品/交互**：`UseStarted/UseFinished(char, item)`、`Opened/Closed/Unlocked/Locked/IsOpened`、`GameBookInterfaceClosed(book, char)`。
- **关系**：`RelationChanged(a, b, newValue, ...)`、`ChangeApprovalRating`（条件侧罕见，见 E 节）。
- **纯查询类**（条件里很常用，不是事件）：`GetPosition`、`GetFaction`、`GetRelation`、`CanSee`、`IsEnemy`、`Exists`、`Random`、`IntegerSum`、`Concatenate`、`SysCount` 等。

### B3. anubis Lua 事件/回调模式

anubis state 内以 `events.事件名 = function(e) ... end` 订阅引擎事件（统计 `Scripts\anubis\` 全量）：

```
EntityEvent 248   TimerFinished 202   SplineControlPointReached 145   FlagSet 120
DialogEnded 56    FlagCleared 47      EnteredCombat 26       TurnStarted 21
LeftCombat 19     DialogStarted 19    Deactivated 17         Activated 17
StatusRemoved 16  Died 16             Destroyed 15           EnteredTrigger 13
TurnEnded 12      SavegameLoaded 12   Dying 11               LeftTrigger 10
StatusApplied 7   DialogActorJoined 7 CaretSplineControlPointReached 7
DialogActorLeft 5 Damaged 5           LevelLoaded 4          UseStarted 3
OnStageChanged 3  RollResult 2        Resurrected 2          BaseFactionChanged 2
SpellCastResult 1 ReposeRemoved 1     ReposeAdded 1          PlatformDestroyed 1
OnShutdown 1      LevelGameplayStarted 1  DisturbanceReactionRequest 1
DisturbanceCanceled 1  AttemptedDisarm 1  AnimationEvent 1   AddedTo 1
AICalculationDone 1
```

完整示例（`Scripts\anubis\node\Traps\Version 4.0\Trap_HiddenPerception.ann`）：
```lua
events.TimerFinished = function(e)
    if e.TimerName == "CheckSight" then
        local actives = GetActiveCharacters(me, params.maxDistance)
        for _, char in pairs(actives) do
            if char.Character.IsPlayer and not failedPlayers[char.UUID.String] and CanSee(char, me) then
                failedPlayers[char.UUID.String] = true
                RequestPassiveRoll(char.Character, me, Skill.Perception, DifficultyClass(params.perceptionDC), "PUZZLE_HiddenPerception")
            end
        end
    end
end
events.EntityEvent = function(e)
    if not visible and e.TargetEntity == me and e.Event == "StoryReveal" then
        SetVisible(me, true)
    end
end
```
即：**anubis 本身就有与 Osiris 同源的事件订阅（40 种），无需 SE 即可拿到对话/战斗/flag/时间事件**；另可用 `StartTimer(me, "Name", interval, repeatCount)` / `StopTimer(me,"Name")` 做周期回调。

### B4. Timeline（时间线）结构 —— 对话的"播放层"

转换样本（Divine.exe convert-resource）：

| 样本 | 来源 | 结论 |
|---|---|---|
| Astarion_Recruitment_Timeline.lsx | `Public\Gustav\Timeline\Generated\Astarion_Recruitment.lsf`（Act1 普通对话） | 结构 `TimelineContent → Effect(Duration≈903.8s) → Phases → Phase{Duration, PlayCount, DialogNodeId}`；每个 Phase 对应对话树一个节点，节点内有 `QuestionHoldAutomation`（玩家回答时停表）等自动化 |
| Astarion_InPartyEND.lsx | `Public\GustavDev\Timeline\Generated\Astarion_InPartyEND.lsf`（Act3） | 更复杂：含 `Actor`（1757 个）、`EffectComponent`、`CameraContainer`、`CombatTimelineHandler`（战斗时间线）、`TransformChannel`（动作通道） |
| ARENA_Hag.lsx | `Public\Gustav\Timeline\Generated\ARENA_Hag.lsf` | 含 `Object/MaterialDetails/OverlayGroups`（场景物件） |
| CharacterLight_Gustav.lsx | `Public\Gustav\Timeline\CharacterLight\` | 照明时间线：`LightingSetup → Light` |

**触发机制**：对话 .lsj 顶层 `TimelineId`（GUID）→ 时间线资源；该 GUID 也出现在时间线文件内部（`MapKey` 属性，Astarion_Recruitment 转换文件第 157263 行 `MapKey=7586fe9c-...`，与 .lsj 的 TimelineId 一致）。播放由引擎在对话开始时按 TimelineId 加载时间线并逐 Phase 执行；时间线里的 `DialogNodeId` 即 .lsj 节点 UUID。**即：对话 = 树（Dialogs .lsj）+ 播放器（Timeline .lsf）+ 文本（Localization）**。osid 不直接播时间线，只负责"启动对话/收尾"（QRY_StartDialog → 引擎加载 TimelineId）。

---

## C. 动作 API（THEN 块函数目录）

### C1. TOP-100 引擎动作（次数为全库 THEN 出现次数，例子为首次出现位置）：

| # | 动作名 | 次数 | 例子(文件:行) | 示例片段 |
|---|---|---|---|---|
| 1 | `SetFlag` | 6038 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:12` | `SetFlag(GLO_Volo_Knows_Lobotomy_6f016a74-c28b-4a6a-919e-b58223cc14cb,` |
| 2 | `SetTag` | 514 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:13` | `SetTag(_Var1,` |
| 3 | `ApplyStatus` | 1285 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:15` | `ApplyStatus(_Var1,` |
| 4 | `StartVoiceBark` | 505 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:24` | `StartVoiceBark(CAMP_VoloOperation_VB_Eye_c6f7a59e-e00a-c55d-1234-4b14762a32fb,` |
| 5 | `RequestDelete` | 78 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:32` | `RequestDelete(S_DEN_ErsatzEye_1e6020d1-2344-4e4e-8a3c-ab0293bc506b);` |
| 6 | `ClearTag` | 355 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:40` | `ClearTag(_Var2,` |
| 7 | `RemoveStatus` | 1216 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:48` | `RemoveStatus(_Var1,` |
| 8 | `ClearFlag` | 2923 | `Gustav/Story/osid/Act1_CAMP_VoloOperation.txt:104` | `ClearFlag(GLO_Volo_State_AtCamp_de1cadca-2eca-4cee-a3dc-e262bbb92277);` |
| 9 | `SetOnStage` | 1614 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:23` | `SetOnStage(S_FOR_Courier_Ball_c9602f79-27a8-4f79-b0f2-3aba300bd80f,` |
| 10 | `QRY_SpeakerIsAvailable` | 70 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:38` | `QRY_SpeakerIsAvailable(_Var1)` |
| 11 | `DialogRequestStop` | 69 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:42` | `DialogRequestStop(S_FOR_Courier_Dog_3059f69c-068d-4e28-8491-55953c027901);` |
| 12 | `TimerLaunch` | 695 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:153` | `TimerLaunch("FOR_CourierDog_Blink2World_Fallback",` |
| 13 | `SetHasDialog` | 507 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:198` | `SetHasDialog(S_FOR_Courier_Dog_3059f69c-068d-4e28-8491-55953c027901,` |
| 14 | `ToInventory` | 522 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:222` | `ToInventory(ITEMGUID_S_FOR_Courier_Ball_c9602f79-27a8-4f79-b0f2-3aba300bd80f,` |
| 15 | `TimerCancel` | 207 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:223` | `TimerCancel("FOR_CourierDog_Blink2World_Fallback");` |
| 16 | `TemplateAddTo` | 167 | `Gustav/Story/osid/Act1a_FOR_Courier.txt:311` | `TemplateAddTo(_Var3,` |
| 17 | `Lock` | 48 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:118` | `Lock(S_CAMP_PartyVoloCageDoor_bb42490f-603e-4118-a167-8129ef192c27,` |
| 18 | `Die` | 993 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:206` | `Die(S_CAMP_DeadBird_a4f25c31-4ac0-418b-a6c4-35f29cb16b7c,` |
| 19 | `TeleportTo` | 1596 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:214` | `TeleportTo(S_DEN_SenderBird_bf90aa40-232b-40fd-a43e-699bb964e337,` |
| 20 | `SetEntityEvent` | 972 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:223` | `SetEntityEvent(S_GLO_Volo_2af25a85-5b9a-4794-85d3-0bd4c4d262fa,` |
| 21 | `SetFaction` | 538 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:248` | `SetFaction(S_GOB_DrowCommander_25721313-0c15-4935-8176-9f134385451b,` |
| 22 | `SetCombatGroupID` | 391 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:249` | `SetCombatGroupID(S_GOB_DrowCommander_25721313-0c15-4935-8176-9f134385451b,` |
| 23 | `LookFromTrigger` | 121 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:326` | `LookFromTrigger(_Var2,` |
| 24 | `Unequip` | 60 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:1022` | `Unequip(_Var1,` |
| 25 | `QRY_SelectDialogStartRequested` | 49 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:1025` | `QRY_SelectDialogStartRequested(S_DEN_ParentA_d6d88c8b-6ba7-4350-b3b3-d60565a44e90,` |
| 26 | `SetCanTrade` | 127 | `Gustav/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:1060` | `SetCanTrade(S_DEN_ParentA_d6d88c8b-6ba7-4350-b3b3-d60565a44e90,` |
| 27 | `SetImmortal` | 132 | `Gustav/Story/osid/Act1a_Camp.txt:215` | `SetImmortal(S_GLO_Cazador_2f1880e6-1297-4ca3-a79c-9fabc7f179d3,` |
| 28 | `ObjectTimerCancel` | 184 | `Gustav/Story/osid/Act1a_Camp.txt:530` | `ObjectTimerCancel(_Var1,` |
| 29 | `ObjectTimerLaunch` | 554 | `Gustav/Story/osid/Act1a_Camp.txt:543` | `ObjectTimerLaunch(_Var1,` |
| 30 | `Transform` | 181 | `Gustav/Story/osid/Act1a_Camp.txt:660` | `Transform(S_ORI_GaleDouble_ddf3dd37-fa65-4351-9f55-e50b1211fcfe,` |
| 31 | `LookAtEntity` | 131 | `Gustav/Story/osid/Act1a_Camp.txt:664` | `LookAtEntity(S_ORI_GaleDouble_ddf3dd37-fa65-4351-9f55-e50b1211fcfe,` |
| 32 | `AddSpell` | 102 | `Gustav/Story/osid/Act1a_Camp.txt:1082` | `AddSpell(_Var1,` |
| 33 | `QRY_CRIME_BlockRegisterCrime` | 149 | `Gustav/Story/osid/Act1a_Camp.txt:1397` | `QRY_CRIME_BlockRegisterCrime((CHARACTER)_Var1,` |
| 34 | `DebugText` | 549 | `Gustav/Story/osid/Act1a_Camp.txt:1460` | `DebugText(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12,` |
| 35 | `TriggerRegisterForCharacter` | 348 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:195` | `TriggerRegisterForCharacter(S_PLA_NPCInterruptionBox_198849d7-7f06-4520-a9e6-1ddedfe38660,` |
| 36 | `SetOwner` | 63 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:202` | `SetOwner(S_CHA_CageBottom_S_LT_PLT_CHA_CageBottom_106fde0f-c09d-8920-3204-dc169a0ef008,` |
| 37 | `SetCanJoinCombat` | 371 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:218` | `SetCanJoinCombat(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12,` |
| 38 | `RemoveHarmfulStatuses` | 112 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:220` | `RemoveHarmfulStatuses(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12);` |
| 39 | `SetHitpointsPercentage` | 102 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:242` | `SetHitpointsPercentage(S_Player_Laezel_58a69333-40bf-8358-1d17-fff240d7fb12,` |
| 40 | `TriggerUnregisterForCharacter` | 267 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:392` | `TriggerUnregisterForCharacter(S_PLA_NPCInterruptionBox_198849d7-7f06-4520-a9e6-1ddedfe38660,` |
| 41 | `QRY_SelectDialogStartRequested_AfterGenerics` | 52 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:534` | `QRY_SelectDialogStartRequested_AfterGenerics((CHARACTER)_Var1,` |
| 42 | `UseSpell` | 184 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:959` | `UseSpell(S_CHA_CagerLaezel1_2c8537fb-bf73-43a2-a8ff-48e41453adea,` |
| 43 | `ClearOwnership` | 178 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:1007` | `ClearOwnership(S_CHA_CageBottom_S_LT_PLT_CHA_CageBottom_106fde0f-c09d-8920-3204-dc169a0ef008);` |
| 44 | `RealtimeObjectTimerLaunch` | 485 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:1846` | `RealtimeObjectTimerLaunch(_Var1,` |
| 45 | `QuestUpdate` | 2668 | `Gustav/Story/osid/Act1_CHA_LaezelRecruit.txt:2144` | `QuestUpdate(_Var1,` |
| 46 | `SetForceUpdate` | 262 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:107` | `SetForceUpdate(S_CHA_FL1_Stairs_Door_a1e0afa3-7a19-4607-8113-9b0b4dbe3c10,` |
| 47 | `SetCanInteract` | 324 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:108` | `SetCanInteract(S_CHA_FL0_LadderToOutside_a7c7ffa0-a495-42c5-bcd1-fc1767d2affd,` |
| 48 | `Unlock` | 141 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:137` | `Unlock(S_CHA_OUTSIDE_Crypt_Door_d06d5638-c69a-4fcc-b996-c305acbb7ebf);` |
| 49 | `Resurrect` | 108 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:161` | `Resurrect(_Var1,` |
| 50 | `PlaySound` | 159 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:737` | `PlaySound(S_CHA_OUTSIDE_Fissure_Boulder_29a94ca5-cede-4932-88c5-3942334e4990,` |
| 51 | `PlayEffect` | 257 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:763` | `PlayEffect(S_CHA_Outside_BoulderImpactFX_34ad3704-84c3-4bed-8493-a5eae5cd2a1b,` |
| 52 | `TriggerUnregisterForItems` | 51 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:765` | `TriggerUnregisterForItems(S_CHA_Outside_HoleTrigger_de003198-dc27-4180-a0c6-3cb299367fa1);` |
| 53 | `CrimeIgnoreCrime` | 86 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:811` | `CrimeIgnoreCrime(_Var5,` |
| 54 | `TeleportToPosition` | 196 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:889` | `TeleportToPosition(_Var1,` |
| 55 | `ApplyDamage` | 51 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:903` | `ApplyDamage(_Var1,` |
| 56 | `SetEntityEventReal` | 94 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1002` | `SetEntityEventReal(_Var1,` |
| 57 | `SetWeaponUnsheathed` | 46 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1256` | `SetWeaponUnsheathed(_Var1,` |
| 58 | `Open` | 138 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1341` | `Open(S_CHA_FL1_MetalGateReplacement_17b11bde-1fbe-441d-8f6a-f13003b5f633);` |
| 59 | `Close` | 92 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1353` | `Close(S_CHA_FL1_MetalGateReplacement_17b11bde-1fbe-441d-8f6a-f13003b5f633);` |
| 60 | `SetDualEntityEvent` | 222 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1506` | `SetDualEntityEvent(NULL_00000000-0000-0000-0000-000000000000,` |
| 61 | `ItemMoveTo` | 75 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:1881` | `ItemMoveTo(S_CHA_FL0_LadderToOutside_a7c7ffa0-a495-42c5-bcd1-fc1767d2affd,` |
| 62 | `SetVisible` | 241 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:2120` | `SetVisible(S_GLO_JergalAvatar_0133f2ad-e121-4590-b5f0-a79413919805,` |
| 63 | `SetDetached` | 102 | `Gustav/Story/osid/Act1_CHA_Chapel.txt:2121` | `SetDetached(S_GLO_JergalAvatar_0133f2ad-e121-4590-b5f0-a79413919805,` |
| 64 | `RemoveSurfaceLayer` | 49 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:112` | `RemoveSurfaceLayer(S_CHA_ShadowHeartStartSphere_8a65b0ae-7d7b-4685-b657-4855f0468915,` |
| 65 | `PurgeOsirisQueue` | 120 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:277` | `PurgeOsirisQueue(S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679);` |
| 66 | `Equip` | 104 | `Gustav/Story/osid/Act1_CHA_ShadowHeartRecruitment.txt:402` | `Equip(S_Player_ShadowHeart_3ed74f06-3c60-42dc-83f6-f034cb47c679,` |
| 67 | `AppearAt` | 69 | `Gustav/Story/osid/Act1_CHA_Forest.txt:68` | `AppearAt(_Var1,` |
| 68 | `CreateExplosion` | 67 | `Gustav/Story/osid/Act1_CHA_Forest.txt:94` | `CreateExplosion(_Var2,` |
| 69 | `RemoveSpell` | 56 | `GustavDev/Story/osid/Act1a_FOR_Courier_PostEA.txt:84` | `RemoveSpell(_Var1,` |
| 70 | `MakePlayerActive` | 78 | `Gustav/Story/osid/Act1_CRA_Escape_IntellectDevourers.txt:188` | `MakePlayerActive(_Var2);` |
| 71 | `SetStoryDisplayName` | 64 | `Gustav/Story/osid/Act1_CRA_Escape_Mindflayer.txt:73` | `SetStoryDisplayName(S_CRA_Escape_Mindflayer_d5385cd0-f371-43dc-a0a2-50381fc50ea4,` |
| 72 | `ClearScreenFade` | 49 | `Gustav/Story/osid/Act1_CRA_Escape_WakeUp.txt:102` | `ClearScreenFade(_Var1,` |
| 73 | `LeaveCombat` | 74 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:697` | `LeaveCombat(_Var1);` |
| 74 | `DebugBreak` | 198 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1020` | `DebugBreak("Start` |
| 75 | `TriggerSetSoundState` | 123 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1575` | `TriggerSetSoundState(Amb_SV_RangerCamp_FZ_000_3fd38540-d846-770c-ba66-21c4924dacd6,` |
| 76 | `Use` | 99 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:1934` | `Use(_Var1,` |
| 77 | `SetCanFight` | 168 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:2005` | `SetCanFight(_Var1,` |
| 78 | `TriggerClearItemsOwner` | 74 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:2027` | `TriggerClearItemsOwner(S_DEN_Trainer_Ownership_5db200ee-bcb1-4a41-b5cc-72be9bc9cbc4);` |
| 79 | `QRY_CorpseLooting_BlockMakeOwned` | 64 | `Gustav/Story/osid/Act1_DEN_AttackOnDen.txt:3152` | `QRY_CorpseLooting_BlockMakeOwned((CHARACTER)_Var1)` |
| 80 | `SysClear` | 342 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:484` | `SysClear("DB_DEN_CapturedGoblin_NPC",` |
| 81 | `CharacterStopCrime` | 92 | `Gustav/Story/osid/Act1_DEN_CapturedGoblin.txt:991` | `CharacterStopCrime(S_DEN_CapturedGoblin_783d7572-a846-455f-b686-247a95263ebb,` |
| 82 | `CreateSurface` | 91 | `GustavDev/Story/osid/Act1a_Camp.txt:932` | `CreateSurface(_Var1,` |
| 83 | `PlayAnimation` | 179 | `Gustav/Story/osid/Act1_DEN_Apprentice.txt:336` | `PlayAnimation(S_DEN_Apprentice_7cabf226-e34b-4556-8903-a45d0fe26caf,` |
| 84 | `QRY_SelectCustomDialog` | 126 | `GustavDev/Story/osid/Act1b_CRE_ChainOfCommand.txt:967` | `QRY_SelectCustomDialog(S_CRE_Templar_378ac93e-03a0-40b4-904c-f37989ac7a8c,` |
| 85 | `RealtimeObjectTimerCancel` | 52 | `Gustav/Story/osid/Act1_DEN_DruidLair.txt:196` | `RealtimeObjectTimerCancel(_Var1,` |
| 86 | `StopAnimation` | 46 | `Gustav/Story/osid/Act1_DEN_Gate.txt:70` | `StopAnimation(S_DEN_GateMechanism_5564d21c-9033-4958-8cc8-cd3f497bb51b,` |
| 87 | `CrimeConfrontationDone` | 74 | `Gustav/Story/osid/Act1_DEN_DruidAttack.txt:536` | `CrimeConfrontationDone(_Var3,` |
| 88 | `PlatformMoveTo` | 54 | `GustavDev/Story/osid/Act1b_CRE_Exterior.txt:43` | `PlatformMoveTo(S_LTN_PLT_CRE_RailLift_000_70bb740a-76eb-4255-b607-e2dcad69dbeb,` |
| 89 | `QRY_GLO_SkillCheck_CheckAdvantage` | 49 | `GustavDev/Story/osid/Act1b_CRE_Creche_Misc.txt:616` | `QRY_GLO_SkillCheck_CheckAdvantage(_Var1,` |
| 90 | `BlockNewCrimeReactions` | 89 | `Gustav/Story/osid/Act1_DEN_HarpyMeal.txt:33` | `BlockNewCrimeReactions(S_DEN_CharmedKid_3b92c689-6024-4446-a6c9-584e9e8d77ca,` |
| 91 | `QRY_OriginMoment_PreventRelaunchDialog` | 95 | `GustavDev/Story/osid/Act1b_OriginMoments_Laezel.txt:143` | `QRY_OriginMoment_PreventRelaunchDialog(CRE_ChainOfCommand_Vlaakith_OM_Laezel_AOM_OOM_8a12a3a7-d7bf-4398-8770-ed2d17e257d6,` |
| 92 | `QRY_SelectCustomDialog_AfterGenerics` | 187 | `GustavDev/Story/osid/Act1_CAMP_GoblinHuntCelebration.txt:1009` | `QRY_SelectCustomDialog_AfterGenerics(_Var1,` |
| 93 | `AddGold` | 79 | `Gustav/Story/osid/Act1_DEN_Thieflings_Hideout.txt:1171` | `AddGold(S_DEN_HideoutKidStash_6a957f96-e910-4a3b-ad12-03359775c4b8,` |
| 94 | `RemoveStatusesWithGroup` | 47 | `SharedDev/Story/osid/GLO_CombatNPCs_PostEA.txt:1029` | `RemoveStatusesWithGroup(_Var1,` |
| 95 | `PlayEffectAtPosition` | 66 | `SharedDev/Story/osid/GLO_CombatNPCs.txt:137` | `PlayEffectAtPosition(VFX_Item_FireBowl_Explosion_01_9838578e-0bee-4c7f-4cf4-8ebf4657d781,` |
| 96 | `RequestProcessed` | 65 | `GustavDev/Story/osid/Act1_DEN_DruidAttack.txt:464` | `RequestProcessed(_Var2,` |
| 97 | `CharacterStopCrimeWithID` | 69 | `GustavDev/Story/osid/Act1_DEN_Thieflings_Hideout.txt:779` | `CharacterStopCrimeWithID(_Var2,` |
| 98 | `HideTutorial` | 64 | `GustavDev/Story/osid/Act1_Tutorials_AfterTUT.txt:91` | `HideTutorial(_Var1,` |
| 99 | `QRY_EPI_Epilogue_ArticleIsValid` | 75 | `GustavDev/Story/osid/Act3c_EPI_Gazettes.txt:139` | `QRY_EPI_Epilogue_ArticleIsValid(_Var2)` |
| 100 | `QRY_EPI_Epilogue_LetterIsValid` | 58 | `GustavDev/Story/osid/Act3c_EPI_Letters.txt:69` | `QRY_EPI_Epilogue_LetterIsValid(_Var1)` |

### C2. 如何启动对话

- 规则侧：`QRY_StartDialog(dialog, speaker, player, ...)` / `QRY_StartDialogCustom` / `QRY_StartDialogWithAvailableSpeakerInRange`（带 10m 距离检查）/ `QRY_StartDialogCustomWithAvailableSpeakerInRange` —— 定义在 `Mods\Gustav\Story\osid\__PROC.txt`（如 802 行 `QRY_StartDialog(_Var3, _Var2, _Var1)`），是用户查询，内部做"说话人可用"检查后请求引擎开对话；对话资源用 .lsj 的 UUID（如 `QRY_StartDialog(PLA_StuckHalfElf_TryJoinParty_78248a7c-..., S_PLA_StuckHalfElf_..., _Var1)`，`Act1_PLA_TavernInvestigation_Surroundings.txt:479`）。
- 引擎自动开对话：物品/书等 `UseStarted(char, item)` + `DB_Dialogs(item, dialog)` → `PROC_ProcessUseItemWithDialog`（__PROC.txt:770+）；`DB_SpotPlayers` 机制用 `EnteredTrigger` 触发"发现"对话。
- 结束/打断：`PROC_ForceStopDialog`（osid 487 次调用）、`DialogRequestStop`、`SetHasDialog(char, 0/1)`、`PROC_RemoveAllDialogEntriesForSpeaker`。
- SE 侧（注入/强开）：`Osi.StartDialog_Internal(...)`（见 G8，用法未官方文档化）。

### C3. 如何修改好感

- `ChangeApprovalRating(char, target, 0, value, _)` —— 例：`Mods\SharedDev\Story\osid\_Greevers_Little_Helpers.txt:1765` `ChangeApprovalRating(_Var4, _Var2, 0, _Var5, _)`（第 3 参数 0 疑似"type"）。
- `RemoveApprovalRating(char, target, _)`（`_GLO_Shared_Origins.txt:641`）；查询 `DB_ApprovalRating(owner, target, value)`（条件）；引擎事件 `ApprovalRatingChanged(owner, target, delta)`（`_GLO_Shared_Origins.txt:668` → `PROC_ApprovalRatingChanged`）。
- 好感阈值机制见 E 节。

### C4. 如何"说话"（无头顶浮字的 Osiris 专用 API）

- osid 里没有 `Say` 函数（grep 零命中）。近似能力：
  - `TextEvent("事件名")` —— 引擎文本事件（条件侧 2403 次，如 `Act1a_FOR_Courier.txt:98` `TextEvent("dog2camp")`；也被对话系统用来触发叙事文本）。
  - `StartVoiceBark(VB_资源GUID, char)` —— 播放语音台词，例 `Act1_CHA_ShadowHeartRecruitment.txt:26`。
  - 正式说话 = 启动对话/AD（`AutomatedDialogStarted` 事件触发旁白台词；anubis 里 `StartAutomatedDialog(ad, wait, entity)`）。
- SE 侧头顶浮字无现成 API（`Osi.DebugText` 仅调试，见 G7）。

---

## D. 时间系统

结论：**Osiris 规则引擎没有"几点钟"概念**（grep Hour/GameTime/TimeOfDay 在 osid 中零命中，仅 `TriggerSetSoundState(..., "AMB_TimeofDay", "Night", 0)` 这种环境音频切换）。时间通过以下机制进入规则：

1. **游戏时钟定时器**（毫秒，暂停时停走）：`TimerLaunch(timerName, ms)` + `TimerFinished(timerName)`；例 `Act1_CRA_Boosters.txt:30` `TimerFinished("CRA_HarperRock_Movable")`。
2. **角色/物件定时器**：`ObjectTimerLaunch(char, name, ms, ...)` + `ObjectTimerFinished`；任务计时：`ObjectQuestTimerLaunch(_Var2, "GOB_ChickenChase_Game", "GOB_ChickenChase_GameTimer", 60000, 0)`（`Act1_GOB_ChickenChase.txt:581`）。
3. **实时定时器**（挂机也走）：`RealtimeObjectTimerLaunch(char, name, ms)`（`__GLOBAL_AnubisConfigs.txt:120` 用 100ms 延迟做 anubis 配置分发）；`TimerCancel/ObjectTimerCancel/RealtimeObjectTimerCancel`。
4. **长休/营地（主要的"一天"事件）**：`PROC_LongRest()`（被营地睡觉等触发，`_Trade.txt:53` 用它刷交易库存）；日夜切换 `PROC_Camp_SetModeToNight`（`Mods\Gustav\Story\osid\GLO_Camp.txt:1885-1905`）→ 写 `DB_Camp_NightMode(1)` + `SetFlag(GLO_CAMP_State_NightMode_fb53edc2-..., NULL, 0)` + `TriggerSetSoundState(trigger, "AMB_TimeofDay", "Night", 0)`。营地夜事件由 `DB_CampNight` 族驱动（`GLO_CampNights.txt` INITSECTION 种子）。
5. **anubis 侧时间**：`StartTimer(me, "CheckSight", 0.5, -1)`（0.5 秒周期、-1 无限重复）与 `events.TimerFinished` 回调（Trap_HiddenPerception.ann）；行为脚本用 `Sleep(秒)` 协程暂停。
6. **引擎时间读取**：SE 侧 `Ext.Timer.GameTime()`（毫秒）与 tick 回调 `e.Time.Time`（G 节）。

对 LLM 模组的含义：**"时间"要用定时器+昼夜 flag+长休事件自己维护**，没有现成时钟查询（除非用 SE 的 GameTime）。

---

## E. 关系系统

### E1. ApprovalRatings 数据（好感评级表）

目录 `Public\GustavDev\ApprovalRatings\Reactions\` 下 **2102 个 UUID 命名的 .lsx**（本身就是 XML，无需转换；`Reactions.lsx` 只是空容器）。结构（样本 `00008148-8f87-454f-95df-88d2a5cbea24.lsx`）：

```xml
<node id="Reaction">
    <attribute id="Scope" type="uint8" value="1"/>   <!-- 作用域 1/2 -->
    <attribute id="UUID" type="guid" value="00008148-..."/>
    <children>
        <node id="Reactions">
            <node id="Reaction">
                <attribute id="id" type="guid" value="3780c689-..."/>  <!-- 对话反应/表态 GUID -->
                <attribute id="value" type="int32" value="0"/>          <!-- 好感增减值 -->
```

即：**每个"对话反应"（dialogue reaction，如某个选项/表态）对应一个好感数值**；多个反应打包在一个 UUID 组里。样本中可见 `value` 为 -1/0/1/5/7 等小整数。引擎在玩家选择相应对话节点时按此表加减好感（具体查找键是对话节点内的反应 GUID）。

### E2. osid 中的好感规则

- 引擎事件 `ApprovalRatingChanged(owner, target, delta)` → `PROC_ApprovalRatingChanged`（`_GLO_Shared_Origins.txt:668-673`）。
- 阈值事件：`DB_OriginRelationThresholdEventsPerSpeaker(说话人槽位, Flag名, 阈值)` 种子（同文件 5-10 行：`...("1", Approval_AtLeast_-40_For_Sp1_b5ab9ca2-..., -40)`），对应的 `Approval_AtLeast_80_For_Sp4` 等就是 `Public\Gustav\Flags\001125f2-....lsf` 里注册的 flag（Name=`Approval_AtLeast_80_For_Sp4`，Usage=4）——**引擎在好感跨过阈值时自动置该 flag**，规则用 `FlagSet` 监听。
- 读好感：`DB_ApprovalRating(owner, target, value)`；写好感：`ChangeApprovalRating` / `RemoveApprovalRating`（C3 节）。
- 好感驱动的玩家选择：`QRY_GetBestAvatarForCompanion` 系列按好感给玩家排名（`_GLO_Shared_Origins.txt:455+`）。

### E3. 同伴入队/离队（recruit）全链路

以影心（`Act1_CHA_ShadowHeartRecruitment.txt`）为证：

1. **对话节点设置 flag**：对话内容里的 `setflags` 机制把 `OriginAddToParty_4870b2cd-210c-0fdc-9c58-4d0142bdae29`（或离队 `OriginRemoveFromPartyAfterDialog_7a429beb-...`）写到角色上；
2. osid 捕获：`_GLO_Shared_Origins.txt:262` `IF FlagSet(OriginAddToParty_..., (CHARACTER)_Var1, (INTEGER)_Var2) AND DB_DialogPlayers(_Var2, _Var3, _) AND NOT DB_GLO_PartyMembers_RecruitAfterDialog(...) AND DB_Avatars(_Var3) THEN DB_GLO_PartyMembers_RecruitAfterDialog(_Var2, _Var1, _Var3);` —— 登记"对话结束后入队"；
3. 对话结束：`_GLO_Shared_PartyMembers.txt:302-307` `IF DialogEnded(_, idx) AND DB_GLO_PartyMembers_RecruitAfterDialog(idx, c1, c2) THEN PROC_GLO_PartyMembers_CheckAdd(c1, c2);` → `PROC_GLO_PartyMembers_Add`；
4. 入队状态：`DB_PartyMembers(char)`、`DB_Players(char)`；伙伴专属 `DB_OriginInPartyGlobal(S_Player_ShadowHeart_..., ORI_ShadowHeart_State_IsInParty_9a029c5a-...)`（`GLO_Origin_ShadowHeart.txt:7`）；`SetBlockDismiss(char, 0/1)` / `DB_BlockDismissable`。
5. 入队后引擎/规则把"招募对话"换成"日常对话"：`PROC_GLO_Origins_MaybeSetDefaultDialog` → `DB_Dialogs(char, 默认对话)`，并 `SetHasDialog(char, 0)`（_GLO_Shared_Origins.txt:314-322）。

### E4. 其他关系维度

- 阵营：`GetFaction(char, fac)` / `SetFaction(char, fac)`、`SetCombatGroupID`、`IsEnemy(a, b, 1)`、`SetRelationMutual(fac1, fac2, v)` / `PROC_SetRelation`（写 `DB_RelationChangingToHostile`，`__PROC.txt` `PROC_SetRelationMutual` 定义处）；关系查询 `GetRelation(a, b, 默认值)`（例 `Act1_DEN_DruidAttack.txt:1655`）。
- 商人：`SetCanTrade(char, 0/1)`（例 `_Gustav_CampFollowers.txt:67` 给 Volo 开贸易）。

---

## F. 持久化

### F1. Flag 机制（游戏事实/记忆的主力）

- 定义文件：`Public\Gustav\Flags\` 下 **UUID 命名**的 .lsf，每文件一个 flag，结构 `{UUID, Name(FixedString), Description, Usage(uint8)}`。转换样本 `000dcdd7-...lsf`：`Name=PLA_DeadFF1_Said_BaldursGate`（Usage=2）；`001125f2-...lsf`：`Name=Approval_AtLeast_80_For_Sp4`（Usage=4）。
- 命名规律（osid 中 SetFlag 采样，24 个典型名）：
  ```
  CAMP_Astarion_State_VictimOfAstarion_78dfbdb1     CAMP_Courier_Dog_State_FoundSomething_79f866c3
  CAMP_GLO_State_InCamp_161b7223                    CAMP_GoblinHuntCelebration_Event_MetBardBeforeParty_9ae7856e
  CAMP_GoblinHuntCelebration_State_DrowBetrayalOver_75aa1308
  CAMP_Origin_State_TiredOfTalkingTo_40225d88       CAMP_OwlbearCub_State_BecameCampFollower_a9742288
  CAMP_UnfortunateGnome_State_MovedToCamp_0292e2c3  CHA_Crypt_Event_ReadJergalPlaque_a33470ad
  CHA_Crypt_State_SpokeToJergal_6bae2cfe           CHA_FL0_State_AllSkeletonDead_a2c88791
  CHA_FL1_State_BanditsAlerted_1c0232a5            CHA_FL1_State_BanditsGoToCorridor_c68ce420
  ORI_ShadowHeart_Event_RecruitmentFight_8a222492   ORI_ShadowHeart_State_IsInParty_9a029c5a
  CRA_ShadowheartRecruitment_State_Unconscious_a461603e
  CHA_ShadowHeartRecruitment_UsedDoor_91d77fbb     DEN_Shadowheart_Event_ToDen_5e61b083
  GLO_Volo_Knows_Lobotomy_6f016a74                 GLO_CAMP_State_NightMode_fb53edc2
  ```
  规律：`<区域>_<主题>_<State|Event|Used|...>_<描述>_<uuid>`。**flag 承担了"世界状态/角色记忆"的功能**：见过谁、说过什么、打过架、营地跟班等等全是 flag。
- 读写 API：`SetFlag(flag, char_or_null, 0)` / `GetFlag(flag, char, 0)` / 事件 `FlagSet` / `FlagCleared` / `ClearFlag`；全局热缓存 `DB_GlobalFlag(flag)`（全库 11806 次，是最常用条件之一）+ `PROC_GlobalSetFlagAndCache`。flag 随存档自动持久化。

### F2. DB_ 数据库（运行时状态表）

- **种子**：INITSECTION 里 `DB_xxx(...)` 直接插入（如 `DB_Players(S_Player_ShadowHeart_...)`、`DB_DropMutingStatussesDialog(...)`）。
- **查询**：条件里 `DB_Players(_Var1)`（通配列）；**插入**：THEN 里 `DB_xxx(...)`；**删除**：`NOT DB_xxx(...)`。
- **一次性保护**：`QRY_OnlyOnce("名字")` 定义即 `AND NOT DB_OnlyOnce(_Var1) THEN DB_OnlyOnce(_Var1)`（`_Greevers_Little_Helpers.txt:757`），外加 `QRY_OnlyOnce_Reset`、`QRY_OnlyOncePerUser`（按玩家档案 ID）。
- **状态机**：`DB_State_Current(char, "状态组", "子状态")` + `PROC_State_Changed` / `PROC_State_Progress`（例：`Act1_CHA_ShadowHeartRecruitment.txt:53-68` 用 `DB_State_Current(S_Player_ShadowHeart_..., "Recruitment", "CHA")` 判断招募进度）。
- **计数/队列**：`SysCount("DB_xxx", 1, n)`（`Act1_DEN_DruidAttack.txt:1426`）、`DB_QRYRTN_*` 查询结果缓存表。
- **持久性**：DB 内容随 Osiris 状态存档；`SavegameLoaded` 是 anubis/规则可订阅的事件（anubis 统计 12 处），`QRY_BG3_SaveGameIsOlderThan` 用于版本迁移补丁（`PROC_ApplySavegamePatches` 2417 次调用）。

### F3. 模组存"NPC 记忆"的可用机制

1. **Osiris DB**：`DB_<Mod>_<NPC>_Memory(npcGuid, key, value)` —— SE 用 `Osi.DB_xxx(...)` 可读写；存读档自动保留；规则侧天然可查。缺点：Osiris 内存里，长表有性能/存档膨胀问题。
2. **Flag**：`SetFlag(<mod>_State_<npc>_<记忆键>_<uuid>, npc, 0)`，被引擎视为游戏事实，可被 `FlagSet` 事件监听；但 flag 有数量级规模（BG3 数万），且无值语义（只能存 0/1 + 关联实体）。
3. **SE 层**：`Ext.Vars.RegisterUserVariable`（随存档持久化、可同步客户端）、`Ext.IO.SaveFile`（写 `Mods/<Mod>/ScriptExtender/...` 文件，适合 LLM 记忆的 JSON 数据库）——见 G6。
4. **对话变量**：`DialogSetVariableInt/Float/String`（G8）把记忆带进对话。
5. 注意：纯文件方案（Ext.IO）不会随存档回滚；混合方案（DB+存档回调）最稳。

---

## G. Script Extender 接入点（联网调研结果）

调研来源：BG3SE 官方仓库（github.com/Norbyte/bg3se，`Docs/API.md` v30 + 完整源码）、LaughingLeader/BG3ModdingTools 生成的完整 Osiris 符号表（`generated/Osi.lua`、`Osi.Events.lua`）、社区 wiki.bg3.community。社区镜像 docs.devtargaryen.com 当时无法解析（DNS），故以上述一手来源交叉验证。

**通用事件订阅模式（确认）**：
```lua
Ext.Events.X:Subscribe(function(e) ... end)          -- 事件对象 e，字段因事件而异
Ext.Events.X:Subscribe(handler, {Priority=50, Once=true})
local id = Ext.Events.X:Subscribe(handler); Ext.Events.X:Unsubscribe(id)
-- 服务端约 30Hz：Ext.Events.Tick:Subscribe(function(e) _P(e.Time.Time) end)
```

| # | 能力 | API（确认/未确认） | 说明 |
|---|---|---|---|
| G1 | 钩子对话开始/结束 | **确认**：`Ext.Osiris.RegisterListener("DialogStarted"\|"DialogEnded", 2, "after", fn)`（对话事件是 Osiris 引擎事件，不是 SE 事件；`Ext.Events` 里没有 Dialogue 事件） | `Osi.DialogStarted(dialog, instanceID)` / `Osi.DialogEnded(dialog, instanceID)`；另有 `DialogStartRequested(target, player)`、`DialogActorJoined/Left`、`AutomatedDialogStarted/Ended` 等；备选：`Ext.Entity.OnChange("EsvCharacter", fn)` 订阅组件字段（`InDialog`）变化 |
| G2 | 每帧/tick 回调 | **确认**：`Ext.Events.Tick:Subscribe(function(e) ... end)`，回调参数 `e.Time.Time`（毫秒，~33ms 一次）；一次性 `Ext.OnNextTick(fn)` | 另有 `Ext.Timer.WaitFor(ms, cb)`（游戏钟）、`WaitForRealtime`、`WaitForPersistent(ms, name, cb)`（写档持久）、`Ext.Timer.GameTime()`。`Ext.Events.Heartbeat` **不存在** |
| G3 | 读取角色状态 | 位置**确认**：`Osi.GetPosition(char)` → x,y,z。好感**确认**：`Osi.GetApprovalRating(owner, rated)`。stats 名：`Osi.GetStatString(char)` → `Ext.Stats.Get(name).Level` 等。HP：**未确认**（无 `Osi.GetHitPoints`；候选：`entity.ActionResources.Resources` 中 HitPoints 资源条目，或 `entity.EsvCharacter` 组件字段） | 实体访问：`Ext.Entity.Get(guidOrHandle)` / `entity:GetComponent("EsvCharacter")` / `_C()`（当前宿主） |
| G4 | 调用 Osiris 函数 | **确认**：全局表 `Osi`（`Ext.Osi` 只含 Register/UnregisterListener）。Call 直接调；Query 无 OUT 返回 bool、有 OUT 按 OUT 数返回多值；`Osi.Proc_xxx` 调 PROC；`Osi.Qry_xxx` 调用户查询；DB 用 `Osi.DB_xxx:Get(nil, v, nil)` 查、调用即插、`:Delete` 删 | GUIDSTRING 参数接受 UUID 字符串或 64 位句柄 |
| G5 | 发起 HTTP 请求 | **确认不存在**：文档原文 "there is no external networking capability in the Script Extender"；源码无任何 Http 调用 | `Ext.Net` 仅游戏内客户端↔服务端通信（`Ext.Net.CreateChannel(moduleUuid, name)` + Send/Request/Broadcast）。**LLM 调用必须走游戏外进程或本地回环** |
| G6 | 持久化 | **确认**：`Ext.IO.SaveFile(path, content)` / `Ext.IO.LoadFile(path)`（路径相对游戏 Data 目录，如 `Mods/MyMod/ScriptExtender/memory.json`）；存档内变量 `Ext.Vars.RegisterUserVariable(name, {Server=true, ...})` → `entity.Vars.NAME`；`Ext.Vars.RegisterModVariable` + `Ext.Vars.GetModVariables(moduleUuid)` | `Ext.ModSaveFile` **不存在**（那是 DOS2SE 的）；`Mods[ModTable].PersistentVars` 已废弃 |
| G7 | 浮动文本/说话 | **未确认（无专门 API）**：`Osi.Say`、`Ext.DisplayFloatingText` 均不存在（符号表 grep 零命中） | 备选：`Osi.DebugText(object, text)`（调试浮字，位置粗略）；`Ext.UI`（Noesis UI 自定义叠加，复杂）；正式说话走对话/AD 系统 |
| G8 | 开始/注入对话 | **部分确认**：符号表有 `Osi.StartDialog_Internal(dialog, allowAttack, speaker1..speaker6, allowSpellVocal)`、`Osi.StartBehaviorDialog_Internal(...)`；实例控制 `Osi.DialogAddActor(instanceID, actor)`、`Osi.DialogRequestStop(speaker)`、`Osi.DialogSetVariableInt/Float/String(...)`、`Osi.SetEntityEventDialog(...)` | `_Internal` 后缀函数用法/前置条件**未官方文档化**；稳妥路线：监听 `DialogStartRequested` 由引擎接管，或按 osid 的 `QRY_StartDialog` 逻辑（DB_Dialogs + 距离/可用性检查）复刻前置 |

**对模组的最重要三点**：BG3SE 无出站网络（G5）、无 `Osi.Say`（G7）、对话钩子走 `Ext.Osiris.RegisterListener`（G1）。

---

## H. 对 LLM NPC 模组的意义（候选清单）

### H1. 观察输入（喂给 LLM 的世界状态）

- **事件流**（三个来源，均可用）：osid 事件（B 表 100 种，选对话/战斗/状态/flag 相关）→ SE `Ext.Osiris.RegisterListener`；引擎 tick → `Ext.Events.Tick`（按需降频到 1-2Hz）；anubis `events.*`（40 种，需把状态代码插进 anubis state 或另起 state）。
- **拉取式状态**（LLM 每次推理时现场取）：位置 `Osi.GetPosition`；stats `Osi.GetStatString` + `Ext.Stats.Get`；状态 `HasActiveStatus`；好感 `Osi.GetApprovalRating`；flag `Osi.GetFlag` / `Osi.DB_xxx:Get`；行为配置 `GetAnubisConfig`。
- **上下文快照**：当前对话（DialogStarted 事件参数 dialog GUID → 读 .lsj 树/文本）、周围角色（`GetActiveCharacters`）、昼夜（`GLO_CAMP_State_NightMode` flag / `DB_Camp_NightMode`）、时间（`Ext.Timer.GameTime()`）。

### H2. 记忆键（NPC 长期记忆的持久化键设计）

- **角色主键**：实例 GUID（UUID 字符串）——stats/对话/规则/anubis 四系统统一主键（A2 证据）。
- **记忆表**：`DB_<Mod>_Memory(npcGuid, key, value, timestamp)`；或 `Ext.Vars` 每 NPC 一个变量对象；或 `Ext.IO` JSON 文件。
- **事件记录**：对话 GUID+实例号（`DialogEnded(dialog, instanceID)`）、flag 名（`<区域>_<NPC>_State_<描述>_<uuid>` 惯例，F1）、好感变化（ApprovalRatingChanged delta）。
- **注意**：flag 无值语义、DB 随档、文件不随档——按记忆类型分桶（硬事实→DB/flag，叙事记忆→文件/JSON）。

### H3. 动作面（LLM 决策后能做什么）

- **说话/表态**：`Osi.StartDialog_Internal`（G8，需实测）或 `DialogAddActor` 注入已有对话；旁白 `StartAutomatedDialog`（anubis 可用）；`StartVoiceBark`（台词语音）。
- **行为**：`MoveTo`/`Wander`/`LookAtEntity`/`PlayAnimation`/`PlaySound`/`ApplyStatus`/`RemoveStatus`/`TeleportTo`/`SetFaction`/`SetCanTrade`/`SetCanJoinCombat`（C1 表）；anubis `m.action.*` 复用或 `DEV_EnableAnubis` 换配置。
- **世界改动**：`SetFlag`/`ClearFlag`（事实与记忆）、`QuestUpdate`、`SetEntityEvent`（规则间通信）、`ChangeApprovalRating`（好感）、`DB_xxx` 写（状态）。
- **LLM 动作管线建议**：LLM 输出结构化动作（动作名+参数）→ 白名单校验 → `Osi.动作` 或 anubis 函数执行；危险动作（Die/TeleportTo/SetFaction）加约束。

### H4. 事件触发器（LLM 被"唤醒"的时机）

1. `Ext.Osiris.RegisterListener` 订阅 `DialogStarted`/`DialogEnded`（NPC 被搭话/对话结束 → LLM 接管）。
2. `EnteredTrigger`/`EnteredCombat`/`AttackedBy`/`Died`（NPC 感知范围变化）。
3. `Ext.Events.Tick` 低频轮询 + 距离/时间条件（NPC 主动行为，如看到玩家）。
4. anubis state 树 `Valid()`/`events.*` 作为游戏内 AI 与 LLM 之间的"保底行为层"（LLM 延迟/失败时 NPC 不至于傻站）。

---

## I. 待验证问题（需运行游戏/进一步调研）

1. **SE API 未确认项**：
   - `Osi.StartDialog_Internal` / `StartBehaviorDialog_Internal` 的前置条件与真实调用方式（`SetHasOsirisDialog`? 需游戏内实测）。
   - HP 的可靠读取途径（`ActionResources.Resources` 的 HitPoints 条目 vs `EsvCharacter` 组件字段）。
   - 头顶浮字方案（`Ext.UI` Noesis 叠加 or `Osi.DebugText` 的显示效果）。
2. **需运行游戏验证**：
   - `Ext.Events.Tick` 实际频率（~30Hz？）与 `e.Time.Time` 的字段类型（milliseconds？）。
   - `Ext.IO.SaveFile` 的写盘时机/是否随存档回滚（推测不随档）。
   - Osiris DB 大表（如 `DB_<Mod>_Memory`）对存档大小与存档读写的性能影响。
   - anubis `events.*` 与 Osiris 事件的时序关系（是否同一引擎事件派发）——决定"SE 监听 + anubis 监听"是否重复。
   - `DEV_EnableAnubis` 在运行时切换 NPC 行为的实际效果与副作用。
   - 时间线（Timeline .lsf）能否被模组注入/替换（.lsf 在 pak 里，SE `Ext.IO.AddPathOverride` 或 `TimelineId` 覆盖）。
3. **资料缺口**：
   - 等级文件（Level .lsf）未解包——NPC 实例↔Character.txt 条目的**放置层**关系（模板引用 stats 名）未直接验证（依据 GLO_Journal.txt 的 S_ 常量间接确认）。
   - `Usage` 字段（flag 的 2/4 等取值）的语义未文档化。
   - ApprovalRatings 中 `id`（反应 GUID）与对话节点具体字段的对应关系未深挖（LLM 输出"表态"时需要）。
   - 对话文本的实际本地化文件位置未定位（`Localization` 目录未解包验证）。

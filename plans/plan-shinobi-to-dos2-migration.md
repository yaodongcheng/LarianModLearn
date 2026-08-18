# 计划：BG3 shinobi 技能全量迁移到 DOS2 忍术 mod

> 状态：**已执行（2026-08-18）**——22 术全量迁移完成，**中文显示已通**（Stats.lsb value 直写中文，六次排错后定型）；待 GM 全量实测（§7 验证清单）；喊话 spike 独立进行 | 关联：`plans/plan-llm-npc-ai-mod.md`、`mods/NarutoJutsu/` | 日期：2026-08-18

## Context

现有 DOS2 忍术原型（`mods/NarutoJutsu`）只有 5 术，已 GM 验证可加载。参考 BG3 shinobi class mod（`extracted/Reference_narutotest/`）。用户要求（含四点反馈）：
1. **全量搬迁（含瞳术/召唤）**，数值贴近 DOS2 原生平衡；
2. **中文本地化**（方案必须写明本地化机制，见 §2）；
3. **还原火影战斗表现**，不止抄 shinobi mod 字段——如天照必须是"黑色不灭火焰"（见 §3）；
4. **技能设计要沉淀为通用规范**，后续可持续扩充火影忍术库（见 §5，新增技能=SOP 三步）；
5. **音效很重要 + 技能名喊话**：本轮落地原生音效链（五段），喊话单列为独立探索任务（见 §4.2）。

**关键机制（已逐一实测核实）**：
- DOS2 SkillData **无音效字段**（BG3 的 PrepareSound/CastSound/TargetSound 不迁移）。DOS2 音效链 = 准备/施放动画（自带音）→ CastTextEvent 施放帧触发 → CastEffect 学派 FX（自带音）→ DamageType 命中音 → 状态音效（FROZEN 有 SoundStart/Loop/Stop，BURNING 有 FX）。
- 学派：DOS2 Ability 合法值含 `None`；雷遁/风遁同属 **Air**（DOS2 无雷学派，风雷合一，已有原型遵循）。
- 召唤：Skill_Summon.txt `Template` = Character.txt 模板 GUID，须佐能乎召唤原生 `Summon_Incarnate_Giant_Character`。
- 状态 buff：StatusData `StatsId` → **SKILLBOOST_\***（定义于 Potion.txt，`type "Potion"` + `using "_SkillBoost"`）。
- 状态 DoT：StatusData `DamageEvent "OnTurn"` + `DamageStats "Damage_<名>"`（参照 BURNING→Damage_Burning 模式，自定义条目进 Data.txt，官方文件名 merge 语义）。
- 表面：Zone SurfaceType 合法值含 `FireCloud`、`FireCursed`（**诅咒之火**——天照黑炎的机制载体）。
- 中文本地化：DOS2 原生 `Localization/Chinese.pak`；mod 发 `Localization/Chinese/chinese.xml` 与 English/ 平行，游戏按语言设置查找。

## 1. 技能清单（22 术 = 5 已有 + 17 新增）

### 五遁（14 术；数值递进：Novice 2AP/100-140% / Adept 2-3AP/140-180% / Master 4AP/200-260%，Cooldown 2-3/3-4/4-6）

| 学派 | 技能 | id | 形态 | Tier | 参考来源 | 图标 | 状态链/表现还原 |
|---|---|---|---|---|---|---|---|
| 火 | 豪火球 | katon_goukakyu | Projectile | Adept | 已有 | Skill_Fire_Fireball | BURNING+燃面 |
| 火 | 凤仙火 | katon_housenka | Projectile | Novice | fenixflower | Skill_Fire_FlamingDaggers | ProjectileCount+Angle 扇形多发，BURNING |
| 火 | 天照 | katon_amaterasu | Zone | Master | Amaterasu | Skill_Fire_EpidemicOfFire | **黑炎**：SurfaceType FireCursed + 自定义状态 NRT_AMATERASU（OnTurn DoT，多回合"不灭"） |
| 水 | 水龙弹 | suiton_suiryudan | Projectile | Adept | 已有 | Skill_Water_RainOfBlood | WET+浇灭 |
| 水 | 水铁炮 | suiton_suijinha | Projectile | Novice | WaterSpit | Skill_Water_IceShard_Piercing | WET+水面（灭火） |
| 水 | 雾隐之术 | suiton_kirigakure | Shout | Novice | HiddenMistCloud | Skill_Air_Skillcrafting_SmokeCover | BLIND |
| 雷(Air) | 雷切 | raiton_raikiri | Rush | Adept | 已有 | Skill_Air_BlindingRadiance | SHOCKED，突进贯穿 |
| 雷(Air) | 千鸟 | raiton_chidori | Rush | Novice | Chidori | Skill_Air_ShockingTouch | SHOCKED，更快突进 |
| 雷(Air) | 麒麟 | raiton_kirin | Zone | Master | Kirin | Skill_Air_LightningBolt | SHOCKED，天降雷霆大范围 |
| 风(Air) | 大突破 | fuuton_daihakki | Shout | Novice | 已有 | Skill_Air_BlindingRadiance | KNOCKED_DOWN 击退 |
| 风(Air) | 螺旋丸 | fuuton_rasengan | Rush | Novice | Rasengan | Skill_Air_BlitzBolt | 近身旋转球：KNOCKED_DOWN+击退 |
| 风(Air) | 螺旋手里剑 | fuuton_rasenshuriken | Projectile | Master | Rasenshuri | Skill_Air_Superconductor | 大范围旋转手里剑，KNOCKED_DOWN |
| 土 | 土隆枪 | doton_doryusou | Zone | Adept | 已有 | Skill_Earth_FossilStrike | IMPALED |
| 土 | 砂暴 | doton_sabaku | Zone | Adept | HiddenSandStorm | Skill_Earth_Contamination | CreateSurface Mud + CRIPPLED |

### 瞳术（6 术，Ability "None"）

| 技能 | id | 形态 | Tier | 机制/表现还原 |
|---|---|---|---|---|
| 写轮眼 | doujutsu_sharingan | Shout | Novice | 自定义状态 NRT_SHARINGAN（StatsId→SKILLBOOST_NRT_Sharingan：暴击/闪避加成，写轮眼预判） |
| 万花筒写轮眼 | doujutsu_mangekyo | Shout | Adept | 自定义状态 NRT_MANGEKYO（更高加成） |
| 月读 | doujutsu_tsukuyomi | Target | Master | 240% Air 伤害 + FROZEN 2 回合（精神世界囚禁） |
| 神威 | doujutsu_kamui | **Teleportation** | Master | 空间扭曲：目标传送+坠落伤害（新形态） |
| 别天神 | doujutsu_koto | Target | Master | 100% + CHARMED 3 回合（无声精神支配） |
| 须佐能乎 | doujutsu_susanoo | **Summon** | Master | 召唤原生模板 Summon_Incarnate_Giant_Character（新形态） |

### 通用（2 术，Ability "None"）

| 技能 | id | 形态 | Tier | 机制 |
|---|---|---|---|---|
| 手里剑 | kunai | Projectile | Novice | 1AP 快速，Physical |
| 瞬身术 | shunshin | Rush | Novice | 2AP 纯位移 |

**不迁移**：影分身/尾兽玉（依赖 BG3 专属模板与九尾资源）、覆写原版技能。写轮眼门控玩法（RequirementConditions+HasStatus）本轮不做门控、直接可用（v2 可 Osiris 补）。

## 2. 中文本地化方案（写清楚）

- **键机制**：DOS2 技能条目 `data "DisplayName" "<键>"` + `data "DisplayNameRef" "|<键>|"`（竖线引用，已实测必须）；Description 同理。键是纯文本标识（如 `NRT_katon_amaterasu_DisplayName`），**游戏按键在本地化文件里查文本**。
- **双语言文件**（pak 根 `Localization/` 下平行目录，与原生 English.pak/Chinese.pak 同构）：
  - `Localization/English/english.xml`：英文文本（现有保留）；
  - `Localization/Chinese/chinese.xml`：中文文本，同键集合，`<content contentuid="<键>">中文</content>`，**无 version 属性**（加了会转换失败，已踩坑）。
- **游戏显示**：游戏语言=中文 → 查 Chinese 文件显示中文；=英文 → 英文文件。两文件键集合必须完全相等（生成器断言）。
- **覆盖范围**：22 术的中文名/描述 + 2 个自定义状态（写轮眼/万花筒）+ 自定义 DoT 状态（天照）。中文名用官方译名（火遁·豪火球之术、凤仙火、天照、水遁·水龙弹之术、水铁炮、雾隐之术、雷遁·雷切、千鸟、麒麟、风遁·大突破、螺旋丸、螺旋手里剑、土遁·土隆枪、砂暴、手里剑、瞬身术、写轮眼、万花筒写轮眼、月读、神威、别天神、须佐能乎）。
- **BG3 侧**：本轮不动（BG3 loca 已有英文 handle 键，中文 BG3 侧列为后续）。

## 3. 战斗表现还原（不止抄字段）

| 原著名场面 | DOS2 还原手段 |
|---|---|
| 天照=黑色不灭火焰 | **SurfaceType "FireCursed"（诅咒之火表面）+ 自定义 NRT_AMATERASU 状态**：OnTurn DoT 持续多回合、死亡前不灭（状态不可被普通浇灭语义）、本地化文案描述黑炎 |
| 千鸟/雷切=手握雷电突进 | Rush 形态（快速突进）+ SHOCKED 状态 + Air 学派施放 FX（手部雷电） |
| 麒麟=引天雷轰击 | Zone 大范围 + SHOCKED + 高 AP 蓄力 |
| 螺旋丸=近身旋转气弹 | Rush 近距离 + KNOCKED_DOWN + 击退 |
| 螺旋手里剑=巨型旋转手里剑 | Projectile 大爆炸半径 + KNOCKED_DOWN |
| 凤仙火=扇形多团火 | ProjectileCount 多枚 + Angle 扇形 + 各自 BURNING |
| 神威=空间扭曲 | Teleportation 形态（目标被卷入异空间、坠落） |
| 月读=精神囚禁 | FROZEN（无法行动=被困精神世界） |
| 别天神=无声支配 | CHARMED |
| 须佐能乎=巨人化 | 召唤巨型化身（Summon_Incarnate_Giant_Character） |
| 写轮眼=洞察预判 | 暴击/闪避加成状态 |

## 4. 音效方案

### 4.1 本轮落地：原生音效链（每术五段，全部原生资源，不新增音频）

| 阶段 | 机制 | 配置 |
|---|---|---|
| 准备 | 结印动画自带音 | PrepareAnimationInit/Loop 按形态（target/dash/geo/zone/voodoo/summon 系列，均原生名） |
| 施放帧 | CastTextEvent | `"cast"`（全形态；Summon 另有 CastEffectTextEvent） |
| 施放 FX | 学派特效自带音 | CastEffect `RS3_FX_Skills_{Fire/Water/Air/Earth}_Cast_Hand_01:Dummy_FX`；瞳术：写轮眼/万花筒/月读→Air、神威/别天神→Voodoo、须佐→原生召唤全链（PrepareEffect+TargetCastEffect） |
| 命中 | 伤害类型自动 | DamageType Fire/Water/Air/Earth/Physical |
| 持续 | 状态音效 | 原生状态（FROZEN 有 SoundStart/Loop/Stop；其余自带 FX）；天照 DoT 状态可配 SoundStart/Loop/Stop（复用游戏内火焰音效名） |

### 4.2 独立探索任务（spike）：技能名喊话

**现状约束**：DOS2 音频=Wwise；SkillData 无音效字段；自定义音频需确认 pak 内 .wem 能否被播放及触发事件如何注册。**本轮网络不可达**（WebSearch/WebFetch 全部失败），无法在线验证社区方案，故拆为独立任务，不阻塞 22 术迁移。

**可行链路（待逐环验证）**：
1. **素材**：火影招式喊话（如《究极风暴》系列语音包，Bilibili/YouTube/Nexus 有流传）——需用户协助获取音频文件（我无法下载视频音频）；个人 mod 非商用可用。
2. **转换**：ogg/mp3 → .wem（Wwise 官方免费版，或社区 ww2ogg 逆向工具链）；事件注册需要 .bnk（Wwise 工程）。
3. **打包**：LSLib Divine create-package 可打入任意文件（已验证能力）。
4. **触发**：候选三路——(a) 动画文本事件挂音频（最原生，需确认事件名绑定方式）；(b) SE 音频 API（BG3SE/DOS2SE v60+ 已装，需查 API 表）；(c) 自定义状态 SoundStart（仅状态生效时，非施放瞬间）。
5. **验证**：最小试验 pak（1 个 .wem + 触发）实机测试。

**spike 产物**：`docs/custom-voice-sfx-spike.md`（链路各环节验证结论 + 可用性判定），判定可行后再排期"22 句台词包"。

## 5. 通用技能设计规范（面向持续扩充）

新增 `mods/NarutoJutsu/spec/DESIGN.md`，沉淀可复用的设计规则：

1. **条目即数据**：一个忍术 = jutsus.json 一条记录，schema 固定（id/nameCn/nameEn/element/dos2{shape,ability,tier,ap,cooldown,dmgMult,dmgType,properties,radii,icon,anim*,castEffect}/bg3? 可选）。
2. **命名规则**：`NRT_<遁系>_<术名>`（katon_/suiton_/raiton_/fuuton_/doton_/doujutsu_）；BG3/DOS2 双形态可共享 id。
3. **数值平衡表**：Tier→AP/Cooldown/Damage Multiplier 区间（§1 表）；新增术按此取值。
4. **形态选型表**：效果意图→形态（远程单体→Projectile、近身位移→Rush、以己为心→Shout、区域→Zone、空间操作→Teleportation、召唤→Summon）+ 该形态必填字段清单。
5. **音效五段规则**（§4.1）：形态→动画名映射表；学派→CastEffect 映射表。
6. **状态复用/新建规则**：能复用原生状态（BURNING/WET/SHOCKED/…）不新建；必须新建时（黑炎/写轮眼）走 Status_<官方文件>.txt + Data.txt 模式。
7. **本地化规则**：每术必配 nameCn/nameEn + descriptionCn/descriptionEn，生成器自动产出双语言 XML 并断言键对等。
8. **新增技能 SOP**：写 JSON 条目 → 跑生成器（含自检断言）→ build.ps1 打包 → GM 验证（加载/显示/音效/表现）。

## 6. 实施步骤

1. `spec/jutsus.json`：新增 17 术（仅 dos2 段）+ 自定义状态段（写轮眼/万花筒/天照 DoT 的 StatsId/DamageStats 字段）。
2. `tools/jutsu_gen/jutsu_gen.py`：
   - 新形态 Teleportation（Height/Acceleration/TeleportDelay/TeleportSelf，参照 vanilla `Teleportation_FreeFall`）、Summon（Lifetime/SummonLevel/Template/SummonCount/FXScale/PrepareEffect/TargetCastEffect，参照 vanilla `Summon_EnemyDemon_Doctor`）；
   - `Ability "None"` 直接输出；
   - 自定义状态生成：Status_CONSUME.txt（NRT_SHARINGAN/NRT_MANGEKYO）+ Status_DAMAGE.txt（NRT_AMATERASU）+ Potion.txt（SKILLBOOST_\*）+ Data.txt（Damage_NRT_Amaterasu），均官方文件名；
   - 中文本地化：`DOS2/Localization/Chinese/chinese.xml` + English.xml 双输出，键集合断言；
   - gen_bg3 跳过无 bg3 段的术（现有 5 术 BG3 不变）。
3. 新增 `spec/DESIGN.md`（§5 内容）。
4. 打包：`powershell -File mods/NarutoJutsu/build.ps1`。
5. 知识库沉淀：`knowledge/stat-file-conventions.md`（无音效字段结论/Ability None/Teleportation·Summon 模板/StatsId→SKILLBOOST/OnTurn DoT 自定义状态模式）；`knowledge/localization.md`（Chinese.xml 平行结构）；新增 `docs/custom-voice-sfx-spike.md` 任务说明（§4.2）。
6. `mods/NarutoJutsu/README.md`：22 术技能表 + 音效五段说明。

## 7. 验证

1. 生成器跑通，产物齐全（Skill_{Projectile,Rush,Shout,Zone,Teleportation,Summon}.txt、Status_*.txt、Potion.txt、Data.txt、english.xml、chinese.xml）。
2. 断言通过：DisplayNameRef/DescriptionRef 键 ∈ 双语言 XML，两 XML 键集合相等。
3. build.ps1 打包成功；Divine list-package 抽查 pak 含 `Localization/Chinese/chinese.xml`。
4. 安装至 `Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\`，GM 实测：22 术可见、中文显示、五阶段音效、天照黑炎表现（诅咒之火表面+持续燃烧）。
5. spike（喊话）单独验证（§4.2），不阻塞本计划。

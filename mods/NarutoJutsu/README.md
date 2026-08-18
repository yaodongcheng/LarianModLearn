# 火影忍术模组（NarutoJutsu）

> 状态：**v0.2.0** —— BG3 shinobi 技能全量迁移至 DOS2（22 术）。**中文显示已通**（2026-08-18：Stats.lsb value 直写中文机制定型）。
> 生成管线：`tools/jutsu_gen/`（规格表 → 配表 + Stats.lsb 映射 + 打包）。设计规范见 [spec/DESIGN.md](spec/DESIGN.md)。

## 本地化说明（重要）

- **文本本体在 `Public/NarutoJutsu/Localization/Stats/<Type>_<Field>.lsb` 的 value**（TranslatedStringKeys：UUID→handle→value），生成器自动产出。
- **value 直接写中文**（游戏显示 value 即中文）；英文模式也会显示中文——个人 mod 取舍。
- DOS2 游戏不查 mod 的语言 xml（Larian 官方不支持 mod 自定义本地化字符串），旧"双语言 xml"方案已废弃（文件保留无害）。
- 改技能名/描述 = 改 `spec/jutsus.json` 重新生成。

## 内容（22 术：五遁 14 + 瞳术 6 + 通用 2）

### 五遁（14 术）

| 忍术 | 元素 | 形态 | Tier | 图标 | 状态链/表现还原 |
|---|---|---|---|---|---|
| 火遁·豪火球之术 | 火 | Projectile | Adept | Skill_Fire_Fireball | BURNING + 燃面 |
| 凤仙火 | 火 | Projectile | Novice | Skill_Fire_FlamingDaggers | 5 连发扇形（Angle 60）+ BURNING |
| 天照 | 火 | Zone | Master | Skill_Fire_EpidemicOfFire | **黑炎**：FireCursed 表面 + NRT_AMATERASU 每回合 DoT |
| 水遁·水龙弹之术 | 水 | Projectile | Adept | Skill_Water_RainOfBlood | WET + 浇灭 |
| 水铁炮 | 水 | Projectile | Novice | Skill_Water_IceShard_Piercing | WET + 浇灭 |
| 雾隐之术 | 水 | Shout | Novice | Skill_Air_Skillcrafting_SmokeCover | BLIND（纯功能术，无伤害） |
| 雷遁·雷切 | 雷(Air) | Rush | Adept | Skill_Air_BlindingRadiance | 突进贯穿 + SHOCKED |
| 千鸟 | 雷(Air) | Rush | Novice | Skill_Air_ShockingTouch | 更快突进 + SHOCKED |
| 麒麟 | 雷(Air) | Zone | Master | Skill_Air_LightningBolt | 天降雷霆 + SHOCKED + 电面 |
| 风遁·大突破 | 风(Air) | Shout | Novice | Skill_Air_BlindingRadiance | 击退 + KNOCKED_DOWN |
| 螺旋丸 | 风(Air) | Rush | Novice | Skill_Air_BlitzBolt | 近身球击 + KNOCKED_DOWN |
| 螺旋手里剑 | 风(Air) | Projectile | Master | Skill_Air_Superconductor | 大爆炸半径 + KNOCKED_DOWN |
| 土遁·土隆枪 | 土 | Zone | Adept | Skill_Earth_FossilStrike | 地刺 + IMPALED |
| 砂暴 | 土 | Zone | Adept | Skill_Earth_Contamination | 流沙表面 + CRIPPLED |

### 瞳术（6 术，Ability None）+ 通用（2 术）

| 忍术 | 形态 | Tier | 机制/表现还原 |
|---|---|---|---|
| 写轮眼 | Shout | Novice | NRT_SHARINGAN 状态：暴击/闪避 +5%（StatsId→SKILLBOOST） |
| 万花筒写轮眼 | Shout | Adept | NRT_MANGEKYO 状态：暴击/闪避 +10% |
| 月读 | Target | Master | 240% Air 伤害 + FROZEN 2 回合（精神囚禁） |
| 神威 | Teleportation | Master | 目标卷入异空间掷落（Height 5 坠落伤害） |
| 别天神 | Target | Master | CHARMED 3 回合（无声支配） |
| 须佐能乎 | Summon | Master | 召唤巨人化身 Summon_Incarnate_Giant_Character（FXScale 150） |
| 手里剑 | Projectile | Novice | 1AP 快速，Physical |
| 瞬身术 | Rush | Novice | 2AP 纯位移 |

**不迁移**：影分身/尾兽玉（依赖 BG3 专属模板与九尾资源）；写轮眼门控（RequirementConditions+HasStatus）本轮不做，v2 可 Osiris 补。

## 自定义状态

| 状态 | 类型 | 机制 |
|---|---|---|
| NRT_SHARINGAN | CONSUME（Status_CONSUME.txt） | StatsId → SKILLBOOST_NRT_Sharingan（Potion.txt）：CriticalChance 5 / DodgeBoost 5 / 3 回合 |
| NRT_MANGEKYO | CONSUME | SKILLBOOST_NRT_Mangekyo：CriticalChance 10 / DodgeBoost 10 / 4 回合 |
| NRT_AMATERASU | DAMAGE（Status_DAMAGE.txt） | DamageEvent OnTurn + DamageStats Damage_NRT_Amaterasu（Weapon.txt）——天照黑炎每回合吞噬 |

## 音效五段（全部原生资源，无新增音频）

| 阶段 | 机制 | 配置 |
|---|---|---|
| 准备 | 结印动画自带音 | PrepareAnimationInit/Loop 按形态（target/dash/geo/voodoo/divine/totem 系列，原生动画名） |
| 施放帧 | CastTextEvent | `"cast"`（全形态；Summon 另有 CastEffectTextEvent） |
| 施放 FX | 学派特效自带音 | `RS3_FX_Skills_{Fire/Water/Air/Earth}_Cast_Hand_01:Dummy_FX`；瞳术 Air 系/Voodoo 系、须佐召唤全链 |
| 命中 | 伤害类型自动 | DamageType Fire/Water/Air/Earth/Physical |
| 持续 | 状态音效 | 原生状态自带（FROZEN SoundStart/Loop/Stop） |

> ⚠️ DOS2 SkillData **无音效字段**（BG3 的 PrepareSound 等不迁移）；技能名喊话（自定义语音）是独立 spike，见 `docs/custom-voice-sfx-spike.md`。

## 机制映射（配表仿制原理）

- **忍术 = 技能条目**（DOS2 `SkillData`），复刻原生条目的完整字段集（火球/冲锋/怒吼/区域/单体/传送/召唤）
- **查克拉 = ActionPoints**（AP 1-4）；**属性 = Ability 学派**（Fire/Water/Air/Earth，瞳术=None）
- **结印 = CastAnimation/CastEffect**（原生动画与学派 FX）；**术的效果 = SkillProperties 状态链**（状态+表面+机制）
- **等级 = Tier（Novice/Adept/Master）**；数值递进：Novice 2AP/100-140% / Adept 2-3AP/140-180% / Master 4AP/200-260%
- 参考：`docs/game-analysis-DOS2.md` C 节、`spec/DESIGN.md`

## 目录结构

```
mods/NarutoJutsu/
├── spec/jutsus.json                    ← 忍术规格表（唯一数据源，22 术 + 自定义状态）
├── spec/DESIGN.md                      ← 通用技能设计规范（新增技能 SOP）
├── DOS2/
│   ├── Mods/NarutoJutsu/meta.lsx       ← 模组清单（含 GM TargetMode + 战役 Dependencies）
│   ├── Localization/English/english.xml + Localization/Chinese/chinese.xml  ← 双语言（键集合断言相等）
│   ├── Public/NarutoJutsu/Stats/Generated/Data/
│   │   ├── Skill_{Projectile,Rush,Shout,Zone,Target,Teleportation,Summon}.txt
│   │   ├── Status_{CONSUME,DAMAGE}.txt + Potion.txt + Weapon.txt
│   └── NarutoJutsu_DOS2.pak            ← 打包产物
├── BG3/                                ← 仅含 bg3 段的 5 术（本轮不动）
└── build.ps1                           ← 重新打包
```

## 构建

```powershell
python tools/jutsu_gen/jutsu_gen.py        # 重新生成条目、状态与双语言本地化（含断言）
powershell -File mods/NarutoJutsu/build.ps1  # 转换 loca + 打包
```

## 安装与验证（需你在游戏里实测）

1. 复制 `DOS2.pak` 到 `%USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\`（游戏也扫描 `DefEd\Data\Mods\`，两处均已放置），启动器里勾选
2. GM 实测清单：
   - [ ] 22 术全部可见（技能书/角色 Skills 添加后）
   - [ ] 中文显示：技能名/描述/状态（写轮眼/万花筒/天照）——游戏语言设为中文
   - [ ] 音效五段：准备（结印音）→ 施放（cast 帧）→ 学派 FX 音 → 命中音 → 状态音（FROZEN 冻结音）
   - [ ] 天照黑炎：FireCursed 诅咒之火表面 + 每回合 DoT（不可被普通浇灭语义）
   - [ ] 须佐能乎：召唤巨人化身；神威：目标掷落坠落伤害；凤仙火：5 连发扇形
   - [ ] 数值手感：AP/冷却/伤害是否符合预期（改 `spec/jutsus.json` 后重新生成即可）

## 已知限制与后续

- **学习途径未配置**：技能需 GM/角色模板添加（本轮未做技能书/学习机制）
- **图标/投射物/动画全部复用原生资源**（图标为原生技能占位，非火影专属）
- **瞳术门控未做**：写轮眼→万花筒→须佐的 HasStatus 门控留 v2（Osiris 可补）
- **BG3 侧未迁移 17 术**：本轮为 DOS2 全量；BG3 中文本地化列为后续
- **技能名喊话**：独立 spike（`docs/custom-voice-sfx-spike.md`），判定可行后排期

## 与 LLM NPC 模组的关系

忍术包是"游戏机制配表"能力的验证件：LLM NPC 需要"动作面"（见 docs/integration-points.md §4），22 术提供了一套可被 LLM 调用的技能库（`Osi` 层直接可调，如 `Osi.Proc_StartDialog` 同级的技能释放函数）。

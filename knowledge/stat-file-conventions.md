# 统计文件命名与技能/法术条目（实测 2026-08-18）

## 核心规则：必须用官方文件名分发！

- ❌ 自定义文件名（如 `Skill_Naruto.txt`）实测**不被加载**（DOS2 GM 模式搜不到技能）
- ✅ 官方文件名分发（对照官方平台 mod `narutotest` 实测确认）
- 合并语义：多个模组的同名文件**按条目名合并**（vanilla 先例：Shared/GustavDev 同名文件共存）

**DOS2 官方统计文件名**（`Public/<Folder>/Stats/Generated/Data/`）：
`Character.txt`、`Armor.txt`、`Object.txt`、`Potion.txt`、`Shield.txt`、`Weapon.txt`（BG3 特有）、`Data.txt`、`Requirements.txt`、`Abilities.txt`、`Equipment.txt`、`ItemTypes.txt`、`ItemCombos.txt`、`ItemProgressionNames/Visuals.txt`、`TreasureGroups.txt`、`Crimes.txt`、`ItemColor.txt`，技能按形态：`Skill_Projectile.txt` / `Skill_Rush.txt` / `Skill_Shout.txt` / `Skill_Zone.txt` / `Skill_Target.txt` / `Skill_Wall.txt` / `Skill_Jump.txt` / `Skill_Rain.txt` / `Skill_Storm.txt` / `Skill_Summon.txt` / `Skill_Teleportation.txt` / `Skill_Tornado.txt` / `Skill_Quake.txt` / `Skill_Dome.txt` / `Skill_MultiStrike.txt` / `Skill_Cone.txt`；状态按类型：`Status_DAMAGE.txt` / `Status_EFFECT.txt` / `Status_ACTIVE_DEFENSE.txt` 等。

**BG3 官方统计文件名**：`Character.txt` / `Passive.txt` / `Interrupt.txt` / `Object.txt` / `Weapon.txt` / `Armor.txt` / `Data.txt` / `Crimes.lsx` / `XPData.txt` / `SpellSet.txt`，技能按形态：`Spell_Projectile.txt` / `Spell_Rush.txt` / `Spell_Shout.txt` / `Spell_Target.txt` / `Spell_Wall.txt` / `Spell_Zone.txt` / `Spell_Throw.txt` / `Spell_Teleportation.txt` / `Spell_ProjectileStrike.txt`；状态：`Status_BOOST.txt` / `Status_DOWNED.txt` / `Status_INCAPACITATED.txt` / `Status_INVISIBLE.txt` 等。

## DOS2 关键认知（2026-08-18 全量迁移实测）

- **SkillData 无音效字段**（BG3 的 PrepareSound/CastSound/TargetSound 不迁移）。DOS2 音效链 = 动画自带音（PrepareAnimationInit/Loop）→ CastTextEvent `"cast"` 施放帧 → CastEffect 学派 FX 自带音（`RS3_FX_Skills_{Fire/Water/Air/Earth}_Cast_Hand_01:Dummy_FX`）→ DamageType 命中音 → 状态音效（FROZEN 有 SoundStart/Loop/Stop = `Status_Tex_Frozen_*`）
- **Ability `"None"` 合法**（vanilla 敌技/瞳术类同款，如 Summon_EnemyDemon_Doctor）；写轮眼/神威/须佐等瞳术直接用
- **纯功能术可不写伤害字段**（雾隐/写轮眼/瞬身：无 Damage Multiplier/DamageType，参照 Target_SourceVampirism 无伤害字段）
- **Zone 形态有原生 `SurfaceType` 字段**（对照 `Zone_EnemyLaserRayCursed`：`data "SurfaceType" "FireCursed"` —— 天照黑炎机制载体）；另有 `CreateSurface,<半径>,,<表面类型>,<强度>` 属性可铺表面（Mud/Electric 等）
- **Projectile 扇形多发**：`ProjectileCount` + `Angle`（度，ArrowSpray 用 Angle 60 描述 16 箭扇形）
- **Target 形态**（单体直击）：`CanTargetCharacters "Yes"` / `CanTargetItems "No"` / `CanTargetTerrain "No"`（对照 Target_SourceVampirism）
- **Teleportation 形态**（空间操作，对照 Teleportation_FreeFall）：`Height`/`Acceleration`/`TeleportDelay`/`TeleportSelf`/`PrepareEffect`/`DisappearEffect`/`ReappearEffect`——投掷目标升空坠落=空间扭曲表现（神威）
- **Summon 形态**（对照 Summon_Incarnate / Summon_EnemyDemon_Doctor）：`Lifetime`/`SummonLevel`/`Template`(+`TemplateAdvanced`/`TemplateOverride`)/`SummonCount`/`FXScale`/`PrepareEffect`/`TargetCastEffect`/`CastEffectTextEvent`。须佐 = Template 巨人化身 GUID `13f9314d-e744-4dc5-acf2-c6bf77a04892`（= vanilla TemplateAdvanced，Character.txt 的 Summon_Incarnate_Giant_Character）
- **状态增益 StatsId → SKILLBOOST_**：StatusData `StatsId` 引用 `Potion.txt` 条目（`type "Potion"` + `using "_SkillBoost"`，参照 SKILLBOOST_Karma），合法字段：CriticalChance/DodgeBoost/AccuracyBoost/DamageBoost/Duration/StatusIcon 等
- **状态 DoT（OnTurn）**：StatusData `DamageEvent "OnTurn"` + `DamageStats "<名>"`（参照 BURNING→Damage_Burning）。**DoT 伤害条目在 Weapon.txt**（`type "Weapon"`，字段 Damage Type/Damage/Damage Range/DamageFromBase）——**不在 Data.txt**（Data.txt 只有 `key` 全局值）
- **状态 DisplayNameRef 用裸键**（无竖线引用，与技能不同）

## DOS2 本地化映射表：Public/<Folder>/Localization/Stats/*.lsb（2026-08-18 定型）

- **文本本体在这里**：`Stats/<Type>_<Field>.lsb`（TranslatedStringKeys 资源），条目 `UUID → handle → value`，游戏直接显示 value。
- `UUID` = 条目 DisplayName/Description 字段值（**必须完全一致**，含 `_DisplayName` 后缀）；`handle` 可自造 `h<md5(英文文本)>`；`value` **直接写中文**（个人 mod 取舍）。
- 生成：.lsx（头 `lslib_meta="v1,bswap_guids"`）→ `Divine -g dos2de convert-resource` → .lsb。
- 对照 vanilla：`Public/Shared/Localization/Stats/Projectile_DisplayName.lsb`（Shared.pak）。
- 完整链路见 `knowledge/localization.md`。

## DOS2 技能条目模板（SkillData，火球示例）

```txt
new entry "NRT_katon_goukakyu"
type "SkillData"
data "SkillType" "Projectile"          ← 形态（决定放哪个文件）
data "ForGameMaster" "Yes"
data "Ability" "Fire"                  ← 学派：Fire/Water/Air/Earth/None
data "Tier" "Adept"                    ← Novice/Adept/Master（对应学派等级需求）
data "ActionPoints" "3"                ← 查克拉≈AP
data "Cooldown" "4"
data "Damage Multiplier" "150"
data "Damage Range" "10"
data "DamageType" "Fire"               ← 元素
data "SkillProperties" "BURNING,100,2;Ignite;CreateSurface,3,,Fire,100"  ← 效果链
data "TargetRadius" "13" / "AreaRadius" "4" / "HitRadius" "1"(Rush)
data "DeathType" "Incinerate"
data "Template" "<投射物GUID>"          ← Projectile 形态必须有（复用现有投射物）
data "Icon" "Skill_Fire_Fireball"      ← 复用现有图标占位
data "DisplayName" "<id>_DisplayName" / "DisplayNameRef" "|<id>_DisplayName|"  ← 竖线引用本地化键（裸文本实测显示异常，见 dos2-gm-mode-mod-loading.md）
data "Description" "<id>_Description" / "DescriptionRef" "|<id>_Description|"
data "PrepareAnimationInit"/"PrepareAnimationLoop"/"CastAnimation"/"CastTextEvent"/"CastEffect"  ← 结印动画
data "Magic Cost" "0"
```
Rush 另需 `Requirement "MeleeWeapon"`、`TargetConditions "!Ally"`；Zone 可用 `SurfaceType`+`SurfaceStatusChance`（SurfaceType 见上节黑炎用法）。

## BG3 法术条目模板（SpellData，火矢/天照示例）

```txt
new entry "NRT_katon_goukakyu"
type "SpellData"
data "SpellType" "Projectile"          ← 形态
data "Level" "2"                       ← 法术等级
data "SpellSchool" "Evocation"
data "SpellProperties" "GROUND:SurfaceChange(Ignite);GROUND:SurfaceChange(Melt)"
data "TargetRadius" "18"
data "SpellRoll" "Attack(AttackType.RangedSpellAttack)"   ← Projectile
data "SpellSuccess" "DealDamage(3d6,Fire,Magical);ApplyStatus(BURNING,100,2)"
data "TargetConditions" "not Self() and not Dead()"
data "Trajectories" "<GUID>"           ← 投射物轨迹
data "Icon" "Spell_Evocation_FireBolt"
data "DisplayName" "h<handle>;1"       ← 本地化 handle（见 localization.md）
data "TooltipDamageList" "DealDamage(3d6,Fire)"
data "UseCosts" "ActionPoint:1;Chakra:4"   ← 自定义资源消耗（查克拉！参考 narutotest）
```
- Zone：`SpellRoll "not SavingThrow(...)"` + `SpellSuccess`/`SpellFail`（半伤）+ Surface 字段
- Rush：`UseCosts`、`SpellAnimation`（GUID 组）、`WeaponTypes "Melee"`、`RechargeValues "3-4"`
- 状态：`Status_*.txt` 里 `new entry "BURNING" type "StatusData"` + `StatusType`/`StatusEffect`/`DisplayNameRef`/`DescriptionRef`/`FormatColor`

## 状态条目（StatusData，DOS2 示例）

```txt
new entry "BURNING"
type "StatusData"
data "StatusType" "DAMAGE"
data "InitiateCombat" "Yes"
data "DisplayName" "BURNING_DisplayName" / "DisplayNameRef" "Burning"
data "Description" "BURNING_Description" / "DescriptionRef" "Deals [1] damage per turn."
data "StatusEffect" "RS3_FX_GP_Status_Burning_01"
data "FormatColor" "Fire"
```

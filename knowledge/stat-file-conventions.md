# 统计文件命名与技能/法术条目（实测 2026-08-18）

## 核心规则：必须用官方文件名分发！

- ❌ 自定义文件名（如 `Skill_Naruto.txt`）实测**不被加载**（DOS2 GM 模式搜不到技能）
- ✅ 官方文件名分发（对照官方平台 mod `narutotest` 实测确认）
- 合并语义：多个模组的同名文件**按条目名合并**（vanilla 先例：Shared/GustavDev 同名文件共存）

**DOS2 官方统计文件名**（`Public/<Folder>/Stats/Generated/Data/`）：
`Character.txt`、`Armor.txt`、`Object.txt`、`Potion.txt`、`Shield.txt`、`Weapon.txt`（BG3 特有）、`Data.txt`、`Requirements.txt`、`Abilities.txt`、`Equipment.txt`、`ItemTypes.txt`、`ItemCombos.txt`、`ItemProgressionNames/Visuals.txt`、`TreasureGroups.txt`、`Crimes.txt`、`ItemColor.txt`，技能按形态：`Skill_Projectile.txt` / `Skill_Rush.txt` / `Skill_Shout.txt` / `Skill_Zone.txt` / `Skill_Target.txt` / `Skill_Wall.txt` / `Skill_Jump.txt` / `Skill_Rain.txt` / `Skill_Storm.txt` / `Skill_Summon.txt` / `Skill_Teleportation.txt` / `Skill_Tornado.txt` / `Skill_Quake.txt` / `Skill_Dome.txt` / `Skill_MultiStrike.txt` / `Skill_Cone.txt`；状态按类型：`Status_DAMAGE.txt` / `Status_EFFECT.txt` / `Status_ACTIVE_DEFENSE.txt` 等。

**BG3 官方统计文件名**：`Character.txt` / `Passive.txt` / `Interrupt.txt` / `Object.txt` / `Weapon.txt` / `Armor.txt` / `Data.txt` / `Crimes.lsx` / `XPData.txt` / `SpellSet.txt`，技能按形态：`Spell_Projectile.txt` / `Spell_Rush.txt` / `Spell_Shout.txt` / `Spell_Target.txt` / `Spell_Wall.txt` / `Spell_Zone.txt` / `Spell_Throw.txt` / `Spell_Teleportation.txt` / `Spell_ProjectileStrike.txt`；状态：`Status_BOOST.txt` / `Status_DOWNED.txt` / `Status_INCAPACITATED.txt` / `Status_INVISIBLE.txt` 等。

## DOS2 技能条目模板（SkillData，火球示例）

```txt
new entry "NRT_katon_goukakyu"
type "SkillData"
data "SkillType" "Projectile"          ← 形态（决定放哪个文件）
data "ForGameMaster" "Yes"
data "Ability" "Fire"                  ← 学派：Fire/Water/Air/Earth/...
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
data "DisplayName" "<id>_DisplayName" / "DisplayNameRef" "<loca键>"
data "Description" "<id>_Description" / "DescriptionRef" "<loca键>"
data "PrepareAnimationInit"/"PrepareAnimationLoop"/"CastAnimation"/"CastTextEvent"/"CastEffect"  ← 结印动画
data "Magic Cost" "0"
```
Rush 另需 `Requirement "MeleeWeapon"`、`TargetConditions "!Ally"`；Zone 可用 `SurfaceType`+`SurfaceStatusChance`。

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

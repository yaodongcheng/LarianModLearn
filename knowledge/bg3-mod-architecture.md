# BG3 模组完整架构（参考 shinobi class mod 逆向，2026-08-18）

> 参考对象：用户从官方模组平台下载的 shinobi class mod（pak `narutotest_38798f9c-704c-3330-1cvk.pak`，解包于 `extracted/Reference_narutotest/`）。
> 这是 BG3 官方平台 mod 的完整结构教科书——**我们的 NarutoJutsu 目前只有 Stats 层，缺学习途径/资源系统**。

## 完整分层

```
Mods/<Folder>/
├── meta.lsx                        ← 清单（Dependencies 含官方 UI 模组 + Gustav 主战役）
├── Localization/English/english.xml ← 本地化（handle 键）
└── GUI/Assets/...                  ← 图标（技能/资源/职业图标 .DDS）

Public/<Folder>/
├── Stats/Generated/Data/Spell_*.txt, Status_*.txt, Passive.txt, Character.txt  ← 统计（官方文件名！）
├── ActionResourceDefinitions/ActionResourceDefinitions.lsx   ← 自定义资源（查克拉）
├── ClassDescriptions/ClassDescriptions.lsx                    ← 职业（Shinobi + 子职业）
├── Progressions/Progressions.lsx                              ← 成长表（技能解锁）
├── Lists/SpellLists.lsx + PassiveLists.lsx                    ← ★技能组/被动组资源（2026-08-18 实测纠正）
├── CharacterCreationPresets/AbilityDistributionPresets.lsx    ← 建卡预设
└── Content/[PAK]_<mod>/*.lsf                                  ← 特效 EffectBank 等（不是技能组！）
```

## 关键机制（抄作业要点）

### 1. 自定义 ActionResource（查克拉）
`ActionResourceDefinitions.lsx`：
```xml
<node id="ActionResourceDefinition">
  <attribute id="Name" type="FixedString" value="Chakra"/>
  <attribute id="ReplenishType" type="FixedString" value="ShortRest"/>
  <attribute id="ShowOnActionResourcePanel" type="bool" value="true"/>
  <attribute id="UUID" type="guid" value="1d2d2674-b76b-45bc-8604-e8134de5c17a"/>
  <attribute id="DisplayName"/Description" type="TranslatedString" handle="h..."/>
</node>
```
技能消耗：`data "UseCosts" "ActionPoint:1;Chakra:4"`（SpellData 里直接写）

### 2. 职业（ClassDescriptions.lsx）
```xml
<node id="ClassDescription">
  <attribute id="Name" type="FixedString" value="Shinobi"/>
  <attribute id="PrimaryAbility" type="uint8" value="2"/>
  <attribute id="SpellCastingAbility" type="uint8" value="5"/>
  <attribute id="ProgressionTableUUID" type="guid" value="6337512d-..."/>  ← 指向成长表
  <attribute id="BaseHp" type="int32" value="12"/> / <attribute id="HpPerLevel" type="int32" value="7"/>
  <attribute id="CanLearnSpells" type="bool" value="true"/>
  <attribute id="LearningStrategy" type="uint8" value="1"/>
  <attribute id="MustPrepareSpells" type="bool" value="false"/>
  ...（UUID、DisplayName/Description handle）
</node>
```
子职业：`ParentGuid` 指向主职业 UUID。

### 3. 成长表（Progressions.lsx）—— 技能解锁的核心
```xml
<node id="Progression">
  <attribute id="TableUUID" type="guid" value="6337512d-..."/>   ← 职业表 UUID
  <attribute id="Level" type="int32" value="1"/>                 ← 等级
  <attribute id="Selectors" type="LSString" value="AddSpells(<技能组UUID>);SelectPassives(<被动组UUID>,1,...);SelectSkills(...);SelectAbilityBonus(...)"/>
</node>
```
- `AddSpells(<UUID>)` 引用的 UUID = Content/[PAK]_<mod>/ 下的**技能组资源**（.lsf，UUID 命名）
- 引擎在角色达到 Level 时执行 Selectors → 技能进法术书
- 多个 Progression 节点共用同一 TableUUID = 每级一条

### 4. 技能组资源（Lists/SpellLists.lsx —— 2026-08-18 实测纠正！）
⚠️ 此前误记为 Content/[PAK]_<mod>/ 下的 UUID .lsf——实测那些是 **EffectBank 特效资源**。真正的技能组在 `Public/<mod>/Lists/SpellLists.lsx`：
```xml
<node id="SpellList">
  <attribute id="Name" type="FixedString" value="Shinobi1"/>
  <attribute id="Spells" type="LSString" value="Target_SneakAttack1;Projectile_SneakAttack1;Projectile_Kunai;"/>
  <attribute id="UUID" type="guid" value="3445c8cb-6ed6-4db9-b676-b03bc315f361"/>  ← Progressions AddSpells(<此UUID>)
</node>
```
被动组同理：`Lists/PassiveLists.lsx`（`SelectPassives(<UUID>,...`）。**纯 txt 路线替代**：`SpellSet.txt`（`new spellset "X"` + `add spell "..."`）——未经官方平台 mod 验证但为文本格式，可作为轻量替代（待验证 ⚠️）。

### 5. 技能定义要点（shinobi 实例）
- `Projectile_Kunai`：`SpellRoll "Attack(AttackType.RangedUnarmedAttack)"`、`UseCosts "BonusActionPoint:1"`、`SpellSuccess "...;ApplyStatus(frseal,100,8)"`
- `Target_Amaterasu`：`RequirementConditions "HasStatus('emsactive', context.Source) or ..."`（**状态需求**——写轮眼/万花筒解锁条件）、`UseCosts "ActionPoint:1;Chakra:4"`、`SpellProperties "GROUND:ApplyStatus(...);GROUND:Summon(<uuid>, 10,,true,...);DealDamage(10,Fire)"`
- `SpellFlags "HasVerbalComponent;HasSomaticComponent;IsSpell;IsHarmful"`、`HitAnimationType "MagicalDamage_External"`
- 图标：自定义名（`"shuriken"`、`"rasenshuriken"`）+ GUI/Assets 里对应 .DDS

## 对我们的启示

1. 我们 BG3 mod 补"学习途径"的最小路径：`SpellSet.txt`（txt 技能组）→ 或完整照抄 ClassDescriptions+Progressions+UUID 资源（需 Toolkit）
2. 自定义状态条件（RequirementConditions + HasStatus）可实现"写轮眼解锁天照"式玩法
3. 查克拉 = ActionResourceDefinitions + UseCosts Chakra:N——比 AP 更贴近火影设定
4. 全部技能清单见 `docs/shinobi-class-skill-list.md`

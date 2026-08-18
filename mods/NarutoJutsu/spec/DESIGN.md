# 忍术技能设计规范（DESIGN.md）

> 面向持续扩充的通用规则：新增一个忍术 = 在 `spec/jutsus.json` 加一条记录 → 跑生成器 → 打包 → GM 验证。
> 本文件是"新增技能 SOP"（§8）与数值/形态/音效/状态的决策依据。所有规则来自 2026-08-18 实测（vanilla 对照条目见各节引用）。

## 1. 条目即数据

一个忍术 = `jutsus.json` 一条记录，schema 固定：

```json
{
  "id": "<NRT_<遁系>_<术名>>",      // 命名规则见 §2
  "nameCn": "中文名", "nameEn": "English",
  "element": "Fire|Water|Air|Earth|None",
  "descriptionCn": "中文描述", "descriptionEn": "English desc",
  "dos2": {                          // 必填，DOS2 配表数据
    "shape": "Projectile|Rush|Shout|Zone|Target|Teleportation|Summon",
    "ability": "Fire|Water|Air|Earth|None",
    "tier": "Novice|Adept|Master",
    "ap": 2, "cooldown": 3,
    "dmgMult": 150, "dmgType": "Fire",      // 纯功能术可不写（雾隐/写轮眼/瞬身）
    "properties": "BURNING,100,2",          // 状态链 / 表面 / 机制
    ...形态必填字段（见 §4）...
    "icon": "Skill_<学派>_<原生名>",
    "animPrepareInit/Loop", "animCast": "原生动画名",
    "castEffect": "RS3_FX_...:Dummy_FX"     // 可选，见 §5
  },
  "bg3": { ... }                   // 可选：有则同步生成 BG3 侧，无则仅 DOS2
}
```

## 2. 命名规则

- 技能 id：`<遁系>_<术名>`，遁系前缀 `katon_(火) / suiton_(水) / raiton_(雷) / fuuton_(风) / doton_(土) / doujutsu_(瞳术)`；通用术直接名词（`kunai`/`shunshin`）。
- 配表条目名 = `NRT_<id>`（SkillData / SpellData）。
- 本地化键 = `NRT_<id>_DisplayName` / `NRT_<id>_Description`（BG3 侧是 handle 键，DOS2 侧是纯文本键）。
- 自定义状态 id：`NRT_<大写名>`（如 NRT_SHARINGAN）；增益条目 `SKILLBOOST_NRT_<Xxx>`；DoT 伤害条目 `Damage_NRT_<Xxx>`。
- BG3/DOS2 双形态共享 id（现有 5 术即如此）。

## 3. 数值平衡表

| Tier | AP | Cooldown | Damage Multiplier | 说明 |
|---|---|---|---|---|
| Novice | 1-2 | 2-3 | 100-140% | 1AP 例外（手里剑 60%） |
| Adept | 2-3 | 3-4 | 140-180% | |
| Master | 4 | 4-6 | 200-260% | 神威/月读等机制型可 100% |

- 伤害类型：火→Fire（死亡 Incinerate）、水→Water、雷/风→Air、土→Earth（死亡 Physical）、瞳术/通用→None/Physical。
- 状态时长（`<状态>,<概率>,<回合>`）：DoT/控制 2-3 回合，增益 3-4 回合。

## 4. 形态选型表（效果意图 → 形态）

| 效果意图 | 形态 | 必填/常用字段 | 参照原生条目 |
|---|---|---|---|
| 远程单体/多发 | Projectile | TargetRadius、AreaRadius、Template、ProjectileCount/Angle（扇形多发） | Fireball、ArrowSpray |
| 近身位移打击 | Rush | TargetRadius、HitRadius、Requirement(MeleeWeapon) | LightningCutter |
| 以己为心爆发 | Shout | AddWeaponRange、TargetConditions | WindBreakthrough |
| 区域持续/表面 | Zone | TargetRadius、AreaRadius、SurfaceType（黑炎用 FireCursed！） | Zone_EnemyLaserRayCursed |
| 单体直击 | Target | TargetRadius、CanTarget*(角色 Yes/物品 No/地形 No) | Target_SourceVampirism |
| 空间操作（传送/投掷） | Teleportation | Height、Acceleration、TeleportDelay、TeleportSelf、PrepareEffect/Disappear/ReappearEffect | Teleportation_FreeFall |
| 召唤 | Summon | Lifetime、SummonLevel、Template(+Advanced)、SummonCount、FXScale、PrepareEffect、TargetCastEffect | Summon_Incarnate / Summon_EnemyDemon_Doctor |

- Projectile 的 `Template` = 投射物模板 GUID（现有统一用火球模板 `04bdf5e2-3c6a-4711-b516-1a275ccbd720`，实测可加载）。
- Summon 的 `Template` = 角色模板 GUID：须佐用巨人化身 `13f9314d-e744-4dc5-acf2-c6bf77a04892`（= vanilla `TemplateAdvanced`，对应 Character.txt 的 `Summon_Incarnate_Giant_Character`）。
- 瞳术/通用 Ability 直接写 `"None"`（合法值，vanilla 敌技同款）。

## 5. 音效五段规则（全部原生资源，不新增音频）

| 阶段 | 机制 | 配置 |
|---|---|---|
| 准备 | 结印动画自带音 | PrepareAnimationInit/Loop 按形态：target(远程)/dash(突进)/geo(区域)/voodoo(爆发)/divine(传送)/totem(召唤) 系列 |
| 施放帧 | CastTextEvent | `"cast"`（全形态；Summon 另有 CastEffectTextEvent `"cast"`） |
| 施放 FX | 学派特效自带音 | castEffect：`RS3_FX_Skills_{Fire/Water/Air/Earth}_Cast_Hand_01:Dummy_FX`；瞳术 Air 系用 Air、神威/别天神用 Voodoo（`RS3_FX_Skills_Voodoo_Attack_Precision_Blood_Hand_01:Dummy_FX`）、须佐用召唤全链 |
| 命中 | 伤害类型自动 | DamageType Fire/Water/Air/Earth/Physical |
| 持续 | 状态音效 | 原生状态自带（FROZEN 有 SoundStart/Loop/Stop = `Status_Tex_Frozen_*`）；自定义 DoT 状态可加 SoundStart/Loop/Stop（火焰音效名待实机验证） |

注意：**DOS2 SkillData 无音效字段**（BG3 的 PrepareSound/CastSound/TargetSound 不迁移）。施放音效完全靠动画事件 + 特效资源自带音。

## 6. 状态复用/新建规则

- **能复用原生状态不新建**：BURNING/WET/SHOCKED/KNOCKED_DOWN/IMPALED/BLIND/FROZEN/CHARMED/CRIPPLED 直接用。
- **必须新建时**（黑炎/写轮眼）走官方文件名分发三件套（生成器已实现，新增只需在 `statuses` 段加一条）：
  1. `Status_CONSUME.txt`（增益型）或 `Status_DAMAGE.txt`（DoT 型）——StatusData 条目；
  2. 增益型：`Potion.txt` 加 `SKILLBOOST_NRT_*`（`type "Potion"` + `using "_SkillBoost"`，合法字段：CriticalChance/DodgeBoost/AccuracyBoost/DamageBoost/Duration/StatusIcon），状态条目用 `StatsId` 引用；
  3. DoT 型：`Weapon.txt` 加 `Damage_NRT_*`（`type "Weapon"`，参照 `Damage_Burning`）——**注意在 Weapon.txt 不在 Data.txt**（Data.txt 只有 `key` 全局值）。
- 状态 DisplayNameRef 用**裸键**（无竖线引用，与技能不同）；键在双语言 XML 中。

## 7. 本地化规则

- 每术必配 nameCn/nameEn + descriptionCn/descriptionEn；状态同理。
- 生成器自动产出 `Localization/English/english.xml` + `Localization/Chinese/chinese.xml`（平行目录，与原生 English.pak/Chinese.pak 同构），游戏按语言设置查找。
- **两文件键集合必须完全相等**（生成器断言，缺键即报错）。
- 中文 XML 无 version 属性（加了会转换失败——已踩坑）。
- BG3 侧：loca 为 handle 键 + 英文（中文 BG3 侧列为后续任务）。

## 8. 新增技能 SOP（三步）

1. **写 JSON 条目**：在 `spec/jutsus.json` 的 `jutsus` 数组加一条记录（§1-§4 取字段）；需要自定义状态时在 `statuses`/`damageEntries` 加对应段（§6）。
2. **跑生成器**：`python tools/jutsu_gen/jutsu_gen.py`——生成配表 + 双语言 XML，断言自动检查（重复 id、缺本地化键、双语言键不等）。
3. **打包 + 验证**：`powershell -File mods/NarutoJutsu/build.ps1` → 装到 `Documents\...\Divinity Original Sin 2 Definitive Edition\Mods\` → GM 实测（加载/显示/音效五段/表现还原）。

**验证清单**（GM 模式）：技能可见 ✓ / 中文名与描述 ✓ / 准备-施放-命中-持续音效 ✓ / 天照黑炎（FireCursed 表面 + 每回合 DoT）✓ / 须佐能乎召唤巨人化身 ✓ / 神威投掷坠落 ✓。

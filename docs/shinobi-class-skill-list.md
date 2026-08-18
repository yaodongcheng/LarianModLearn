# shinobi class mod 技能清单（参考）

> 来源：用户从 BG3 官方模组平台下载的 **shinobi class mod**（pak 文件 `narutotest_38798f9c-704c-3330-1cvk.pak`，2026-08-18 解包）。
> 注意：这是第三方火影职业模组，与我们的 **NarutoJutsu** 原型（5 术）无关，仅作机制参考与游玩体验。
> 数据路径：`extracted\Reference_narutotest\Public\narutotest_<uuid>\Stats\Generated\Data\`

## 快速升级 / 直接加技能（BG3SE 控制台）

```lua
local c = Osi.GetHostCharacter()
Osi.SetLevel(c, 12)            -- 一键 12 级，职业成长表全解锁
Osi.AddSpell(c, "技能名")       -- 直接给技能（角色在前、技能名在后）
```

函数已从 BG3 本体 Osiris 反编译核实：`SetLevel(char, level)`（35 处）、`AddSpell(char, spell)`（102 处）、`Proc_LevelUp(char)` = 升 1 级。

## 每级解锁表（2026-08-18 实测 Progressions.lsx + Lists/SpellLists.lsx 交叉核对）

### 主职业 Shinobi（所有玩家，1-20 级）
| 级 | 拿到的技能 | 被动/特性 | 资源 |
|---|---|---|---|
| 1 | Projectile_Kunai、Target/Projectile_SneakAttack1 | FastMovement、UnarmoredDefense_Monk、SneakAttack_Unlock、MartialArts_DextrousUnarmedAttacks、ShinobiOrigin（起源被动） | 查克拉+3；轻甲/简易武器/手弩/长剑/细剑/短剑熟练；敏豁免 |
| 2 | **Target_Flicker（瞬身术）** | MartialArts_BonusStrike_Passive、BonusUnarmedStrike、FastHands | 查克拉+3 |
| 3 | （选子职业） | UnarmoredMovement_1 | 查克拉+3 |
| 4 | — | 专长点（feat）、SlowFall | 查克拉+4 |
| 5 | — | **ExtraAttack（额外攻击）** | 查克拉+4 |
| 6 | — | Evasion | 查克拉+4 |
| 7 | — | UnarmoredMovement_2 | 查克拉+4 |
| 8 | — | 专长点 | 查克拉+4 |
| 9 | — | UnarmoredMovement_DifficultTerrain | 查克拉+4 |
| 10 | — | 专长点 | 查克拉+4 |
| 11 | — | UnarmoredMovement_3、**sixpaths（六道）** | 查克拉+4 |
| 12 | — | 专长点 | 查克拉+4 |
| 13-20 | — | —（仅查克拉+4） | BG3 本体上限 12 |

### 子职业 IndraPath（宇智波线，3 级二选一）
| 级 | 技能 | 被动 |
|---|---|---|
| 3 | **Rush_Chidori（千鸟）**、Projectile_fireballjutsu（火球）、**Shout_sharingan_on（写轮眼）** | uchihablood（宇智波血统）；+魅力豁免/洞悉/调查/察觉 |
| 4 | Projectile_fenixflower（凤仙火） | — |
| 5 | Projectile_fireballjutsutwo（火球二式） | — |
| 6 | 五选一：**Target_kamui（神威）/ Target_tsuku（月读）/ Target_Amaterasu（天照）/ Target_koto（别天神）/ Wall_AmaWall** | mspassive、amaoffpassive（万花筒） |
| 7 | **Target_Kirin（麒麟）** | — |
| 8 | Projectile_AmaFireball（天照火球） | — |
| 9 | Shout_eternal（永恒） | **emspassive（永恒万花筒，替换 mspassive）** |
| 10 | **Shout_rin_on（轮回眼）** | — |
| 11 | **Shout_susarmor（须佐能乎）** | — |
| 12 | **Zone_IndraArrow（因陀罗之矢）** | — |

### 子职业 AshuraPath（鸣人线，3 级二选一）
| 级 | 技能 | 被动/资源 |
|---|---|---|
| 3 | **Rush_Rasengan（螺旋丸）**、Target_RemUnsummon | uzamakiblood、Jin、sclone1；查克拉+3+**九尾+1** |
| 4 | —（技能组为空！） | ntr1 |
| 5 | **Zone_rshuri（螺旋手里剑）** | — |
| 6 | **Target_MultiShadowClone（多重影分身）** | — |
| 7 | Target_conele | sagemodetoggle（仙人模式开关） |
| 8 | Target_invras（因陀罗之矢前置） | ntre（替换 ntr1）；九尾+5 |
| 9 | **Target_FlyRai（雷遁飞行）** | — |
| 10 | —（技能组为空！） | sclone2（替换 sclone1） |
| 11 | **Shout_kcm（九尾查克拉模式）** | — |
| 12 | **Projectile_tbb（尾兽玉）** | — |

> 注：SpellLists.lsx 里 `narutospells`（主职 1 级第二组）、`Ashura4`、`Ashura10` 的 Spells 为空——作者留空未填。另有一批**未挂进成长表**的旧技能组（sasukespells/fenixflower/Chirodi/flower8/10/12）与大量覆写原版技能（Projectile_EldritchBlast/FireBolt/MagicMissile 等），只能靠 AddSpell 手动给。

## 技能（SpellData，按形态）

### Projectile（投射）
Projectile_Kunai（手里剑）、Projectile_AmaFireball（天照火球）、Projectile_Rasenshuri（螺旋手里剑）、Projectile_fenixflower（凤仙火）、Projectile_fireballjutsu / fireballjutsutwo（火球术）、Projectile_WaterSpit、Projectile_tbb（尾兽玉）、Projectile_New_Stat_0、Projectile_EldritchBlast / FireBolt / MagicMissile / SneakAttack1（覆写原版）

### Rush（突进）
Rush_Chidori（千鸟）、Rush_Rasengan（螺旋丸）、Rush_Charger_Push_override、Rush_Rush（覆写）

### Shout（怒吼/光环）
Shout_sagemode（仙人模式）、Shout_sharingan_on/off（写轮眼）、Shout_rin_on（轮回眼）、Shout_kcm（九尾查克拉模式）、Shout_ninetailsrage / enhancedninetailsrage（九尾暴走）、Shout_ms_on（万花筒）、Shout_ems_on（永恒万花筒）、Shout_HiddenMistCloud（雾隐）、Shout_R_Apush / Repulsor（神罗天征系）、Shout_susarmor（须佐能乎）、Shout_Rage / Ragetest / EndRage、Shout_Stone*（须佐系列）

### Target（目标）
Target_Amaterasu（天照）+ _Move、Target_Kirin（麒麟）、Target_kamui（神威）、Target_koto（别天神）、Target_tsuku（月读）、Target_MultiShadowClone（多重影分身）、Target_ShadowClone1/2、Target_HiddenLeafClone（木叶分身）、Target_FlyRai（雷遁飞行）、Target_R_Push / R_Pull / R_Blackhole（天道系）、Target_Flicker（瞬身术）、Target_Sub（替身术）、Target_CallLightning、Target_invras（因陀罗之矢前置）、Target_RSwitch、Target_amaofftarget、Target_conele、Target_flyraitwo

### Zone（区域）
Zone_rshuri（螺旋手里剑）、Zone_clonershuri、Zone_IndraArrow（因陀罗之矢）、Zone_R_Wave、Zone_Sub1、Zone_BurningHandsConele

### Wall（墙）
Wall_AmaWall（天照火墙）、Wall_New_Stat_0

## 被动（Passive.txt）
ShinobiOrigin_Cloud（忍者起源）、uchihablood（宇智波血统）、uzamakiblood（漩涡血统）、sixpaths（六道）、Kurama（九尾）、emspassive/emstoggle（永恒万花筒）、cloudpsv、amaoffpassive、RageUnlock、MartialArts_*（体术）、FullSwing_Passive、SubPass/SubPass43、SEE_INVISIBILITY

## 状态（Status_*.txt）
BURNING_override、AMA_burning（天照之焰）/AMA_burning2/AMA_aura/AMA_owner/AMA_wall、FLYRAI_OWNER、RIN_active、SH_active、kamuitest、kotoactive、tsukudmg、SEE_INVISIBILITY(_SEENsh)、DOMINATE_PERSON

## 其他资源（mod 架构参考）
- 查克拉资源：`Public/<mod>/ActionResourceDefinitions/ActionResourceDefinitions.lsx`（Chakra/Kurama，ShortRest 回复）
- 职业：`ClassDescriptions/ClassDescriptions.lsx`（Shinobi + AshuraPath/IndraPath 子职业，ProgressionTableUUID）
- 成长表：`Progressions/Progressions.lsx`（TableUUID + Selectors: AddSpells/SelectPassives/SelectSkills）
- 技能组/特效：`Content/[PAK]_narutotest/*.lsf`（UUID 资源）
- 本地化：`Mods/<Folder>/Localization/English/english.xml`（handle 键）

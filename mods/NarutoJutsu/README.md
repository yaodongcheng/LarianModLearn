# 火影忍术原型模组（NarutoJutsu）

> 状态：**原型 v0.1** —— 纯配表仿制，验证"忍术→游戏机制"映射可行性与游戏内实际效果。
> 生成管线：`tools/jutsu_gen/`（规格表 → 配表条目 + 本地化 → 打包）。

## 内容（五遁各一术）

| 忍术 | 元素 | DOS2 形态 | BG3 形态 | 效果 |
|---|---|---|---|---|
| 火遁·豪火球之术 | 火 | Projectile | Projectile | 爆炸火球 + 灼烧 BURNING + 点燃地面 |
| 水遁·水龙弹之术 | 水/寒 | Projectile | Projectile | 水龙冲击 + 湿身 WET（DOS2） |
| 雷遁·雷切 | 雷 | Rush | Rush | 突进贯穿 + 电击 SHOCKED（DOS2） |
| 风遁·大突破 | 风 | Shout | Zone | 风压爆发 + 击倒/击退 |
| 土遁·土隆枪 | 土 | Zone | Zone | 地刺突刺 + 穿刺 IMPALED（DOS2）/ 击倒（BG3） |

## 机制映射（配表仿制原理）

- **忍术 = 技能/法术条目**（DOS2 `SkillData` / BG3 `SpellData`），复刻原生条目（火球术/雷切/激光射线/怒吼/震雷波）的完整字段集
- **查克拉 = ActionPoints / ActionResource**（DOS2 AP 2-3；BG3 ActionPoint:1）
- **属性 = Ability 学派 / SpellSchool + DamageType**（火=Fire、水=Water/Cold、雷=Air/Lightning、风=Air/Force、土=Earth/Bludgeoning）
- **结印 = CastAnimation/CastEffect**（复用原生施法动画占位，后续可换自定义）
- **术的效果 = SkillProperties/SpellSuccess 效果链**（状态+表面+伤害表达式）
- **等级 = Tier（Novice/Adept）/ Spell Level**
- 参考：`docs/game-analysis-DOS2.md` C 节、`docs/game-analysis-BG3.md` C 节

## 目录结构

```
mods/NarutoJutsu/
├── spec/jutsus.json                    ← 忍术规格表（唯一数据源）
├── DOS2/
│   ├── meta.lsx                        ← 模组清单（UUID 为占位，发布前需更换）
│   ├── Localization/English/english.xml
│   ├── Public/NarutoJutsu/Stats/Generated/Data/Skill_Naruto.txt
│   └── NarutoJutsu_DOS2.pak            ← 打包产物
├── BG3/
│   ├── meta.lsx
│   ├── Localization/English/english.{xml,loca}
│   ├── Public/NarutoJutsu/Stats/Generated/Data/Spell_Naruto.txt
│   └── NarutoJutsu_BG3.pak
└── build.ps1                           ← 重新打包
```

## 构建

```powershell
python tools/jutsu_gen/jutsu_gen.py        # 重新生成条目与本地化
powershell -File mods/NarutoJutsu/build.ps1  # 转换 loca + 打包
```

## 安装与验证（需你在游戏里实测）

1. 复制对应 .pak 到 Mods 目录：
   - BG3：`%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\`（官方模组管理器标准），并在模组管理器或 `modsettings.lsx` 启用
   - DOS2：`%USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\`（**DOS2 用 Documents，不是 LocalAppData**）；游戏也扫描 `DefEd\Data\Mods\`（本体战役文件夹同处）——两个位置当前均已放置，启动器里勾选
2. **pak 结构要点**（对照游戏本体 pak 实测）：`Mods/<Folder>/meta.lsx`（Config/ModuleInfo 格式）+ `Public/<Folder>/...` + `Localization/English/...`——工程形态（Toolkit 的 Projects/Mods/Public/Editor 四目录）不是发布形态
2. 验证清单：
   - [ ] 游戏正常启动、存档正常（无解析报错）
   - [ ] 技能/法术条目能否被游戏加载（**自定义文件名 Skill_Naruto.txt / Spell_Naruto.txt 是否被合并——若未加载，需改用官方同名文件**，这是本原型最大的未知项）
   - [ ] DOS2：给角色加技能后（控制台/书/修改角色 Skills），豪火球能否释放、伤害/燃烧/冷却是否符合预期
   - [ ] BG3：给角色加法术（SpellSet 或控制台 AddSpell），豪火球能否施放
   - [ ] 名字/描述是否正确显示（DOS2 纯字符串键；BG3 自造 handle——若显示原始 handle，说明 loca 查找方式不符，需换方案）

## 已知限制与后续

- **学习途径未配置**：原型只定义了技能本身；DOS2 需给角色模板 Skills 字段/技能书，BG3 需 Progressions/SpellSet——待实机验证后按"学习机制"补配
- **视觉为占位**：图标/投射物/动画全部复用原生资源
- **数值未平衡**：AP/伤害/冷却为估算，按手感调整只需改 `spec/jutsus.json` 后重新生成
- **meta.lsx UUID 为占位**：正式发布前生成新 GUID（两游戏模组唯一标识）
- 下一步可扩展：新 StatusData（如"灼烧加深"）、血继限界被动（BG3 PassiveData / DOS2 天赋）、自定义图标

## 与 LLM NPC 模组的关系

本原型是"游戏机制配表"能力的验证件：LLM NPC 需要"动作面"（见 docs/integration-points.md §4），忍术包提供了一套可被 LLM 调用的技能库（`Osi` 层直接可调，如 `Osi.Proc_StartDialog` 同级的技能释放函数）。

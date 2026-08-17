# 忍术模组实机验证指南

> 适用：`NarutoJutsu_DOS2.pak` / `NarutoJutsu_BG3.pak`（v0.1 原型）
> 原则：先验证"模组被游戏接受"，再验证"技能可用"，最后验证"效果符合预期"。
> 关键未知项：**自定义文件名（Skill_Naruto.txt / Spell_Naruto.txt）能否被游戏统计系统合并**——这是第一步就要确认的。

---

## A. DOS2 验证（推荐 GM 模式，免装 SE）

### A1. 安装与启用
1. 复制 `mods\NarutoJutsu\DOS2\NarutoJutsu_DOS2.pak` 到（**DOS2 用 Documents，不是 LocalAppData**——后者是 BG3 的惯例）：
   `%USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\`
   （2026-08-17 实测：游戏也扫描 `G:\...\DefEd\Data\Mods\`——myFirstMod 即在此被识别；两个位置当前都已放置本 pak）
2. 启动游戏 → 主菜单 → **Mods（模组）** → 列表里找到 NarutoJutsu → **启用**（钩上/Install）
3. 模组启用在**新建游戏或 GM 会话**时生效（对已有存档需在存档的模组列表确认）

### A2. 用 GM 模式测试（DOS2 官方测试环境，无需 SE）
1. 主菜单 → **Game Master Mode** → 创建/打开一个会话（单人即可）
2. 在 GM 界面放置一个角色（角色面板拖出任意 NPC 或自建角色）
3. 选中角色 → 打开**角色编辑器（inspector）** → 找到 **Skills（技能）** 列表 → 搜索 `NRT_` 前缀
   - ✅ 能看到 `NRT_katon_goukakyu` 等 5 个技能 → **模组统计被加载，自定义文件名生效**
   - ❌ 列表里没有 → 自定义文件名未被合并 → 回填方案：把条目并入官方同名文件（见 D 节）
4. 给角色加上技能 → 检查角色面板技能描述/图标
   - ✅ 显示英文名与描述 → 本地化字符串键方案生效
   - ❌ 显示原始文本/空白 → 本地化方案需调整
5. 让玩家角色进入会话，施放技能（需要技能学派等级满足 Tier 需求：Adept 需要对应学派 3 级，可通过角色编辑器把 Fire/Water/Air/Earth 学派等级调高）
6. 观察：伤害数值、状态（灼烧/湿身/电击/穿刺/击倒）、冷却与 AP 消耗

### A3. 备选：装 DOS2SE 用控制台
- 复制 `tools\DOS2SE-Updater-v5\dxgi.dll` 到 `G:\SteamLibrary\steamapps\common\Divinity Original Sin 2\DefEd\bin\`（游戏首次启动会自动更新 SE）
- 控制台/调试方式以 SE 文档为准（`OsirisExtenderSettings.json` 的 LuaDebuggerPort=9998）
- 控制台里可用 `Osi.AddSkill("NRT_katon_goukakyu", char)` 类调用（具体函数名以 SE 文档核实）

---

## B. BG3 验证（需要 BG3SE，控制台加技能）

### B1. 安装 BG3SE（修改游戏目录，请确认后操作）
1. 复制 `tools\BG3SE-Updater-20260621\DWrite.dll` 到：
   `E:\SteamLibrary\steamapps\common\Baldurs Gate 3\bin\`
2. 启动游戏 → 右下角出现 SE 版本号提示 = 注入成功；按 **`~`**（反引号）打开 **Lua 控制台**

### B2. 安装与启用模组
1. 复制 `mods\NarutoJutsu\BG3\NarutoJutsu_BG3.pak` 到：
   `%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\`
2. 主菜单 → **Mod Manager** → 启用 NarutoJutsu（或先开游戏让它自动识别）

### B3. 控制台验证（读档后按 `~`）
```lua
-- 1) 确认模组统计已加载（关键第一步）
Ext.Stats.Get("NRT_katon_goukakyu")   -- 非 nil = 自定义文件名生效 ✅
-- 2) 给当前玩家角色加技能
local c = Osi.GetHostCharacter()
Osi.AddSpell("NRT_katon_goukakyu", c)
Osi.AddSpell("NRT_suiton_suiryudan", c)
Osi.AddSpell("NRT_raiton_raikiri", c)
Osi.AddSpell("NRT_fuuton_daihakki", c)
Osi.AddSpell("NRT_doton_doryusou", c)
```
3. 打开法术书/快捷栏：5 个技能出现
   - ✅ 显示英文名/描述 → 自造 handle 方案生效
   - ❌ 名字显示为 `h734ab279...;1` 原始串 → loca 查找方式不符，需换方案
4. 找敌人施放：验证伤害（3d6 火/寒、2d8 力、3d8 钝击）、火球点燃地面、风遁击退、雷切突进、土遁击倒
5. 注意：雷切/豪火球有等级需求（Level 2/3）与 ActionPoint 消耗，低等级角色需控制台调级（`Osi.SetLevel` 类命令或直接看是否可用）

---

## C. 验证清单（勾选上报）

| # | 检查项 | 预期 | 失败含义 |
|---|---|---|---|
| 1 | 模组在游戏里被识别并启用 | 模组列表可见 | pak/meta.lsx 问题 |
| 2 | `Ext.Stats.Get("NRT_katon_goukakyu")` 非 nil / GM 技能列表可见 | 可查询 | **自定义文件名未合并** → 方案 D |
| 3 | 技能名/描述显示 | 英文文本 | 本地化键方案问题 |
| 4 | 技能可施放 | 有施法动作/特效 | 字段集缺字段或数值非法 |
| 5 | 伤害与状态生效 | 按规格 | 效果链语法问题 |
| 6 | AP/冷却符合配置 | AP 2-3、CD 3-4 | 数值字段问题 |

## D. 若"自定义文件名"不被加载（回填方案）

Larian 统计系统按**条目名**合并，但部分版本要求文件在官方命名的文件中。修复方式（生成器一键切换）：
1. 生成器增加 `merge_mode`：把条目输出到 `Skill_Projectile.txt` / `Skill_Rush.txt` / `Skill_Zone.txt` / `Skill_Shout.txt`（DOS2）与 `Spell_Projectile.txt` / `Spell_Rush.txt` / `Spell_Zone.txt`（BG3）——按术的形态分发
2. 若官方文件会被整个覆盖（非合并语义），需从解包数据复制完整 vanilla 文件再追加（我们已有全部源数据）
3. 重新打包、重新验证

## E. 注意事项
- **BG3 模组管理器**：BG3 内置 Mod Manager 启用后，读档/新档需在模组列表确认 NarutoJutsu 处于启用
- **存档风险**：原型模组请用**新档或测试档**验证，不要用主力档
- **SE 版本**：BG3SE v32 对应游戏当前补丁；若游戏更新后 SE 失效，重新下载对应版本
- 报告格式建议：勾选 C 表 + 截图（技能列表、施放瞬间、伤害飘字）

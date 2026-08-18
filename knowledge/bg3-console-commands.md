# BG3SE 控制台速查（函数签名已从游戏本体 Osiris 反编译核实 2026-08-18）

## 打开方式

- 安装：`DWrite.dll` → `E:\...\Baldurs Gate 3\bin\`（游戏首次启动自动更新 SE；SE 与游戏版本强绑定）
- 游戏内按 **`~`**（反引号）打开 Lua 控制台；右下角 SE 版本号 = 注入成功
- 控制台是 Lua REPL：`local x = ...` 多行用回车，单行直接执行

## 核心指令（均已核实存在）

```lua
-- 角色引用
local c = Osi.GetHostCharacter()        -- 当前玩家控制角色
-- 或 _C()（BG3SE 便捷函数，当前选中角色）

-- 等级（升级会走职业成长表解锁技能）
Osi.SetLevel(c, 12)                     -- 直接设 12 级（最高）；SetLevel 在 osi 中 35 处使用
Osi.Proc_LevelUp(c)                     -- 升 1 级（定义链：Proc_LevelUp → Proc_LevelUpBy → SetLevel(level+1)）
Osi.GetLevel(c)                         -- 查询当前等级

-- 给技能（注意参数顺序：角色在前、技能名在后！）
Osi.AddSpell(c, "Projectile_Kunai")     -- 手里剑；AddSpell(char, spell) 在 osi 中 102 处使用

-- 常用查询
Osi.GetPosition(c)                      -- 位置 x,y,z
Osi.GetApprovalRating(c, target)        -- 好感
Osi.HasActiveStatus(c, "BURNING")       -- 状态
```

## 事件/钩子（模组开发用）

```lua
Ext.Osiris.RegisterListener("DialogStarted", 2, "after", function(dialog, instance) end)
Ext.Events.Tick:Subscribe(function(e) print(e.Time.Time) end)   -- ~30Hz
```

## 持久化/文件

```lua
Ext.IO.SaveFile("Mods/MyMod/memory.json", jsonString)
Ext.IO.LoadFile("Mods/MyMod/memory.json")
Ext.Vars.RegisterUserVariable("MyVar", {Server=true, Persistent=true})
```

## 局限（重要）

- **无出站 HTTP**（LLM 桥接必须外部进程/原生 DLL）
- **无 `Osi.Say`**（说话走对话系统/StartVoiceBark；头顶浮字无现成 API）
- `Osi.StartDialog_Internal` 用法未文档化（待实测）
- `Ext.ModSaveFile` 不存在（那是 DOS2SE 概念，BG3 用 Ext.IO）

## 参考

- 完整 Osiris 符号：游戏本体反编译 `extracted/BG3/Mods/*/Story/osid/`（SetLevel/AddSpell/ChangeApprovalRating/QRY_StartDialog 族等均可查）
- SE 文档：github.com/Norbyte/bg3se（Docs/API.md）

# BG3 存档格式 v4.1.1（patch 8.x）实测

> 2026-08-18 实测：游戏版本 4.1.1.7398727 的 .lsv 存档结构，与老教程（Progress/ 目录）完全不同。

## 包内结构（Divine list-package 实测，仅 7 个条目）

```
AutoSave_0.WebP           缩略图
Globals.lsf               全部全局状态（~2.2MB，含角色世界状态）
LevelCache/SYS_CC_I.lsf   建卡地图实体缓存
LevelCache/TUT_Avernus_C.lsf  当前地图实体缓存
meta.lsf                  LSOF 资源
SaveInfo.json             加载页元数据（等级/经验/职业只在这！改它无实际效果）
StorySave.bin             Osiris 状态（33MB，`.Osiris save fil` 头）
```

## 关键结论：XP/等级不在任何 XML 里

- **无 Progress/ 目录**（老版本 `Progress/Public/Game/Progress/Character_<uuid>.lsf` 已消失）
- Globals.lsx（convert-resource 可读）搜遍无 `XP`/`Progression` 字段；角色节点只有世界状态（位置/StatusManager/PlayerData/FlagMap）
- XP 由 **Osiris 系统**管理：游戏发经验走 `AddExplorationExperience(char, amount)`（Gustav 反编译 osid 有实例）
- `SetLevel(char, level)` 是原生引擎函数；`Proc_LevelUp(c)` = `Proc_LevelUpBy(c,1)` = `GetLevel+IntegerSum → SetLevel(level+1)`（__PROC.txt 实测）

→ **想改经验/等级：直接改存档不可行（要二进制手术 Osiris 状态）；走 SE 控制台或 Osiris 作弊 mod**

## Globals.lsx region 速查（对照用）

| region | 内容 |
|---|---|
| ModuleSettings | 启用的 mod 列表（Folder/Name） |
| Characters | 全部角色实例（Level 属性=地图名！不是角色等级） |
| Stats | 战利品表等 stat 条目（也无 XP） |
| NewAge | 引擎序列化状态 ScratchBuffer（base64，`LSMF` 头，非 LSF，勿编辑） |
| Story / StoryElements / AnubisFramework / EventStorages | Osiris/事件状态 |

## 相关链接

- [[larian-mod-directories]]（装/找存档）
- [[stat-file-conventions]]（技能配表）
- SE 控制台方案：`knowledge/bg3-console-commands.md`（SetLevel/Proc_LevelUp/AddSpell 均已核实）

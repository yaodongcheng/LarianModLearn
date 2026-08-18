# BG3 模组 Osiris story 编译管线（.txt goal → story.div.osi，2026-08-18 实测）

> 从"给 NarutoJutsu 加经验规则"实站踩坑总结。游戏本体把 goal 源码一起发布了，可当格式教科书。

## 文件位置约定（ModResources.cs 源码 + 游戏 Data 实测）

```
Mods/<mod>/Story/
├── RawFiles/Goals/*.txt        ← goal 源码（只收 .txt，扩展名必须是 .txt）
├── RawFiles/story_header.div   ← 头文件（必需！缺了报 X00 无法编译）
├── RawFiles/TypeCoercionWhitelist.txt   ← 可选
├── story_orphanqueries_ignore_local.txt ← 可选
└── story.div.osi               ← 编译产物（运行时引擎读这个）
```

- 游戏本体源码位置：`E:\...\Baldurs Gate 3\Data\Mods\Gustav\Story\RawFiles\Goals\`（GustavDev/Shared/SharedDev/Honour 同构）
- 头文件抄源：`Data\Mods\Shared\Story\RawFiles\story_header.div`（1331 行，全部函数声明）

## goal 源文件格式（照抄游戏本体）

```
Version 1
SubGoalCombiner SGC_AND
INITSECTION
//REGION ...
DB_xxx(...);                    ← 初始事实
//END_REGION
KBSECTION
//REGION ...
IF
条件
AND
条件
THEN
动作;
//END_REGION
```

- INITSECTION = 初始事实段；KBSECTION = IF/THEN 规则段
- DB 事实**不用声明**（编译器从用法推断类型）；函数必须写在 story_header.div

## story_header.div 格式（极简版）

```
alias_type {CHARACTER, 6, 5}
call AddExplorationExperience((CHARACTER)_Character, (INTEGER)_Gain) (1,0,27,1)
```

- 预定义类型免声明：INTEGER(1)/INTEGER64(2)/REAL(3)/STRING(4)/GUIDSTRING(5)
- 函数声明格式从游戏头文件原样抄（含末尾元组 `(1,0,27,1)`，有引擎语义勿改）
- 游戏头文件首行注明 "automatically generated. Do not modify!"——官方 Toolkit 自动生成；我们手写极简版只声明用到的函数即可

## 编译命令

```
StoryCompiler.exe --game bg3 --game-data-path "E:\...\Baldurs Gate 3\Data" --mod <Mod名> --output <out.div.osi> --no-packages
```

- `--game bg3` 支持（usage 帮助文本过时只写了 dos2|dos2de，实际枚举是 dos2;dos2de;bg3）
- 源码/头文件要放在 **game-data-path 之下** `Mods/<mod>/Story/RawFiles/`（Toolkit 惯例：把工程源码写进游戏 `Data\Mods\<mod>\`）；`--game-data-path` 指游戏 Data 根
- `--mod` 可重复；**多 mod 合并输出成一个 story**，header 取参数列表里最后一个有 header 的 mod（"last mod wins"，不会合并多个 header）
- 只编自己的 mod：自己的极简 header 就够（编译器不要求声明全部游戏函数）
- 其他：`--check-only` 只查错不输出；`--no-warn <code>` 压警告；`--debug-log <path>` 输出编译日志

## 常见错误

| 报错 | 原因 |
|---|---|
| `X00 Unable to locate story header file (story_header.div)` | RawFiles 缺头文件（最常见） |
| `X00 Could not parse goal file <名>` | 多为上头文件缺失的级联错误，先修 header 再看 |

## 运行时行为（已核实）

- 引擎按 mod 合并所有已加载 story；**DB 事实存在故事状态（StorySave.bin），存档后持久**——一次性 guard 用 `NOT DB_<自造>(char)` + THEN 写事实
- 玩家检测：`DB_Players(char)`（游戏本体 goal 里大量使用）
- 加经验：`call AddExplorationExperience(char, amount)`（游戏发探索经验用；注释警告 "Do NOT use this call without express permission"——我们就是要用）
- 卸载 mod：story 重编译丢的是本 mod 的事实/规则；经验在引擎侧（NewAge 状态），卸载不影响已获得的经验

## 相关

- [[bg3-mod-architecture]]（技能组/成长表，与 story 互补）
- [[osiris-and-tools]]（反编译 StoryDecompiler / 解包打包）
- 游戏本体 goal 源码 = 最佳语法参考：`Data\Mods\Gustav\Story\RawFiles\Goals\`（例：`DebugItem_Dev.txt` 有完整的 DB_Players+AddExplorationExperience 模式）

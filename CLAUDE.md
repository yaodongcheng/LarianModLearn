# CLAUDE.md — LarianModLearn 项目基础认知

> 项目：为《博德之门 3》(BG3) 与《神界：原罪 2 决定版》(DOS2 DE) 制作大模型驱动 NPC AI 模组 + 忍术配表模组（原型已可加载）。
> 本文件是项目基础认知第一步。详细分析见 `docs/`。

## 1. 环境

| 项 | 路径 |
|---|---|
| 项目根 | `f:\LarianModLearn`（git 仓库，main 分支） |
| BG3 安装 | `E:\SteamLibrary\steamapps\common\Baldurs Gate 3`（主程序 `bin\bg3.exe`） |
| DOS2 DE 安装 | `G:\SteamLibrary\steamapps\common\Divinity Original Sin 2`（主程序 `DefEd\bin\EoCApp.exe`） |
| 官方 Toolkit | BG3 Toolkit / The Divinity Engine 2（均在 `G:\SteamLibrary\steamapps\common\`，用户已装，工程在游戏 Data 目录） |
| LSLib | `tools\ExportTool-v1.20.4\Packed\`（Divine.exe / StoryDecompiler / ConverterApp[纯GUI] / StatParser） |
| SE（已安装 2026-08-18，DWrite.dll 已在游戏 bin\） | `tools\BG3SE-Updater-20260621\DWrite.dll`（升级器本体） |
| 解包数据（不入库） | `extracted\BG3\`（87k 文件）、`extracted\DOS2\`（7k 文件），含反编译 Osiris goals（osid\） |
| OpenGameAgent | `vendor\OpenGameAgent\`（0.3.0-alpha.2，C#，独立 .NET 服务模式接入） |
| 忍术模组 | `mods\NarutoJutsu\`（生成器 `tools\jutsu_gen\jutsu_gen.py`，规格表 `spec\jutsus.json`） |

## 2. 模组目录与形态（实测结论，勿混用）

- **DOS2 模组加载**：游戏扫描 `DefEd\Data\Mods\`（本体战役 Shared/DivinityOrigins 也是文件夹形态于此）；玩家标准位 `%USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\`
- **BG3 模组加载**：`%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\`（官方模组管理器标准）；`E:\...\Baldurs Gate 3\Data\Mods\` 是本体战役文件夹；Toolkit 工程在 Data\Projects/Public/Editor
- **形态**：工程形态 = 文件夹四目录（Projects/Mods/Public/Editor，Toolkit 生成，如 myFirstMod_<uuid>）；**发布形态 = .pak**
- **pak 内结构**（对照本体实测）：`Mods/<Folder>/meta.lsx` + `Public/<Folder>/...` + `Localization/English/...`
- **meta.lsx 格式**：`region id="Config"` → root → Dependencies + ModuleInfo（**不是** Module 区域）。BG3：version 4.8 + `Version64`(int64) + FileSize/PublishHandle；DOS2：version 3.6 + `Version`(int32) + Type="Add-on" + Dependencies 依赖主战役 DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4
- 玩家启用：DOS2 主菜单 Mods 勾选；BG3 模组管理器启用

## 3. 两游戏机制速览（详见 docs/game-analysis-*.md）

- **统一主键**：NPC 实例 GUID（UUID 字符串）贯穿 stats/对话/Osiris 规则/anubis（BG3）/charScript（DOS2）
- **Osiris**：事件驱动规则引擎（`IF 事件 AND 条件 THEN 动作`）。BG3 反编译 1452 goals（Gustav 382 + GustavDev 935 + SharedDev 135），DOS2 68 goals。事件/动作 TOP-100 表见分析文档
- **对话**：.lsj JSON（节点树 + TaggedTexts + speakerlist），BG3 另配 Timeline 播放器；对话启动 DOS2 走 `Proc_StartDialog`（完整校验链），BG3 走 `QRY_StartDialog` 族
- **SE（Script Extender）**：两游戏均**无出站 HTTP**（LLM 桥接必须外部进程：BG3 原生 DLL 或 Ext.IO 文件桥；DOS2 v60+ Ext.IO 文件桥）；BG3 有 `Ext.Events.Tick`、`Ext.Osiris.RegisterListener`；DOS2 v60+ 也有 Tick 与 Ext.IO；无 Osi.Say（说话走对话/StartVoiceBark）
- **时间**：BG3 无引擎时钟（Ext.Timer.GameTime + 昼夜 flag 自建）；DOS2 有 `DB_Time` + `NewHour` 事件
- **技能/法术配表**：DOS2 `Skill_<形态>.txt`（SkillData：Ability 学派/Tier/ActionPoints/Cooldown/DamageType/SkillProperties/CastAnimation/Template）；BG3 `Spell_<形态>.txt`（SpellData：Level/SpellSchool/SpellRoll/SpellSuccess/SpellProperties）。状态在 `Status_*.txt`（StatusData）。**模组统计文件需用官方文件名分发（存疑项→2026-08-17 切换中）**

## 4. 工具链命令速查（详见 docs/toolchain-notes.md）

```bash
DIVINE="tools/ExportTool-v1.20.4/Packed/Tools/Divine.exe"
# 解包/列表/转换/打包
"$DIVINE" -g bg3 --action list-package -s <pak>
"$DIVINE" -g bg3 --action extract-package -s <pak> -x "**/Story/**" -d <out>
"$DIVINE" -g bg3 --action convert-resource -s <x.lsf> -d <x.lsx>   # 输出须 .lsx
"$DIVINE" -g bg3 --action convert-loca -s <xml> -d <x.loca>        # BG3 本地化
"$DIVINE" -g dos2de --action create-package -s <dir含Mods/> -d <out.pak>
# Osiris 反编译（输出目录，每 goal 一个 txt；bash 用正斜杠路径）
StoryDecompiler.exe --input <story.div.osi> --output <osid目录>
```

## 5. 关键文档索引

| 文档 | 内容 |
|---|---|
| `plans/plan-llm-npc-ai-mod.md` | 总计划（分析阶段已全部完成，M5 关卡已到） |
| `docs/game-analysis-BG3.md` / `-DOS2.md` | 反编译分析（事件/动作 TOP100、SE API 核实） |
| `docs/integration-points.md` | 六类接入点清单 |
| `docs/opengameagent-study.md` | OpenGameAgent 研读（Server + Remote actions 模式） |
| `docs/capability-matrix-and-limits.md` | 能力矩阵与限制 |
| `docs/integration-design.md` | 桥接架构 + 实施路线 S1-S6 |
| `docs/verification-guide.md` | 实机验证步骤（DOS2 GM 模式 / BG3 SE 控制台） |

## 6. 知识库（knowledge/，实测速查，动手前先看）

| 文件 | 何时查 |
|---|---|
| `knowledge/mod-install-and-loading.md` | 装/找 mod、目录放错排查（BG3=LocalAppData；DOS2=Data\Mods+Documents） |
| `knowledge/pak-and-meta-lsx.md` | 打包新 mod：pak 结构 + meta.lsx（Config/ModuleInfo，两游戏字段不同） |
| `knowledge/stat-file-conventions.md` | 配新技能/法术：**必须官方文件名分发** + 条目字段模板 |
| `knowledge/localization.md` | 加文本：BG3 自造 handle + loca 转换；DOS2 字符串键 XML |
| `knowledge/osiris-and-tools.md` | 解包/反编译/转换/打包命令与坑 |
| `knowledge/bg3-save-format-v4.md` | 改存档前必看：v4.1.1 存档无 XP 字段（Osiris 管 XP），改档不可行→SE 控制台 |
| `knowledge/bg3-console-commands.md` | 游戏内调试：`~` 控制台 SetLevel/AddSpell（参数顺序！） |
| `knowledge/bg3-mod-architecture.md` | BG3 模组架构（查克拉/职业/成长表，参考 shinobi class mod） |
| `knowledge/dos2-gm-mode-mod-loading.md` | DOS2 GM 模式加载 mod：三层链路（pak/EditorProfile/战役 Dependencies）+ TargetModes 需含 GM + 竖线本地化 |

## 7. 待办与坑

- 忍术原型：DOS2 GM 模式**技能已验证可加载**（2026-08-18：官方文件名 + TargetModes GM + 战役 Dependencies + 竖线本地化，四步后火焰学派 Adept 可见）；BG3 学习途径未配置（SpellSet 路线待验证）；BG3 验证需 SE（**已装 2026-08-18**，首次启动自动更新）
- DOS2 用户环境：GM 模式配置走 EditorProfile modsettings + **战役文件 Dependencies**（已确认，见 knowledge/dos2-gm-mode-mod-loading.md）
- SE 与游戏版本强绑定；游戏更新会破坏
- `ConverterApp.exe` 无 CLI；`Divine convert-resource` 输出扩展名必须 .lsx；StoryDecompiler 输出是目录
- git：大目录不入库（extracted/、vendor/、tools 二进制），`tools/jutsu_gen/` 与 `knowledge/` 保留

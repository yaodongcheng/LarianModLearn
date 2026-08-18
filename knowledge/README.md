# Knowledge 知识库

> 本项目**实测验证**的技术知识速查（2026-08-18 建）。与 `docs/`（分析报告，讲"为什么"）不同，这里讲"怎么操作"——每个结论都经过实际验证（解包/打包/游戏内实测），标注证据来源。
> 使用方式：按主题查对应文件；CLAUDE.md 第 7 节是索引。

## 文件索引

| 文件 | 内容 | 何时查 |
|---|---|---|
| [mod-install-and-loading.md](mod-install-and-loading.md) | 两游戏模组目录与加载机制（BG3=LocalAppData / DOS2=Data\Mods+Documents；官方管理器位置；游戏目录 vs 玩家目录） | 装/找 mod、放错位置排查时 |
| [pak-and-meta-lsx.md](pak-and-meta-lsx.md) | pak 内结构 + meta.lsx 两游戏格式（Config/ModuleInfo、Version64 vs Version、依赖写法） | 打包新 mod、meta 报错时 |
| [stat-file-conventions.md](stat-file-conventions.md) | 统计文件命名约定（必须官方文件名分发！）+ 技能/法术条目字段集（各形态模板） | 配新技能/法术时 |
| [localization.md](localization.md) | 本地化三方案：BG3 自造 handle + .loca 转换；DOS2 字符串键 XML（无 version 属性）；键与引用一致性 | 加文本/名字不显示时 |
| [osiris-and-tools.md](osiris-and-tools.md) | LSLib 命令速查 + 坑（StoryDecompiler 输出目录、ConverterApp 无 CLI、convert-resource 须 .lsx、bash 正斜杠） | 解包/反编译/转换/打包时 |
| [bg3-console-commands.md](bg3-console-commands.md) | BG3SE 控制台速查（`~` 打开；SetLevel/AddSpell 签名——参数顺序！） | 游戏内调试/给技能/升级时 |
| [bg3-mod-architecture.md](bg3-mod-architecture.md) | BG3 模组完整架构（参考 shinobi class mod）：ActionResourceDefinitions / ClassDescriptions / Progressions / 技能组资源 | 做 BG3 职业/学习途径/查克拉系统时 |

## 待验证条目（写入对应文件时标注 ⚠️）

- DOS2 GM 模式加载玩家 mod 的确认（EditorProfile modsettings 机制——半确认）
- DOS2 SE（Ext.IO 文件桥）实机行为
- BG3 `Osi.StartDialog_Internal` 前置条件

# 工具链笔记（Phase 0 交付物）

> 2026-08-17 建立。所有分析结论基于以下工具与版本。

## 游戏版本

| 游戏 | 安装路径 | buildid | 备注 |
|---|---|---|---|
| Baldur's Gate 3 | `E:\SteamLibrary\steamapps\common\Baldurs Gate 3` | 24532579 | 主程序 `bin\bg3.exe`，`bin\Osiris.dll` 随游戏分发 |
| Divinity OS 2 DE | `G:\SteamLibrary\steamapps\common\Divinity Original Sin 2` | 9530355 | 主程序 `DefEd\bin\EoCApp.exe`；`Classic\` 为原版可忽略 |
| BG3 Toolkit（官方） | `G:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit` | appid 2934770 | 官方编辑器，交叉验证用 |
| The Divinity Engine 2（官方） | `G:\SteamLibrary\steamapps\common\The Divinity Engine 2` | appid 664400 | 官方编辑器，交叉验证用 |

## 工具清单（`tools\`）

| 工具 | 来源 | 版本 | 用途 |
|---|---|---|---|
| `ExportTool-v1.20.4\Packed\Tools\Divine.exe` | Norbyte/lslib GitHub Releases | v1.20.4 (2026-01-24) | pak 解包、.lsf→.lsx 转换 |
| `ExportTool-v1.20.4\Packed\Tools\StoryDecompiler.exe` | 同上 | v1.20.4 | Osiris story.div.osi 反编译（按 goal 输出 .txt） |
| `ExportTool-v1.20.4\Packed\Tools\StoryCompiler.exe` | 同上 | v1.20.4 | 未来写 Osiris 规则用（暂未用） |
| `ExportTool-v1.20.4\Packed\ConverterApp.exe` | 同上 | v1.20.4 | **纯 GUI，无 CLI**（验证过，勿再尝试命令行调用） |
| `BG3SE-Updater-20260621\DWrite.dll` | Norbyte/bg3se Releases v32 (2026-06-21) | 对应最新补丁 | BG3SE 注入 DLL（放 BG3 `bin\` 下；未安装，待阶段 2 运行时验证） |
| `DOS2SE-Updater-v5\dxgi.dll` | Norbyte/ositools Releases updater_v5 (2022-09-19) | 自动拉最新 | DOS2SE 注入 DLL（放 DOS2 `DefEd\bin\` 下；未安装） |

> 注：SE 版本与游戏版本强绑定。BG3SE v32 发布于 2026-06-21，游戏 buildid 24532579（2025-12 有更新日志），安装 SE 前需核对兼容性。

## 常用命令

```bash
# 列出 pak 内容
Divine.exe -g bg3 --action list-package -s <pak>

# 定向提取（glob 支持 **）
Divine.exe -g bg3 --action extract-package -s <pak> -x "**/Story/**" -d <outdir>

# .lsf → .lsx（输出扩展名必须是 .lsx）
Divine.exe -g bg3 --action convert-resource -s <file.lsf> -d <out.lsx>

# Osiris 反编译（输出为目录，每个 goal 一个 .txt）
StoryDecompiler.exe --input <story.div.osi> --output <osid目录>
```

## Pak 结构要点（两游戏通用）

- 数据分两类：`Mods\<Mod>\`（故事/对话/Osiris 脚本）与 `Public\<Mod>\`（数值/flag/本地化/素材）
- **两游戏的 stats 都是可读 .txt**（`Public\<Mod>\Stats\Generated\`，BG3 有 Character.txt）
- **对话 .lsj 是 JSON 可读**（BG3: `Mods\Gustav\Story\Dialogs\`；DOS2: `Mods\Shared\Story\Dialogs\`），另有 .lsf 二进制副本（BG3: DialogsBinary/、Timeline/）
- **Osiris 已编译故事**每模组 1 个 `story.div.osi`
- BG3 额外有：`Public\Gustav\Flags\`（游戏 flag 表）、`Public\GustavDev\ApprovalRatings\`（好感评级）、`Public\Gustav\Timeline\`（对话 timeline 引擎数据）、`Scripts\anubis\`（内置 Lua 脚本）

## 反编译统计（2026-08-17）

| 模块 | goals 数 | 路径 |
|---|---|---|
| BG3 Gustav | 382 | `extracted\BG3\Mods\Gustav\Story\osid\` |
| BG3 GustavDev | 935 | `extracted\BG3\Mods\GustavDev\Story\osid\` |
| BG3 SharedDev | 135 | `extracted\BG3\Mods\SharedDev\Story\osid\` |
| DOS2 Shared | 68 | `extracted\DOS2\Mods\Shared\Story\osid\` |

## 坑与经验

1. `ConverterApp.exe` 无 CLI，启动即 GUI（会挂住命令）。
2. `StoryDecompiler.exe` 的 `--output` 是**目录**；bash 循环里路径含 `$var` 时用正斜杠 `f:/...` 避免转义问题。
3. `Divine.exe --action convert-resource` 输出扩展名决定了格式，`.json` 不被识别，用 `.lsx`。
4. 提取的文件 61% 是 .lsf（BG3），但分析所需的主体（对话/数值/flag 名称/Osiris 规则）都可读，无需全量转换。

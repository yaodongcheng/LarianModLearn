# LSLib 工具命令速查与坑（实测 2026-08-18）

工具位置：`tools/ExportTool-v1.20.4/Packed/`（Divine.exe / StoryDecompiler.exe / StoryCompiler.exe / StatParser.exe / ConverterApp.exe[纯GUI]）

## 常用命令（bash 风格；Windows 路径在 bash 里用正斜杠避免转义问题）

```bash
DIVINE="tools/ExportTool-v1.20.4/Packed/Tools/Divine.exe"

# 列出 pak 内容
"$DIVINE" -g bg3 --action list-package -s <pak>

# 定向提取（glob 支持 **）
"$DIVINE" -g bg3 --action extract-package -s <pak> -x "**/Story/**" -d <outdir>

# 提取单个文件
"$DIVINE" -g bg3 --action extract-single-file -s <pak> -f "Mods/Shared/meta.lsx" -d <out.lsx>

# .lsf → .lsx（输出扩展名必须是 .lsx，.json 会报 "Unrecognized file extension"）
"$DIVINE" -g bg3 --action convert-resource -s <x.lsf> -d <x.lsx>

# 本地化
"$DIVINE" -g bg3 --action convert-loca -s <english.xml> -d <english.loca>   # BG3（XML 带 version 属性）
"$DIVINE" -g dos2de --action convert-loca -s <x.loca> -d <x.xml>            # DOS2 反向转换参考

# 打包（-s 指向含 Mods/ 的目录）
"$DIVINE" -g dos2de --action create-package -s <dir> -d <out.pak>
"$DIVINE" -g bg3 --action create-package -s <dir> -d <out.pak>
```

## Osiris 反编译

```bash
StoryDecompiler.exe --input <story.div.osi> --output <osid目录>
```
- `--output` 是**目录**（每 goal 一个 .txt），不是文件
- 两游戏各模组只有一个编译故事：`Mods/<Folder>/Story/story.div.osi`
- bash 循环中 `$var` 拼接 Windows 路径时用正斜杠（`f:/...`）——反斜杠+变量会展开失败（已踩坑）

## 坑清单

| 坑 | 说明 |
|---|---|
| `ConverterApp.exe` 无 CLI | 启动即 GUI（会挂住终端），不要用命令行调用它 |
| `convert-resource` 输出扩展名 | 必须是 .lsx（.json 不被识别） |
| `list-package` 动作名 | 是 `list-package`（`list` 不是合法值） |
| StoryDecompiler 参数 | `--input`/`--output` 都是必填，缺一会报 "not marked as optional" |
| StatParser | 需要 `LSLibDefinitions.xml`（release 完整版在 lslib 发布包内，GitHub master 的是 7 条目的 stub，别用）——实际用游戏/Toolkit 验证更可靠 |
| pak 残留 | 生成器目录重构后旧路径会残留进 pak——打包前清理（我们踩过：旧 Localization 路径进 pak） |

## 版本信息

- LSLib v1.20.4（2026-01-24）
- BG3 buildid 24532579；DOS2 DE buildid 9530355
- 解包统计：BG3 87,480 文件 / DOS2 6,981 文件；Osiris goals：BG3 1,452（Gustav 382 + GustavDev 935 + SharedDev 135）/ DOS2 68

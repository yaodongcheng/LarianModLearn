# 两游戏模组目录与加载机制（实测 2026-08-18）

## BG3（玩家 mod 只有一个合法位置）

| 目录 | 内容 | 说明 |
|---|---|---|
| `%LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\` | **玩家 mod**（官方模组管理器下载 + 手动 .pak） | **唯一标准位置**；游戏启动扫描 + `modsettings.lsx` 决定启用 |
| `E:\...\Baldurs Gate 3\Data\Mods\` | 本体战役文件夹模组（Gustav/Shared/GustavDev/SharedDev/GustavX） | 游戏自带"模组化本体"，**不是玩家 mod 位置**（玩家 .pak 放这里大概率不加载） |
| `E:\...\Baldurs Gate 3\Data\` | 本体 pak（Shared.pak 等） | Steam 管理，勿动 |

- 官方模组管理器（游戏内 Mods 界面）下载的 mod 就存在 LocalAppData\Mods，文件名如 `narutotest_<uuid>.pak`（带 mod.io 后缀风格）
- 存档的 mod 配置在 `%LocalAppData%\...\PlayerProfiles\Public\modsettings.lsx`
- 设计原因：用户可写 + 游戏更新隔离 + 多用户隔离

## DOS2 DE（两个合法位置）

| 目录 | 内容 |
|---|---|
| `G:\...\Divinity Original Sin 2\DefEd\Data\Mods\` | 本体战役文件夹（Shared/DivinityOrigins/DOS2_Arena）+ 用户 mod（myFirstMod 在此被识别）——**游戏扫描此目录** |
| `%USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\` | 玩家标准位置（社区教程惯例） |
| ⚠️ `%LocalAppData%\...\DOS2DE\Mods\` | **不是** DOS2 位置（BG3 才用 LocalAppData）——我犯过的错 |

- 玩家 profile modsettings：`Documents\...\PlayerProfiles\<用户名>\modsettings.lsx`
- **GM 模式（地下城与城主）疑似用 `PlayerProfiles\EditorProfile\modsettings.lsx`**（实测 NarutoJutsu 注册进了 EditorProfile 而非玩家 profile；GM 会话加载哪份配置待完全确认 ⚠️）
- 启用 mod 后**必须完全重启游戏**才加载 mod 数据（写 modsettings 后重启生效）

## 模组形态

- **工程形态**（Toolkit 开发期）：文件夹四目录 `Projects/Mods/Public/Editor`（如 `myFirstMod_<uuid>`，位于游戏 Data 下）
- **发布形态**：`.pak` 单文件
- 详见 [pak-and-meta-lsx.md](pak-and-meta-lsx.md)

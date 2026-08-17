# 计划：基于大模型的 BG3 / DOS2 NPC AI 模组（分析阶段）

> 状态：**规划完成，待执行**
> 日期：2026-08-17
> 原则：本计划**只做分析与接入方案设计，不实现任何具体功能**。阶段 0–2 完成反编译分析后，再进入阶段 3–4 研究 OpenGameAgent 并输出接入方案。

---

## 0. 项目目标（一句话）

为 Steam 已安装的 **博德之门 3**（BG3）与 **神界：原罪 2 决定版**（DOS2 DE）制作"由大模型驱动的 NPC AI"模组：NPC 能**观察**游戏世界、**记住**过往互动、**执行**游戏内动作，并有目标/任务/人物关系等长期状态——通过桥接 **OpenGameAgent**（LLM agent 运行时）实现。

---

## 1. 已完成的环境侦察（2026-08-17）

| 项 | 结果 |
|---|---|
| 工作目录 | `f:\LarianModLearn`（空，无 git） |
| BG3 安装 | `E:\SteamLibrary\steamapps\common\Baldurs Gate 3`，主程序 `bin\bg3.exe`（buildid 24532579），`bin\Osiris.dll` 随游戏分发 |
| DOS2 DE 安装 | `G:\SteamLibrary\steamapps\common\Divinity Original Sin 2`，主程序 `DefEd\bin\EoCApp.exe`（buildid 9530355），另有 `Classic\EoCApp.exe`（原版，可忽略） |
| BG3 Toolkit（官方） | `G:\SteamLibrary\steamapps\common\Baldurs Gate 3 Toolkit`（appid 2934770，已安装） |
| The Divinity Engine 2（官方） | `G:\SteamLibrary\steamapps\common\The Divinity Engine 2`（appid 664400，已安装） |
| OpenGameAgent 初查 | 通用 C# AI 游戏运行时（Apache-2.0，netstandard2.1，v0.3.0-alpha.2）：agent kernel + game runtime 两层；支持 Godot 4.7 .NET / Unity 6 / 独立 .NET 服务；模型无关（Anthropic/OpenAI/Gemini/Mistral/本地端点）；有游戏时间记忆、工具校验、durable action receipts、多 actor 并发模型。**不绑定引擎**，需自建游戏侧桥接 |

---

## 2. 总体路线（5 个阶段）

```
阶段 0  工具链准备（LSLib / Script Extender / 解包流程）
   ↓
阶段 1  反编译与静态分析（游戏数据结构 / Osiris / 事件 / 动作 API）
   ↓
阶段 2  确定三个接入位置：NPC 系统 / 事件系统 / 动作执行
   ↓
阶段 3  下载并完整研读 OpenGameAgent（README、文档、源码、示例）
   ↓
阶段 4  能力评估 + 接入方案设计（观察/记忆/执行/多角色/限制）
   ↓
（关卡）交付 3 份文档 → 用户评审 → 通过后才进入功能实现
```

---

## 3. 阶段 0：工具链准备

目标：确认解包/注入/调试工具可用，建立"游戏数据 → 文本"的分析通道。

- [ ] 下载 **LSLib**（Norbyte，`Norbyte/lslib`，含 Divine.exe / ConverterApp）：解包 `.pak`、转换 `.lsf/.lsx/.loca` 为可读文本
- [ ] 下载 **BG3 Script Extender**（`Norbyte/bg3se`，配套 DLL）与 **DOS2 Script Extender**（`Norbyte/DivinityEngine2` 仓库或发布页）
- [ ] **官方模组工具**（已安装，作为权威参考与交叉验证）：
  - `Baldurs Gate 3 Toolkit\bin\...`——BG3 编辑器，含数据导出、对话/脚本编辑能力
  - `The Divinity Engine 2\bin\...`——DOS2 编辑器，同样含导出与编辑能力
  - 两者的自带 `Data/` 目录本身就是（接近）未打包的游戏数据，可直接对照 LSLib 解包结果
- [ ] 确认 BG3 `--export` / 开发者导出流程（解包 Public 目录）
- [ ] 确认 `.pak` 解包产物目录（BG3: `Data/Public/...`；DOS2: `Data/Public/...` 与 `Public/...`）
- [ ] 记录两个游戏的**当前版本号**（buildid 已记录于上表；分析文档标注版本，防日后更新失效）
- [ ] 本地准备：git、.NET 8 SDK（OpenGameAgent 构建要求）、文本搜索工具（ripgrep 已具备）

**交付物**：`docs/toolchain-notes.md`（工具版本、解包命令、目录结构速查）。

---

## 4. 阶段 1：反编译与静态分析

### 4.1 游戏数据反编译（两游戏并行做，结果分节记录）

BG3 解包位置：`E:\SteamLibrary\steamapps\common\Baldurs Gate 3\Data\`（含 `Shared.pak`、`Gustav.pak`、`Patch*.pak` 等）
DOS2 解包位置：`G:\SteamLibrary\steamapps\common\Divinity Original Sin 2\Data\` 与 `DefEd\Data\`

- [ ] 解包两个游戏的 `Shared.pak` + 主内容 pak，得到 `Public/` 结构
- [ ] 重点目录：`Stats`（角色/道具数值，`.lsf`）、`Scripts`（Osiris `.osi` 反编译）、`Dialog`（对话 `.lsf`）、`Story`（任务/flag）、`Levels`（关卡数据）、`Localization`（`.loca` 文本）
- [ ] 用 LSLib 将 `.lsf/.lsx` 转 JSON/XML 可读格式
- [ ] 用官方 Toolkit（BG3 Toolkit / Divinity Engine 2）打开对应工程/数据，交叉验证解包结果，并确认官方编辑器中 NPC、对话、事件的编辑界面结构（对接入点设计有指导意义）

### 4.2 Osiris 脚本系统分析（事件系统的核心）

- [ ] 反编译并通读两游戏的 `.osi` 脚本，建立**事件目录**：
  - 对话事件（`DialogueStarted` 等）
  - 角色/生命周期事件（进入区域、死亡、加入队伍）
  - 状态变化事件（flag 设置、任务推进、时间变化）
  - 战斗事件（进入/退出战斗、回合）
- [ ] 记录事件 → 数据库（`DB_*`）→ 查询（`Query*`）的调用链，确认哪些事件能作为 LLM 的"感知触发器"

### 4.3 对话系统分析（NPC 交互的落点）

- [ ] 分析 `.lsf` 对话结构：节点、条件、语音、分支——确认对话树可否程序化注入/替换
- [ ] 确认 NPC 说话的可选通道：对话 UI、浮动文本（floating text）、日志/字幕
- [ ] 确认 BG3 的 **Approval（好感）** 与 DOS2 的 **Reputation（声望）** 数据结构与修改 API

### 4.4 NPC 数据与 AI 行为

- [ ] 角色 `.lsf` 结构：属性、阵营、AI 行为字段（aggressive/flee 等）
- [ ] 确认 NPC 是否有"日程/行为脚本"字段（便于 LLM 接管/补充）

### 4.5 Script Extender 能力清单（动作执行的落点）

- [ ] 列出 BG3SE / DOS2SE 的 Lua API 目录：`Osi`（调 Osiris 函数）、`Events`（钩子）、`Ext.*`（本地能力：网络 HTTP、文件、持久变量、UI、实体遍历）
- [ ] 验证关键能力存在性（**这是后续桥接的地基**，示例写法为待验证）：
  - 事件钩子：对话开始/结束、角色移动、回合切换
  - 动作：移动/传送、说话/浮动文本、给物品、设 flag、改好感
  - 游戏时间读取（时分/天数）
  - 持久化（存档内变量 vs 磁盘 JSON）
  - 遍历场景角色（感知的输入来源）
  - `Ext.Net` 发起 HTTP 请求（与外部 agent 服务通信的通道）

**交付物**：`docs/game-decompiled-analysis.md`（BG3 与 DOS2 各一节，含事件目录、API 清单、代码位置引用）。

---

## 5. 阶段 2：确定三个接入位置

在阶段 1 数据基础上，产出**接入点清单**（每项标注：游戏、位置、可读/可写、示例调用、验证方式）：

1. **NPC 系统接入位置**
   - 对话触发点（开始/结束/节点选择）——LLM 每次交互的入口
   - 角色数据读取（感知输入）与好感/声望修改（状态写回）
   - NPC 主动行动点（空闲轮询 / 定时器 / 区域触发器）
2. **事件系统接入位置**
   - 引擎事件 → SE 钩子 → 转成 LLM 观察到的"情境快照"
   - 事件过滤与节流（防止高频事件淹没 LLM 调用）
3. **动作执行接入位置**
   - LLM 决策 → 工具调用 → SE/Osi 执行 → 结果回执（对应 OpenGameAgent 的 durable action receipts）
   - 不可执行动作的降级策略（引擎为权威，见限制分析）

**交付物**：`docs/integration-points.md`（接入点清单 + 时序图描述）。

---

## 6. 阶段 3：OpenGameAgent 完整研读

- [ ] `git clone https://github.com/EricSun0218/OpenGameAgent` 到 `f:\LarianModLearn\vendor\OpenGameAgent`
- [ ] 通读 README（架构、feature table、放置方式三种：引擎内/游戏服务器/独立服务）
- [ ] 通读 `docs/`（getting-started、architecture、engine-integration、deployment-and-security、media、image-input）
- [ ] 读源码核心：agent kernel（model/tool 循环）、game runtime（sessions/actors、timeline/ticks、memory、action dispatcher、mailboxes、goals/workflows）
- [ ] 跑通官方示例/单元测试（.NET 8，确认构建方式）
- [ ] 重点回答：**"独立 .NET 服务 + JSON/SSE"部署模式**的接口形状（Larian 引擎没有 Godot/Unity 适配器，必须走这条路径）

**交付物**：`docs/opengameagent-study.md`（模块图、关键类、接口、示例代码摘录、版本与许可证备注）。

---

## 7. 阶段 4：能力评估与接入方案

### 7.1 能力映射：OpenGameAgent 概念 → 游戏能力

| OpenGameAgent 概念 | BG3/DOS2 中的实现途径 | 可行度 |
|---|---|---|
| Observation（有界 JSON + 可选图像） | SE 场景快照：附近角色、玩家、flag、时间、好感；图像输入需游戏截图能力，待验证 | 待定 |
| Memory（游戏时间过滤、过期、embedding 检索） | 持久化到磁盘 JSON/SQLite + SE 读取 | 高 |
| Tools（游戏校验后执行） | Osi 调用封装（移动/说话/给物/设flag） | 高 |
| Actions / durable receipts（幂等重试） | 执行结果回执，防 LLM 重复写 | 中 |
| Game-time timeline/ticks | 对接游戏内时钟（BG3 时分、DOS2 时辰） | 中 |
| Actors / sessions / mailboxes（多角色并发） | 每 NPC 一个 actor，SE 事件分发 | 高 |
| Goals / task plans / workflows | NPC 日程、任务目标、脚本化兜底 | 中 |
| 模型无关（Anthropic/OpenAI/本地端点） | 本地 Ollama 低延迟优先，云端备用 | 高 |

### 7.2 桥接架构（初稿）

```
游戏进程（bg3.exe / EoCApp.exe）
  └─ Script Extender (Lua)        ← 事件钩子 + 动作执行 + 场景快照
        │  HTTP / WebSocket（Ext.Net 或自建）
        ▼
OpenGameAgent（独立 .NET 服务，netstandard2.1 runtime）
  ├─ agent kernel（model/tool 循环）
  ├─ game runtime（actor、记忆、目标、收据）
  └─ LLM Provider（Anthropic / OpenAI / Ollama…）
```

- 单机模式：游戏与 agent 服务同机运行；SE 启动时拉起服务或由用户手动启动
- 此桥接层的接口契约（JSON schema）在阶段 4 中定义，**不写实现代码**

### 7.3 限制分析（需在方案文档中明确回答）

- 对话是**树状 UI**，LLM 自由文本如何进入对话框 / 浮动文本的可行性
- **延迟**：LLM 调用阻塞 NPC 响应的时间预算；流式输出、本地模型的取舍
- **战斗**：LLM 不应接管战斗 AI（引擎权威），降级策略
- **多角色**：同屏多个 LLM NPC 的并发与上下文成本；OpenGameAgent 的 actor 串行化是否够用
- **游戏时间**：回合制/暂停机制与 agent tick 的对齐
- **持久化**：存档兼容性（SE 变量 vs 磁盘文件）、MOD 依赖（SE 版本与游戏版本强绑定，Patch 更新会破坏）
- **多人与网络**：SE 钩子本地性，多人场景的行为分歧
- **成本/硬件**：本地模型（Ollama）显存需求 vs 云端 API 费用

**交付物**：`docs/capability-matrix-and-limits.md` + `docs/integration-design.md`。

---

## 8. 里程碑与验收标准

| # | 里程碑 | 验收标准 |
|---|---|---|
| M1 | 工具链就绪 | 两个游戏的 `.pak` 成功解包，SE 注入无报错，两个官方 Toolkit 确认可用 |
| M2 | 反编译分析完成 | 事件目录、NPC 数据结构、动作 API 清单成文，每个结论可追溯到具体文件/行 |
| M3 | 接入点确定 | `integration-points.md` 列出 ≥3 类接入位置并标注读写方向 |
| M4 | OpenGameAgent 研读完成 | 源码通读笔记 + 官方示例本地跑通 |
| M5 | 方案评审 | 能力矩阵 + 接入设计 + 限制清单 3 份文档齐备，用户评审通过 |

**关卡：M5 通过后才进入"功能实现"阶段（另立计划），本计划不做任何功能。**

---

## 9. 风险与开放问题

1. **SE 与游戏版本绑定**：两游戏近期均更新过（BG3 buildid 24532579，含 2025-12 日志），需确认 SE 版本兼容性（可能需匹配的 SE 版本或等待更新）
2. **OpenGameAgent 为 0.3.0-alpha**：API 可能变动，桥接层应把"游戏侧契约"与"agent 侧 API"解耦
3. **对话注入的可行性**未验证：若树状对话无法优雅承载 LLM 自由文本，需备选通道（浮动文本/字幕）
4. **图像观察**依赖游戏截图能力，BG3SE 是否提供需在阶段 1 验证；不可行则纯文本观察
5. ~~DOS2 先行~~ → 已确认（2026-08-17 用户决定）：**两游戏并行分析**，并纳入官方模组工具（BG3 Toolkit / Divinity Engine 2）作为分析参考

---

## 10. 目录规划

```
f:\LarianModLearn\
├── plans\                      ← 本计划
├── vendor\OpenGameAgent\       ← 阶段 3 克隆
├── tools\                      ← LSLib / SE 下载解压
├── extracted\BG3\ ...          ← 解包产物（大文件不入库）
│   extracted\DOS2\ ...
└── docs\
    ├── toolchain-notes.md
    ├── game-decompiled-analysis.md
    ├── integration-points.md
    ├── opengameagent-study.md
    ├── capability-matrix-and-limits.md
    └── integration-design.md
```

# Spike：技能名喊话（自定义语音 SFX）

> 状态：**独立探索任务**（不阻塞 22 术迁移）| 创建：2026-08-18 | 关联：`plans/plan-shinobi-to-dos2-migration.md` §4.2、`mods/NarutoJutsu/`

## 目标

忍术施放时播放角色喊话（如"豪火球之术！"、"千鸟！"），还原火影战斗表现。

## 现状约束（已实测确认）

1. **DOS2 音频 = Wwise**：游戏音频资源为 .wem（Wwise 容器），音频事件绑定在 .bnk（SoundBank）中
2. **SkillData 无音效字段**：DOS2 技能没有 BG3 的 PrepareSound/CastSound/TargetSound，施放音效全靠动画事件 + 特效资源自带音（见 DESIGN.md §5 音效五段）
3. **自定义音频可行链路未知**：pak 内 .wem 能否被播放、触发事件如何注册均未验证
4. **本轮网络不可达**：WebSearch/WebFetch 全部失败，无法在线验证社区方案（LSLib 是否支持 .wem/.bnk 打包播放、Wwise 事件注册方式）

## 可行链路（待逐环验证）

| 环节 | 方案 | 依赖 | 风险 |
|---|---|---|---|
| 1. 素材 | 火影招式喊话语音包（《究极风暴》等流传包，Bilibili/YouTube/Nexus） | **用户协助获取音频文件**（AI 无法下载视频音频） | 版权：个人 mod 非商用可用 |
| 2. 转换 | ogg/mp3 → .wem（Wwise 官方免费版，或社区 ww2ogg 逆向工具链） | Wwise 安装/逆向工具 | 编码参数需匹配引擎（ADPCM vs PCM） |
| 3. 事件注册 | .wem 需要 .bnk（Wwise 工程）才能被引擎调用 | Wwise 工程 | 引擎只播 bank 内注册的事件 |
| 4. 打包 | LSLib Divine create-package 可打入任意文件（已验证能力） | 无 | .wem/.bnk 路径约定未知 |
| 5. 触发 | 候选三路：<br>(a) 动画文本事件挂音频（最原生，需确认事件名绑定方式）<br>(b) SE 音频 API（DOS2SE v60+ 已装，需查 API 表）<br>(c) 自定义状态 SoundStart（仅状态生效时，非施放瞬间） | 逐个试验 | 前两路可能不可行 |

## 产物

- `docs/custom-voice-sfx-spike.md`（本文件）：链路各环节验证结论 + 可用性判定
- 判定可行后：排期"22 句台词包"（22 术 × 中文喊话，复用 jutsus.json 的 id 列表）

## 最小试验包设计

1. 1 个 .wem（用户提供或测试音）+ 触发配置
2. 触发路 (a) 优先：CastTextEvent 上挂自定义事件名，或复用现有 `"cast"` 事件
3. 实机 GM 测试：施放忍术 → 是否出声

## 验证标准

- [ ] .wem 能否被打入 pak 并被游戏加载
- [ ] 三种触发路哪条可行（或全不可行→判定放弃自定义喊话）
- [ ] 音量/延迟/多语言（喊话语言与游戏语言是否同步）

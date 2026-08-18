# 本地化（两游戏三方案，实测 2026-08-18）

## 结论速查

| 方案 | 适用 | 键格式 | XML 属性 | 状态 |
|---|---|---|---|---|
| BG3 handle 自造 | BG3 | `h<32hex>;版本` | `version="N"` | ✅ 实测可用（LSLib 往返保留自定义键；游戏只按键查找，不校验哈希） |
| DOS2 字符串键 | DOS2 | 纯文本键（=DisplayNameRef） | **无 version 属性**（有会报错！） | ✅ 打包成功，待游戏内最终确认显示 |
| DOS2 handle 键 | DOS2（Toolkit 生成） | 同 BG3 格式 | 无 version | 参考用（vanilla english.xml 实测为 handle 键） |

## 关键细节

1. **BG3 handle 自造**：handle = `h` + md5(文本) 前 32 hex，按 8-4-4-4-12 用 `g` 分隔（例 `h734ab279gfdf3g2bf6gfe31g1ceafec615e0`）。
   - 游戏只按键在 .loca 里查文本——**不需要符合官方哈希算法**（官方算法未破解，MD5/xxHash 均不对，已实测）
   - 法术条目里引用格式：`data "DisplayName" "h<handle>;1"`（分号+版本号，与 loca 的 version 一致）
2. **BG3 .loca 生成**：`Divine.exe -g bg3 --action convert-loca -s <english.xml> -d <english.loca>`（XML 带 version 属性，往返保留自定义键——已实测）
3. **DOS2 发布 XML**：pak 内 `Localization/English/english.xml`，`<content contentuid="键">文本</content>`（**无 version 属性**；加了会报 "Destination array was not long enough" 转换失败——已踩坑）
4. **DOS2 无需转 .loca**：vanilla 的 English.pak 里就是 xml（13MB）——直接发 XML
5. **pak 内路径**：`Localization/English/`（pak 根下，不在 Public/）

## 一致性校验

生成后必须检查：法术条目里的每个 handle 引用都在 loca 键集合中（我们做过：10 引用 ↔ 10 键无缺失）。DOS2 同理：`DisplayNameRef`/`DescriptionRef` 的值 = loca 键。

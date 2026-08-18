# 本地化（两游戏，实测 2026-08-18 定型）

> ⚠️ **DOS2 部分已全面重写**（v0.2.0 中文显示成功后定型）：mod 的语言 xml 不被游戏查询，
> 文本本体在 `Stats.lsb` 的 Content value。旧认知（pak 根 Localization/*.xml 双语言）已作废。

## DOS2 本地化完整机制（实证闭环）

**链路**：stats 条目 `DisplayName="<UUID>"` → 游戏查 `Public/<Folder>/Localization/Stats/<Type>_<Field>.lsb`（TranslatedStringKeys 映射）→ **直接显示 Content value 文本**。

```
技能条目（Skill_Projectile.txt）:
  data "DisplayName" "NRT_katon_goukakyu_DisplayName"   ← UUID
  data "DisplayNameRef" "|Fireball Jutsu|"               ← 语义性引用（vanilla 同款，非主路径）
        ↓
Public/NarutoJutsu/Localization/Stats/Projectile_DisplayName.lsb（TranslatedStringKeys）:
  UUID="NRT_katon_goukakyu_DisplayName" → handle="h<md5(英文文本)>" → value="火遁·豪火球之术"
        ↓
游戏直接显示 value → 中文 ✓
```

**关键规则**：

1. **value 是文本本体**：无竖线纯文本 = 直接显示（vanilla `SCROLL_Fireball` value="Fireball Scroll" 实证）；
   `|Fireball|` 竖线 = 引用游戏级 loca（`Data/Localization`）查多语言文本，查不到回退竖线内文本。
   **mod 自定义文本写中文 = 直接写 value**（英文模式也显示中文——个人 mod 取舍）。
2. **UUID 必须与条目 DisplayName 字段值完全一致**（含 `_DisplayName`/`_Description` 后缀）——
   不一致则 tooltip/状态名显示原始键（踩坑：状态 UUID 漏后缀 → "附加 NRT_AMATERASU_DisplayName 状态"）。
3. **mod 的语言 xml 游戏不查**（`Localization/English/english.xml`、`Chinese/chinese.xml` 均不参与）
   ——Larian 官方"mod 不能定义自定义本地化字符串"实锤；语言文本必须在游戏级 loca 或 Stats.lsb value。
   游戏级 loca 方案会改游戏文件 → **用户拒绝（要发布）**，不用。
4. **handle 可自造**：`h<md5(英文文本)>`（8-4-4-4-12 用 g 分隔），游戏只做 UUID→handle→value 映射，不校验算法。
5. **.lsb 生成**：先写 .lsx（头含 `lslib_meta="v1,bswap_guids"`，version 3.6.6），再 `Divine -g dos2de convert-resource` 转 .lsb。
6. **文件布局**（对照 vanilla `Public/Shared/Localization/Stats/`）：
   `Public/<Folder>/Localization/Stats/<Type>_<Field>.lsb`——按形态×字段分文件
   （Projectile_DisplayName / Projectile_Description / Rush_DisplayName / ... / Status_CONSUME_DisplayName / ...）。
7. **条目格式**（对照 vanilla Projectile_DisplayName.lsb）：
   ```xml
   <node id="TranslatedStringKey">
       <attribute id="Content" type="28" handle="h<...>" value="显示文本" />
       <attribute id="ExtraData" type="23" value="" />
       <attribute id="Speaker" type="22" value="" />
       <attribute id="Stub" type="19" value="True" />
       <attribute id="UUID" type="22" value="<DisplayName字段值>" />
   </node>
   ```
8. **游戏活动语言** = `DefEd/Data/Localization/language.lsx` 的 Value（Steam 切换语言会改写它）；游戏只在启动时加载 mod pak。

**生成器已内置**（`tools/jutsu_gen/jutsu_gen.py` → gen_stats_lsx_files + build.ps1 的 lsx→lsb 步骤），新增技能无需手工碰这些文件。

## BG3 handle 自造（保持旧结论，待实机验证）

| 项 | 结论 |
|---|---|
| BG3 loca | `.loca`（pak 根 `Localization/English/english.loca`），键 `h<handle>;版本` |
| handle 自造 | `h` + md5(文本) 前 32 hex 按 8-4-4-4-12 用 g 分隔；**未实机验证**（BG3 验证需 SE，待办） |
| 转换 | `Divine -g bg3 --action convert-loca -s <xml> -d <loca>` |

## 一致性校验

- DOS2：每个条目的 DisplayName/Description 字段值（UUID）∈ Stats.lsb 的 UUID 集合（生成器断言）。
- DOS2：所有 Stats.lsb 的 value 键对（中英文）覆盖 22 术 + 3 状态。
- BG3：handle 引用 ∈ loca 键集合（生成器断言）。

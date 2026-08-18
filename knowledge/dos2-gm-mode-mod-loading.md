# DOS2 GM 模式（地下城与城主）加载 mod 与技能（实测 2026-08-18）

> 结论来源：忍术原型 GM 模式搜不到技能 → 逐层排查 → 修复后技能面板可见。
> **三层条件缺一不可**：pak 在位 + EditorProfile 启用 + **战役 Dependencies 声明 add-on**。

## 1. 加载链路（GM 模式与单人模式不同！）

| 层 | 位置 | 作用 | 排查要点 |
|---|---|---|---|
| 1 | `Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\*.pak`（或游戏 `DefEd\Data\Mods\`） | pak 存在 | 主菜单 Mods 页能看到 = 这层通过 |
| 2 | `PlayerProfiles\EditorProfile\modsettings.lsx` | **GM 模式专用 profile** 的启用列表 | 主菜单 Mods 勾选写入这里（GM 模式与单人 profile 分开） |
| 3 | `GMCampaigns\<战役名_UUID>\meta.lsf` 的 **Dependencies** 节点 | **战役级 add-on 声明**——决定该战役加载哪些 add-on 的 stats | **最容易被漏的一层** |

- **主菜单 Mods 启用 ≠ GM 战役加载**。战役的插件页（齿轮 → 插件）看到的只是"可用 add-on 列表"；**只有声明进战役文件 Dependencies 的 add-on 才会被战役加载其 stats**。
- 单机战役（DivinityOrigins）与 GM 战役共用 EditorProfile 吗？**不**：GM 模式用 `EditorProfile`（用户名 profile 是单人模式用）。

## 2. Add-on 的 meta.lsx 必须声明 TargetModes 含 GM

```xml
<node id="TargetModes">
    <children>
        <node id="Target"><attribute id="Object" value="Story" type="22" /></node>
        <node id="Target"><attribute id="Object" value="GM" type="22" /></node>
    </children>
</node>
```

- 只声明 `Story` 的 add-on **不会出现在 GM 战役的插件页**（实测：补 GM 后立即可见）。
- 对照：GameMaster 战役（`Type="Adventure"`）= Story+GM；add-on 建议双声明（单人/GM 都能用）。

## 3. 战役文件写入 add-on 依赖（手动法，游戏内勾选失败的备选）

`GMCampaigns\<campaign>\meta.lsf` 是二进制，用 LSLib 转格式改：

```bash
# 1) 备份 + 转 lsx
cp "<campaign>/meta.lsf" meta.lsf.bak
Divine.exe -g dos2de --action convert-resource -s "<campaign>/meta.lsf" -d meta.lsx
# 2) 编辑 lsx：在 <node id="Dependencies"/> 里加（注意 lslib 转换格式：id/type/value 属性顺序）
#   <node id="ModuleShortDesc">
#       <attribute id="UUID" type="22" value="<mod-uuid>" />
#       <attribute id="Name" type="22" value="<mod-name>" />
#       <attribute id="Version" type="4" value="<version>" />
#       <attribute id="MD5" type="23" value="" />
#       <attribute id="Folder" type="30" value="<mod-folder>" />
#   </node>
# 3) 转回 lsf
Divine.exe -g dos2de --action convert-resource -s meta.lsx -d "<campaign>/meta.lsf"
```

- mod UUID/Version 与 `Mods/<Folder>/meta.lsx` 的 ModuleInfo 一致（如 NarutoJutsu：UUID `5d2e3f1a-...`、Version `268435456`）。
- 战役本身的 `MainGMMod`（GameMaster）保持不变。
- 游戏内正确流程：GM 战役选择界面 → 右下角齿轮 → 插件页 → 勾选 add-on（此动作应写入上述 Dependencies；实测勾选后文件未见写入，改为手动法成功）。

## 4. DOS2 本地化：GM 面板显示名必须"键名 + 竖线引用"配对

stats 条目 + `Localization/English/english.xml` **三处必须配对**：

```txt
data "DisplayName" "NRT_katon_goukakyu_DisplayName"
data "DisplayNameRef" "|NRT_katon_goukakyu_DisplayName|"   ← 竖线引用，本体格式
data "Description" "NRT_katon_goukakyu_Description"
data "DescriptionRef" "|NRT_katon_goukakyu_Description|"
```

```xml
<content contentuid="NRT_katon_goukakyu_DisplayName">Fireball Jutsu</content>
```

- ❌ 裸文本 `DisplayNameRef "Fireball Jutsu"`（无竖线）实测显示异常；✅ 竖线引用 `|键|` + contentuid 配对。
- 技能面板无搜索框，只能按**学派（Ability）分类**翻，注意 **Tier 分组**（Novice/Adept/Master）——豪火球 Tier=Adept 在 Adept 分组下。

## 5. 其他实测

- **日志**：`DefEd\bin\gold.log`（release 版极简，只有 GameState 切换，无 stats 加载细节；Documents 下无 Game.log）。
- **打包坑**：Divine create-package 的输出路径**不能在输入目录内**（文件自锁报 IOException）。
- **bash 中文路径**：显示为乱码但实际写入正确（UTF-8 字节，勿因此误判）。
- 条目字段：`ForGameMaster "Yes"` 必须；`MemorizationRequirements`/`Memory Cost`/`CycleConditions`/`ExplodeRadius` 缺失**不影响加载**（只影响记忆/循环），GM 面板列表可见。
- 备份：本次战役 meta.lsf 备份在 `tmp/战役测试_meta.lsf.bak`。

# pak 结构与 meta.lsx 格式（实测 2026-08-18）

## pak 内结构（两游戏一致，对照游戏本体 pak 实测）

```
Mods/<Folder>/meta.lsx          ← 模组清单（必须在 Mods/<Folder>/ 下，不在根！）
Mods/<Folder>/...               ← Story/脚本/GUI 等
Public/<Folder>/...             ← Stats/对话/Timeline/职业/成长表等数据
Localization/English/...        ← 本地化（BG3: english.loca + .xml；DOS2: english.xml）
```

## meta.lsx 格式（两游戏都是 Config 区域，不是 Module 区域！）

结构：`<region id="Config">` → `<node id="root">` → children: `Conflicts`/`Dependencies`/`ModuleInfo`

**BG3**（version `4.8`，对照 Shared.pak 内 meta）：
```xml
<version major="4" minor="8" revision="0" build="500"/>
<attribute id="Folder" type="LSString" value="NarutoJutsu"/>
<attribute id="Name" type="LSString" value="NarutoJutsu"/>
<attribute id="UUID" type="FixedString" value="<guid>"/>
<attribute id="Version64" type="int64" value="36028797018963968"/>   ← int64！
<attribute id="FileSize" type="uint64" value="0"/>
<attribute id="PublishHandle" type="uint64" value="0"/>
<attribute id="MD5" type="LSString" value=""/>
```
依赖（官方平台 mod 的写法，Dependencies 里每个 ModuleShortDesc 带 Folder/MD5/Name/PublishHandle/UUID/Version64）：
官方 mod 列了 DiceSet_01/02/03/06、MainUI、ModBrowser、PhotoMode、CrossplayUI、Gustav（主战役）等——**最少也要依赖主战役 Gustav**（UUID `991c9c7a-fb80-40cb-8f0d-b92d4e80e9b1`）。

**DOS2**（version `3.6`，对照 Shared.pak 内 meta + myFirstMod）：
```xml
<version major="3" minor="6" revision="0" build="3"/>
<attribute id="Folder" value="NarutoJutsu" type="30"/>
<attribute id="Name" value="NarutoJutsu" type="22"/>
<attribute id="UUID" value="<guid>" type="22"/>
<attribute id="Version" value="268435456" type="4"/>          ← int32！
<attribute id="Type" value="Add-on" type="22"/>
<attribute id="Tags" value="" type="30"/>
```
依赖（Dependencies）：**必须依赖主战役** `DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4`（Folder=DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4, Name=Divinity: Original Sin 2, UUID=1301db3d-1f54-4e98-9be5-5094030916e4, Version=373234071, MD5=73d13f95607b70c953cc32e56d62b7d7）。

## 关键教训

- ❌ meta.lsx 放 pak 根 → 不识别（必须在 Mods/<Folder>/）
- ❌ Module 区域格式 → 不识别（必须是 Config/root/ModuleInfo）
- ⚠️ meta.lsx 里 MD5 空值：myFirstMod 也空，游戏仍识别；MD5 是打包时整体资源校验，非 meta 自身哈希（实测不符）
- 打包命令：`Divine.exe -g dos2de|bg3 --action create-package -s <含Mods/> -d <out.pak>`

## 参考样本（解包数据）

- DOS2 本体 meta：`extracted/DOS2/Mods/Shared/meta.lsx`
- BG3 本体 meta：`extracted/BG3/_meta_bg3.lsx`
- 官方平台 mod meta：`extracted/Reference_narutotest/Mods/narutotest_<uuid>/meta.lsx`

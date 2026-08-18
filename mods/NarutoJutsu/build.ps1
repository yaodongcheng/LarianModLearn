# 忍术原型打包脚本（在项目根目录运行：powershell -File mods/NarutoJutsu/build.ps1）
$divine = 'F:\LarianModLearn\tools\ExportTool-v1.20.4\Packed\Tools\Divine.exe'
# 0) TranslatedStringKeys .lsx -> .lsb（Stats.lsb 是 mod 本地化映射表，缺它技能名显示原始键）
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Projectile_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Projectile_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Projectile_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Projectile_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Rush_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Rush_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Rush_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Rush_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Shout_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Shout_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Shout_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Shout_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_CONSUME_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_CONSUME_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_CONSUME_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_CONSUME_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_DAMAGE_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_DAMAGE_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_DAMAGE_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Status_DAMAGE_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Summon_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Summon_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Summon_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Summon_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Target_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Target_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Target_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Target_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Teleportation_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Teleportation_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Teleportation_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Teleportation_DisplayName.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Zone_Description.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Zone_Description.lsb"
& $divine -g dos2de --action convert-resource -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Zone_DisplayName.lsx" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2\Public\NarutoJutsu\Localization\Stats\Zone_DisplayName.lsb"
# 1) BG3 本地化 XML -> .loca（DOS2 直接发布 XML，游戏原生格式）
& $divine -g bg3 --action convert-loca -s "F:\LarianModLearn\mods\NarutoJutsu\BG3\Localization\English\english.xml" -d "F:\LarianModLearn\mods\NarutoJutsu\BG3\Localization\English\english.loca"
# 2) 打包（-s 传含 meta.lsx 的目录；DOS2 双语言 Localization/English + Localization/Chinese 一并入包）
& $divine -g dos2de --action create-package -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2.pak"
& $divine -g bg3 --action create-package -s "F:\LarianModLearn\mods\NarutoJutsu\BG3" -d "F:\LarianModLearn\mods\NarutoJutsu\BG3.pak"
# 3) 安装：复制 .pak 到 Mods 目录
#   BG3:  %LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\
#   DOS2: %USERPROFILE%\Documents\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\（DOS2 用 Documents，不是 LocalAppData）

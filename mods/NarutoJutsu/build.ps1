# 忍术原型打包脚本（在项目根目录运行：powershell -File mods/NarutoJutsu/build.ps1）
$divine = 'F:\LarianModLearn\tools\ExportTool-v1.20.4\Packed\Tools\Divine.exe'
# 1) BG3 本地化 XML -> .loca（DOS2 直接发布 XML，游戏原生格式）
& $divine -g bg3 --action convert-loca -s "F:\LarianModLearn\mods\NarutoJutsu\BG3\Localization\English\english.xml" -d "F:\LarianModLearn\mods\NarutoJutsu\BG3\Localization\English\english.loca"
# 2) 打包（-s 传含 meta.lsx 的目录）
& $divine -g dos2de --action create-package -s "F:\LarianModLearn\mods\NarutoJutsu\DOS2" -d "F:\LarianModLearn\mods\NarutoJutsu\DOS2.pak"
& $divine -g bg3 --action create-package -s "F:\LarianModLearn\mods\NarutoJutsu\BG3" -d "F:\LarianModLearn\mods\NarutoJutsu\BG3.pak"
# 3) 安装：复制 .pak 到 Mods 目录
#   BG3:  %LocalAppData%\Larian Studios\Baldur's Gate 3\Mods\
#   DOS2: %LocalAppData%\Larian Studios\Divinity Original Sin 2 Definitive Edition\Mods\

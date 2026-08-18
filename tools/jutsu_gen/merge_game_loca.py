#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把忍术 mod 的本地化键合并进游戏级中文 loca（3DM/Larian 论坛验证路径）：
  原版 Chinese.pak 的 chinese.xml（92k 条）+ 我们的 50 条 → DefEd/Data/Localization/Chinese/chinese.xml 松散文件
背景：DOS2 mod 级 Localization 自定义字符串不被游戏加载（Larian 官方确认不支持）；
  游戏级 Data/Localization/<Lang>/<lang>.xml 松散文件被加载（3DM 汉化补丁同款）。
用法：python tools/jutsu_gen/merge_game_loca.py [--backup] [--restore]
"""
import re
import shutil
import sys
from pathlib import Path

GAME_LOCA = Path("G:/SteamLibrary/steamapps/common/Divinity Original Sin 2/DefEd/Data/Localization/Chinese/chinese.xml")
VANILLA_SRC = Path("F:/LarianModLearn/extracted/DOS2/_chk/Localization/Chinese/chinese.xml")  # 原版提取备份
OURS = Path("F:/LarianModLearn/mods/NarutoJutsu/DOS2/Localization/Chinese/chinese.xml")
BAK = Path("F:/LarianModLearn/tmp/game_chinese.xml.bak")

def restore():
    if not BAK.exists():
        print("无备份可恢复:", BAK)
        return
    shutil.copy(BAK, GAME_LOCA)
    print("已恢复原版 chinese.xml（来自备份）")

def merge():
    if not VANILLA_SRC.exists():
        print("缺少原版提取源:", VANILLA_SRC, "（需先从 Chinese.pak 提取）")
        sys.exit(1)
    vanilla = VANILLA_SRC.read_text(encoding="utf-8")
    ours = OURS.read_text(encoding="utf-8")

    our_lines = [l for l in ours.splitlines() if "<content" in l]
    vanilla_keys = set(re.findall(r'contentuid="([^"]+)"', vanilla))
    our_keys = set(re.findall(r'contentuid="([^"]+)"', ours))
    dup = our_keys & vanilla_keys
    assert not dup, f"键冲突: {dup}"

    # 备份现有游戏文件（首次运行时）
    if GAME_LOCA.exists() and not BAK.exists():
        shutil.copy(GAME_LOCA, BAK)
        print("已备份现有游戏 chinese.xml →", BAK)

    merged = vanilla.replace("</contentList>", "\n".join(our_lines) + "\n</contentList>")
    GAME_LOCA.write_text(merged, encoding="utf-8", newline="")
    print(f"已写入 {len(our_lines)} 条合并: {GAME_LOCA} ({GAME_LOCA.stat().st_size} bytes)")

if __name__ == "__main__":
    if "--restore" in sys.argv:
        restore()
    else:
        merge()

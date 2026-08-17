#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
忍术生成器：从 spec/jutsus.json 生成 BG3 / DOS2 的配表条目与本地化。
原理：复刻游戏原生技能（火球/冲撞/射线/怒吼/区域）的字段集，替换为忍术规格。

用法：python tools/jutsu_gen/jutsu_gen.py
产物：
  mods/NarutoJutsu/DOS2/Public/NarutoJutsu/Stats/Generated/Data/Skill_Naruto.txt
  mods/NarutoJutsu/DOS2/Public/NarutoJutsu/Localization/English/english.xml (→ .loca)
  mods/NarutoJutsu/BG3/Public/NarutoJutsu/Stats/Generated/Data/Spell_Naruto.txt
  mods/NarutoJutsu/BG3/Public/NarutoJutsu/Localization/English/english.xml (→ .loca)
  mods/NarutoJutsu/build.ps1（打包命令）
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "mods" / "NarutoJutsu" / "spec" / "jutsus.json"
OUT = ROOT / "mods" / "NarutoJutsu"

# ---------- 工具 ----------

def fmt_handle(text: str) -> str:
    """生成 BG3 本地化 handle：h + md5(text) 前 32 hex，按 8-4-4-4-12 用 g 分隔。
    说明：handle 只是 loca 键，游戏按键查找，与文本无需满足官方哈希算法（已实测 LSLib 往返保留自定义键）。"""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return f"h{h[0:8]}g{h[8:12]}g{h[12:16]}g{h[16:20]}g{h[20:32]}"

def loca_xml(entries, with_version=True) -> str:
    """entries: list[(uid, version, text)]；BG3 需 version 属性，DOS2 不需要（格式差异已实测）"""
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<contentList>"]
    for uid, version, text in entries:
        text_xml = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ver = f' version="{version}"' if with_version else ""
        lines.append(f'\t<content contentuid="{uid}"{ver}>{text_xml}</content>')
    lines.append("</contentList>")
    return "\n".join(lines) + "\n"

# ---------- DOS2 条目生成 ----------

def gen_dos2_entry(j, shape):
    d = j["dos2"]
    aid = f"NRT_{j['id']}"
    lines = [f'new entry "{aid}"', 'type "SkillData"', f'data "SkillType" "{shape}"']

    def opt(fmt, key=None, include=True):
        """惰性格式化：key 存在时才格式化，避免 KeyError"""
        if not include:
            return None
        if key is not None and key not in d:
            return None
        return fmt

    common = [
        (lambda: 'data "ForGameMaster" "Yes"', True),
        (lambda: f'data "Ability" "{d["ability"]}"', True),
        (lambda: f'data "Tier" "{d.get("tier", "Novice")}"', True),
        (lambda: f'data "Requirement" "{d["requirement"]}"', "requirement" in d),
        (lambda: f'data "ActionPoints" "{d["ap"]}"', True),
        (lambda: f'data "Cooldown" "{d["cooldown"]}"', True),
        (lambda: f'data "Damage Multiplier" "{d["dmgMult"]}"', True),
        (lambda: 'data "Damage Range" "10"', True),
        (lambda: f'data "DamageType" "{d["dmgType"]}"', "dmgType" in d),
        (lambda: f'data "SkillProperties" "{d["properties"]}"', True),
        (lambda: f'data "AddWeaponRange" "{d["addWeaponRange"]}"', "addWeaponRange" in d),
        (lambda: f'data "TargetRadius" "{d["targetRadius"]}"', "targetRadius" in d and shape in ("Projectile", "Zone", "Rush")),
        (lambda: f'data "AreaRadius" "{d["areaRadius"]}"', "areaRadius" in d),
        (lambda: f'data "HitRadius" "{d.get("hitRadius", 1)}"', shape == "Rush"),
        (lambda: f'data "DeathType" "{d["deathType"]}"', True),
        (lambda: f'data "TargetConditions" "{d["targetConditions"]}"', "targetConditions" in d),
        (lambda: 'data "CanTargetCharacters" "Yes"', True),
        (lambda: 'data "CanTargetItems" "Yes"', True),
        (lambda: 'data "CanTargetTerrain" "Yes"', True),
        (lambda: 'data "ForceTarget" "No"', shape == "Projectile"),
        (lambda: 'data "UseCharacterStats" "No"', True),
        (lambda: 'data "UseWeaponDamage" "No"', shape in ("Projectile", "Zone", "Shout")),
        (lambda: 'data "UseWeaponProperties" "No"', shape in ("Projectile", "Zone", "Shout")),
        (lambda: 'data "ProjectileCount" "1"', shape == "Projectile"),
        (lambda: 'data "ProjectileDelay" "0"', shape == "Projectile"),
        (lambda: f'data "Template" "{d["template"]}"', shape == "Projectile"),
        (lambda: f'data "Icon" "{d["icon"]}"', True),
        (lambda: f'data "DisplayName" "{aid}_DisplayName"', True),
        (lambda: f'data "DisplayNameRef" "{j["nameEn"]}"', True),
        (lambda: f'data "Description" "{aid}_Description"', True),
        (lambda: f'data "DescriptionRef" "{j["descriptionEn"]}"', True),
        (lambda: 'data "StatsDescriptionParams" "Damage"', shape in ("Projectile", "Zone")),
        (lambda: f'data "PrepareAnimationInit" "{d["animPrepareInit"]}"', "animPrepareInit" in d),
        (lambda: f'data "PrepareAnimationLoop" "{d["animPrepareLoop"]}"', "animPrepareLoop" in d),
        (lambda: f'data "CastAnimation" "{d["animCast"]}"', "animCast" in d),
        (lambda: 'data "CastTextEvent" "cast"', shape in ("Projectile", "Zone", "Shout")),
        (lambda: f'data "CastEffect" "{d["castEffect"]}"', "castEffect" in d),
        (lambda: 'data "Magic Cost" "0"', True),
        (lambda: 'data "ProjectileTerrainOffset" "Yes"', shape == "Projectile"),
        (lambda: 'data "OverrideMinAP" "No"', shape == "Projectile"),
    ]
    for fmt, include in common:
        if include:
            lines.append(fmt())
    return "\n".join(lines)

def gen_dos2():
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    out_dir = OUT / "DOS2" / "Public" / "NarutoJutsu"
    stats_dir = out_dir / "Stats" / "Generated" / "Data"
    # DOS2 本地化：pak 根 Localization/English/english.xml（游戏原生即 XML，与 English.pak 同构）
    loca_dir = OUT / "DOS2" / "Localization" / "English"
    stats_dir.mkdir(parents=True, exist_ok=True)
    loca_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    loca_entries = []
    for j in data["jutsus"]:
        shape = j["dos2"]["shape"]
        entries.append(gen_dos2_entry(j, shape))
        # loca: 键 = 显示名/描述文本（DOS2 loca 键为字符串，与 DisplayNameRef/DescriptionRef 一致）
        loca_entries.append((j["nameEn"], 1, j["nameEn"]))
        loca_entries.append((j["descriptionEn"], 1, j["descriptionEn"]))
    (stats_dir / "Skill_Naruto.txt").write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    (loca_dir / "english.xml").write_text(loca_xml(loca_entries, with_version=False), encoding="utf-8")
    return stats_dir / "Skill_Naruto.txt", loca_dir / "english.xml"

# ---------- BG3 条目生成 ----------

def gen_bg3_entry(j, shape):
    d = j["bg3"]
    aid = f"NRT_{j['id']}"
    loc_ver = 1
    display_handle = fmt_handle(j["nameEn"])
    desc_handle = fmt_handle(j["descriptionEn"])
    lines = [f'new entry "{aid}"', 'type "SpellData"', f'data "SpellType" "{shape}"',
             f'data "Level" "{d["level"]}"']
    if "school" in d:
        lines.append(f'data "SpellSchool" "{d["school"]}"')
    # Zone 专用
    if shape == "Zone":
        lines += [f'data "SurfaceType" "{d["surfaceType"]}"',
                  f'data "SurfaceLifetime" "{d["surfaceLifetime"]}"',
                  f'data "SurfaceGrowStep" "{d["surfaceGrowStep"]}"',
                  f'data "SurfaceGrowInterval" "{d["surfaceGrowInterval"]}"']
    # Projectile 专用
    if shape == "Projectile":
        if d["properties"]:
            lines.append(f'data "SpellProperties" "{d["properties"]}"')
        lines += [f'data "TargetFloor" "{d["targetFloor"]}"',
                  f'data "TargetRadius" "{d["targetRadius"]}"',
                  f'data "SpellRoll" "{d["spellRoll"]}"',
                  f'data "SpellSuccess" "{d["spellSuccess"]}"',
                  f'data "TargetConditions" "{d["targetConditions"]}"',
                  f'data "ProjectileCount" "1"',
                  f'data "Trajectories" "{d["trajectories"]}"']
    # Rush 专用
    if shape == "Rush":
        lines += [f'data "Cooldown" "{d["cooldown"]}"',
                  f'data "TargetRadius" "{d["targetRadius"]}"',
                  f'data "HitRadius" "{d["hitRadius"]}"',
                  f'data "MovementSpeed" "{d["movementSpeed"]}"',
                  f'data "SpellRoll" "{d["spellRoll"]}"',
                  f'data "SpellSuccess" "{d["spellSuccess"]}"',
                  f'data "TargetConditions" "{d["targetConditions"]}"',
                  f'data "Requirements" "{d["requirements"]}"',
                  f'data "CycleConditions" "{d["cycleConditions"]}"',
                  f'data "UseCosts" "{d["useCosts"]}"',
                  f'data "SpellAnimation" "{d["spellAnimation"]}"',
                  f'data "WeaponTypes" "{d["weaponTypes"]}"',
                  f'data "SpellFlags" "{d["spellFlags"]}"',
                  f'data "SpellAnimationIntentType" "{d["spellAnimationIntentType"]}"',
                  f'data "RechargeValues" "{d["rechargeValues"]}"',
                  f'data "VerbalIntent" "{d["verbalIntent"]}"']
    # Zone 的施法骰（Zone 需要 SpellRoll/SpellSuccess/SpellFail）
    if shape == "Zone":
        lines += [f'data "SpellRoll" "{d["spellRoll"]}"',
                  f'data "SpellSuccess" "{d["spellSuccess"]}"',
                  f'data "SpellFail" "{d["spellFail"]}"',
                  f'data "TargetConditions" "{d["targetConditions"]}"']
    lines += [f'data "Icon" "{d["icon"]}"',
              f'data "DisplayName" "{display_handle};{loc_ver}"',
              f'data "Description" "{desc_handle};{loc_ver}"',
              f'data "TooltipDamageList" "{d["tooltipDamage"]}"']
    if "tooltipStatus" in d:
        lines.append(f'data "TooltipStatusApply" "{d["tooltipStatus"]}"')
    if shape == "Rush":
        lines += [f'data "CastSound" "{d["castSound"]}"',
                  f'data "CastTextEvent" "{d["castTextEvent"]}"']
    return "\n".join(lines), (display_handle, loc_ver, j["nameEn"]), (desc_handle, loc_ver, j["descriptionEn"])

def gen_bg3():
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    out_dir = OUT / "BG3" / "Public" / "NarutoJutsu"
    stats_dir = out_dir / "Stats" / "Generated" / "Data"
    # BG3 本地化：pak 根 Localization/English/english.xml + .loca 二进制（BG3 游戏内为 .loca）
    loca_dir = OUT / "BG3" / "Localization" / "English"
    stats_dir.mkdir(parents=True, exist_ok=True)
    loca_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    loca_entries = []
    for j in data["jutsus"]:
        shape = j["bg3"]["shape"]
        entry, disp, desc = gen_bg3_entry(j, shape)
        entries.append(entry)
        loca_entries.extend([disp, desc])
    (stats_dir / "Spell_Naruto.txt").write_text("\n\n".join(entries) + "\n", encoding="utf-8")
    (loca_dir / "english.xml").write_text(loca_xml(loca_entries), encoding="utf-8")
    return stats_dir / "Spell_Naruto.txt", loca_dir / "english.xml"

# ---------- meta.lsx + 打包脚本 ----------

def gen_meta_lsx(game: str, mod_uuid: str) -> str:
    name = "NarutoJutsu"
    if game == "dos2de":
        return f'''<?xml version="1.0" encoding="utf-8"?>
<save>
  <version major="4" minor="0" revision="0" build="16" />
  <region id="Module">
    <node id="Module">
      <attribute id="Folder" type="LSString" value="{name}" />
      <attribute id="Name" type="LSString" value="{name}" />
      <attribute id="UUID" type="guid" value="{mod_uuid}" />
      <attribute id="Version" type="int32" value="1" />
      <attribute id="Type" type="int32" value="2" />
      <attribute id="Author" type="LSString" value="LarianModLearn" />
      <attribute id="Description" type="LSString" value="Naruto jutsu prototype (DOS2)" />
    </node>
  </region>
</save>
'''
    return f'''<?xml version="1.0" encoding="utf-8"?>
<save>
  <version major="4" minor="0" revision="0" build="16" />
  <region id="Module">
    <node id="Module">
      <attribute id="Folder" type="LSString" value="{name}" />
      <attribute id="Name" type="LSString" value="{name}" />
      <attribute id="UUID" type="guid" value="{mod_uuid}" />
      <attribute id="Version" type="int32" value="1" />
      <attribute id="Type" type="int32" value="1" />
      <attribute id="Author" type="LSString" value="LarianModLearn" />
      <attribute id="Description" type="LSString" value="Naruto jutsu prototype (BG3)" />
    </node>
  </region>
</save>
'''

def gen_build_script(dos2_stats, dos2_loca, bg3_stats, bg3_loca):
    divine = str(ROOT / "tools" / "ExportTool-v1.20.4" / "Packed" / "Tools" / "Divine.exe").replace("/", "\\")
    dos2_root = OUT / "DOS2"
    bg3_root = OUT / "BG3"
    lines = [
        "# 忍术原型打包脚本（在项目根目录运行：powershell -File mods/NarutoJutsu/build.ps1）",
        "$divine = '%s'" % divine,
        "# 1) BG3 本地化 XML -> .loca（DOS2 直接发布 XML，游戏原生格式）",
        f'& $divine -g bg3 --action convert-loca -s "{bg3_loca}" -d "{bg3_loca.with_suffix(".loca")}"',
        "# 2) 打包（-s 传含 meta.lsx 的目录）",
        f'& $divine -g dos2de --action create-package -s "{dos2_root}" -d "{dos2_root}.pak"',
        f'& $divine -g bg3 --action create-package -s "{bg3_root}" -d "{bg3_root}.pak"',
        "# 3) 安装：复制 .pak 到 Mods 目录",
        '#   BG3:  %LocalAppData%\\Larian Studios\\Baldur\'s Gate 3\\Mods\\',
        '#   DOS2: %LocalAppData%\\Larian Studios\\Divinity Original Sin 2 Definitive Edition\\Mods\\',
    ]
    return "\n".join(lines) + "\n"

def main():
    dos2_stats, dos2_loca = gen_dos2()
    bg3_stats, bg3_loca = gen_bg3()
    # meta.lsx（两个固定 mod UUID）
    (OUT / "DOS2" / "meta.lsx").write_text(gen_meta_lsx("dos2de", "11111111-1111-4111-8111-111111111111"), encoding="utf-8")
    (OUT / "BG3" / "meta.lsx").write_text(gen_meta_lsx("bg3", "22222222-2222-4222-8222-222222222222"), encoding="utf-8")
    (OUT / "build.ps1").write_text(gen_build_script(dos2_stats, dos2_loca, bg3_stats, bg3_loca), encoding="utf-8")
    print(f"[OK] DOS2: {dos2_stats}")
    print(f"[OK] DOS2 loca: {dos2_loca}")
    print(f"[OK] BG3: {bg3_stats}")
    print(f"[OK] BG3 loca: {bg3_loca}")
    print(f"[OK] build.ps1 已生成（含 loca 转换与打包命令）")

if __name__ == "__main__":
    main()

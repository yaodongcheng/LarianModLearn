#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
忍术生成器：从 spec/jutsus.json 生成 BG3 / DOS2 的配表条目与本地化。
原理：复刻游戏原生技能（火球/冲撞/射线/怒吼/区域/传送/召唤）的字段集，替换为忍术规格。

用法：python tools/jutsu_gen/jutsu_gen.py
产物：
  DOS2:
    Public/NarutoJutsu/Stats/Generated/Data/Skill_{Projectile,Rush,Shout,Zone,Target,Teleportation,Summon}.txt
    Public/NarutoJutsu/Stats/Generated/Data/Status_{CONSUME,DAMAGE}.txt   （自定义状态：写轮眼/万花筒/天照）
    Public/NarutoJutsu/Stats/Generated/Data/Potion.txt                    （SKILLBOOST_* 增益条目）
    Public/NarutoJutsu/Stats/Generated/Data/Weapon.txt                    （Damage_NRT_Amaterasu DoT 伤害条目）
    Localization/English/english.xml + Localization/Chinese/chinese.xml    （双语言，键集合断言相等）
  BG3:
    Public/NarutoJutsu/Stats/Generated/Data/Spell_{Projectile,Rush,Zone}.txt （仅含 bg3 段的术）
    Localization/English/english.{xml,loca}
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

def xml_keys(xml_text: str) -> set:
    return set(re.findall(r'contentuid="([^"]+)"', xml_text))

# ---------- DOS2 条目生成 ----------

def gen_dos2_entry(j, shape):
    """生成单个忍术的 DOS2 SkillData 条目。字段集按形态对照原生条目：
    Projectile=火球类 / Rush=冲锋 / Shout=怒吼 / Zone=区域 / Target=单体 /
    Teleportation=Teleportation_FreeFall / Summon=Summon_EnemyDemon_Doctor+Summon_Incarnate"""
    d = j["dos2"]
    aid = f"NRT_{j['id']}"
    L = [f'new entry "{aid}"', 'type "SkillData"', f'data "SkillType" "{shape}"']
    L.append('data "ForGameMaster" "Yes"')
    L.append(f'data "Ability" "{d["ability"]}"')
    L.append(f'data "Tier" "{d.get("tier", "Novice")}"')
    if "requirement" in d:
        L.append(f'data "Requirement" "{d["requirement"]}"')
    L.append(f'data "ActionPoints" "{d["ap"]}"')
    L.append(f'data "Cooldown" "{d["cooldown"]}"')
    # 伤害块：有 dmgMult 才有伤害字段（纯功能术如雾隐/写轮眼/瞬身不写）
    if "dmgMult" in d:
        L.append(f'data "Damage Multiplier" "{d["dmgMult"]}"')
        L.append('data "Damage Range" "10"')
        if "dmgType" in d:
            L.append(f'data "DamageType" "{d["dmgType"]}"')
    if "properties" in d:
        L.append(f'data "SkillProperties" "{d["properties"]}"')
    if "addWeaponRange" in d:
        L.append(f'data "AddWeaponRange" "{d["addWeaponRange"]}"')
    # 形态专用字段
    if shape == "Projectile":
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              f'data "AreaRadius" "{d.get("areaRadius", 1)}"',
              'data "ForceTarget" "No"', 'data "UseCharacterStats" "No"',
              'data "UseWeaponDamage" "No"', 'data "UseWeaponProperties" "No"',
              f'data "ProjectileCount" "{d.get("projectileCount", 1)}"',
              'data "ProjectileDelay" "0"',
              f'data "Template" "{d["template"]}"']
        if "angle" in d:
            L.append(f'data "Angle" "{d["angle"]}"')
    elif shape == "Rush":
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              f'data "HitRadius" "{d.get("hitRadius", 1)}"',
              'data "UseCharacterStats" "No"']
    elif shape == "Shout":
        L += ['data "UseCharacterStats" "No"', 'data "UseWeaponDamage" "No"',
              'data "UseWeaponProperties" "No"']
    elif shape == "Zone":
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              f'data "AreaRadius" "{d.get("areaRadius", 3)}"',
              'data "UseCharacterStats" "No"', 'data "UseWeaponDamage" "No"',
              'data "UseWeaponProperties" "No"']
        if "surfaceType" in d:
            # Zone 原生 SurfaceType 字段（对照 Zone_EnemyLaserRayCursed 的 FireCursed）
            L.append(f'data "SurfaceType" "{d["surfaceType"]}"')
    elif shape == "Target":
        # 对照 Target_SourceVampirism：单体直击，不可指向物品/地形
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              'data "UseCharacterStats" "No"', 'data "UseWeaponDamage" "No"',
              'data "UseWeaponProperties" "No"',
              'data "CanTargetCharacters" "Yes"', 'data "CanTargetItems" "No"',
              'data "CanTargetTerrain" "No"']
    elif shape == "Teleportation":
        # 对照 Teleportation_FreeFall：投掷目标升空坠落（神威=空间扭曲）
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              f'data "AreaRadius" "{d["areaRadius"]}"',
              f'data "HitRadius" "{d.get("hitRadius", 1)}"',
              f'data "Height" "{d["height"]}"',
              f'data "Acceleration" "{d["acceleration"]}"',
              f'data "TeleportDelay" "{d["teleportDelay"]}"',
              f'data "TeleportSelf" "{d["teleportSelf"]}"',
              f'data "CanTargetCharacters" "{d.get("canTargetCharacters", "Yes")}"',
              f'data "CanTargetItems" "{d.get("canTargetItems", "No")}"',
              f'data "CanTargetTerrain" "{d.get("canTargetTerrain", "No")}"',
              'data "UseCharacterStats" "No"']
    elif shape == "Summon":
        # 对照 Summon_Incarnate / Summon_EnemyDemon_Doctor
        L += [f'data "Lifetime" "{d["lifetime"]}"',
              f'data "SummonLevel" "{d["summonLevel"]}"',
              f'data "Template" "{d["template"]}"']
        if "templateAdvanced" in d:
            L += [f'data "TemplateAdvanced" "{d["templateAdvanced"]}"',
                  f'data "TemplateOverride" "{d["templateAdvanced"]}"']
        L += [f'data "TargetRadius" "{d["targetRadius"]}"',
              f'data "SummonCount" "{d["summonCount"]}"',
              f'data "FXScale" "{d.get("fxScale", 100)}"']
    if "deathType" in d:
        L.append(f'data "DeathType" "{d["deathType"]}"')
    if "targetConditions" in d:
        L.append(f'data "TargetConditions" "{d["targetConditions"]}"')
    if shape not in ("Summon", "Target", "Teleportation"):
        L += ['data "CanTargetCharacters" "Yes"', 'data "CanTargetItems" "Yes"',
              'data "CanTargetTerrain" "Yes"']
    L.append(f'data "Icon" "{d["icon"]}"')
    # 本地化（2026-08-18 实证修正）：DisplayNameRef 竖线里是【英文显示文本】而非键名！
    # 参照 vanilla Projectile_Fireball: DisplayNameRef "|Fireball|"（英文文本），游戏按文本匹配
    # 双语言 loca 的同一 handle 键（h<md5(英文文本)>），再取当前语言文本。
    # 旧做法（ref=键名 NRT_*_DisplayName）游戏按文本索引找不到 → 显示原始键（三包实测均失败）。
    name_handle = fmt_handle(j["nameEn"])
    desc_handle = fmt_handle(j["descriptionEn"])
    L += [f'data "DisplayName" "{aid}_DisplayName"',
          f'data "DisplayNameRef" "|{j["nameEn"]}|"',
          f'data "Description" "{aid}_Description"',
          f'data "DescriptionRef" "|{j["descriptionEn"]}|"']
    if "dmgMult" in d and shape in ("Projectile", "Zone", "Target"):
        L.append('data "StatsDescriptionParams" "Damage"')
    # 动画三件套（准备/施放自带音效，原生动画名）
    if "animPrepareInit" in d:
        L.append(f'data "PrepareAnimationInit" "{d["animPrepareInit"]}"')
    if "animPrepareLoop" in d:
        L.append(f'data "PrepareAnimationLoop" "{d["animPrepareLoop"]}"')
    if "animCast" in d:
        L.append(f'data "CastAnimation" "{d["animCast"]}"')
    # 施放帧文本事件（触发施放动作音效的帧）——Summon 另有 CastEffectTextEvent
    if shape in ("Projectile", "Zone", "Shout", "Target", "Teleportation", "Summon"):
        L.append('data "CastTextEvent" "cast"')
    if shape == "Summon":
        L.append('data "CastEffectTextEvent" "cast"')
    if "prepareEffect" in d:
        L.append(f'data "PrepareEffect" "{d["prepareEffect"]}"')
    if "castEffect" in d:
        L.append(f'data "CastEffect" "{d["castEffect"]}"')
    if "disappearEffect" in d:
        L.append(f'data "DisappearEffect" "{d["disappearEffect"]}"')
    if "reappearEffect" in d:
        L.append(f'data "ReappearEffect" "{d["reappearEffect"]}"')
    if "targetCastEffect" in d:
        L.append(f'data "TargetCastEffect" "{d["targetCastEffect"]}"')
    L.append('data "Magic Cost" "0"')
    if shape == "Projectile":
        L += ['data "ProjectileTerrainOffset" "Yes"', 'data "OverrideMinAP" "No"']
    return "\n".join(L)

# ---------- DOS2 自定义状态 / 增益 / DoT 伤害 ----------

def gen_dos2_statuses(data):
    """自定义状态三件套（官方文件名分发）：
    1) Status_CONSUME.txt — 写轮眼/万花筒（StatsId → SKILLBOOST_*，Potion 增益条目）
    2) Status_DAMAGE.txt  — 天照黑炎（DamageEvent OnTurn + DamageStats，参照 BURNING）
    3) Potion.txt         — SKILLBOOST_NRT_*（type Potion + using _SkillBoost，参照 SKILLBOOST_Karma）
    4) Weapon.txt         — Damage_NRT_Amaterasu（DoT 每回合伤害条目，参照 Damage_Burning —— 注意在 Weapon.txt 不在 Data.txt）"""
    statuses_dir = OUT / "DOS2" / "Public" / "NarutoJutsu" / "Stats" / "Generated" / "Data"
    statuses_dir.mkdir(parents=True, exist_ok=True)

    consume_entries, damage_entries, potion_entries, weapon_entries = [], [], [], []
    loca_status = []

    for s in data["statuses"]:
        sid = s["id"]
        stype = s["statusType"]
        # 本地化（同技能机制：ref=英文文本，loca 键 = h<md5(英文文本)>，双语言同键）
        loca_status += [(fmt_handle(s["nameEn"]), 1, s["nameEn"], s["nameCn"]),
                        (fmt_handle(s["descriptionEn"]), 1, s["descriptionEn"], s["descriptionCn"])]
        common = [f'new entry "{sid}"', 'type "StatusData"', f'data "StatusType" "{stype}"',
                  'data "ForGameMaster" "Yes"', 'data "InitiateCombat" "Yes"',
                  f'data "DisplayName" "{sid}_DisplayName"',
                  f'data "DisplayNameRef" "|{s["nameEn"]}|"',
                  f'data "Description" "{sid}_Description"',
                  f'data "DescriptionRef" "|{s["descriptionEn"]}|"',
                  f'data "Icon" "{s["icon"]}"',
                  f'data "FormatColor" "{s["formatColor"]}"',
                  f'data "StackId" "{s["stackId"]}"']
        if "statsId" in s:
            common.append(f'data "StatsId" "{s["statsId"]}"')
            boost = s["boost"]
            potion_entries.append(
                "\n".join([
                    f'new entry "{s["statsId"]}"', 'type "Potion"', 'using "_SkillBoost"',
                    f'data "StackId" "{s["statsId"]}"',
                    f'data "CriticalChance" "{boost.get("criticalChance", 0)}"',
                    f'data "DodgeBoost" "{boost.get("dodgeBoost", 0)}"',
                    f'data "Duration" "{boost["duration"]}"',
                    f'data "StatusIcon" "{boost["statusIcon"]}"']))
        if "damageStats" in s:
            # 参照 BURNING 的 OnTurn DoT 字段集
            common += [f'data "DamageEvent" "{s["damageEvent"]}"',
                       f'data "DamageStats" "{s["damageStats"]}"',
                       f'data "DeathType" "{s["deathType"]}"',
                       'data "DamageCharacters" "Yes"', 'data "DamageItems" "No"',
                       'data "DamageTorches" "No"', 'data "SpawnBlood" "No"']
        if stype == "CONSUME":
            consume_entries.append("\n".join(common))
        elif stype == "DAMAGE":
            damage_entries.append("\n".join(common))

    for de in data.get("damageEntries", []):
        # 参照 Damage_Burning（Weapon.txt）：DoT 状态通过 DamageStats 引用此条目
        weapon_entries.append(
            "\n".join([
                f'new entry "{de["id"]}"', f'type "{de["type"]}"',
                f'data "ModifierType" "{de.get("modifierType", "Item")}"',
                f'data "Damage Type" "{de["damageType"]}"',
                f'data "Damage" "{de["damage"]}"',
                f'data "Damage Range" "{de["damageRange"]}"',
                f'data "DamageFromBase" "{de["damageFromBase"]}"',
                'data "Charges" "0"']))

    written = []
    if consume_entries:
        f = statuses_dir / "Status_CONSUME.txt"
        f.write_text("\n\n".join(consume_entries) + "\n", encoding="utf-8")
        written.append(f)
    if damage_entries:
        f = statuses_dir / "Status_DAMAGE.txt"
        f.write_text("\n\n".join(damage_entries) + "\n", encoding="utf-8")
        written.append(f)
    if potion_entries:
        f = statuses_dir / "Potion.txt"
        f.write_text("\n\n".join(potion_entries) + "\n", encoding="utf-8")
        written.append(f)
    if weapon_entries:
        f = statuses_dir / "Weapon.txt"
        f.write_text("\n\n".join(weapon_entries) + "\n", encoding="utf-8")
        written.append(f)
    return written, loca_status

# ---------- DOS2 TranslatedStringKeys（Stats.lsb，本地化缺失环节！）----------

def gen_stats_lsx_files(data):
    """生成 Stats/<Type>_<Field>.lsx（build 时转 .lsb），照抄 vanilla 结构：
    Public/<Folder>/Localization/Stats/Projectile_DisplayName.lsb 等。

    机制（2026-08-18 实证闭环，vanilla Projectile_Fireball）：
      stats 条目 DisplayName="<UUID>" → 游戏查 Stats.lsb 的 UUID → 拿 handle
      → 语言 loca（english.xml/chinese.xml）按 handle（contentuid）查当前语言文本。
    没有 Stats.lsb，游戏拿 DisplayName 值查不到任何映射 → 显示原始键（五包实测均失败）。

    条目格式（对照 vanilla Projectile_DisplayName.lsb）：
      <node id="TranslatedStringKey">
        <attribute id="Content" type="28" handle="h<md5(英文文本)>" value="|<英文文本>|" />
        <attribute id="ExtraData" type="23" value="" />
        <attribute id="Speaker" type="22" value="" />
        <attribute id="Stub" type="19" value="True" />
        <attribute id="UUID" type="22" value="<DisplayName字段值>" />
      </node>
    handle 为自造 h<md5(英文文本)>（游戏只做 UUID→handle→loca 映射，不校验算法）。"""
    loc_dir = OUT / "DOS2" / "Public" / "NarutoJutsu" / "Localization" / "Stats"
    loc_dir.mkdir(parents=True, exist_ok=True)
    # 清旧文件
    for old in loc_dir.glob("*.lsx"):
        old.unlink()

    files = {}  # (Type, Field) -> [entry...]
    for j in data["jutsus"]:
        shape = j["dos2"]["shape"]
        for field, text in (("DisplayName", j["nameEn"]), ("Description", j["descriptionEn"])):
            files.setdefault((shape, field), []).append(
                (f"NRT_{j['id']}_{field}", fmt_handle(text), f"|{text}|"))
    for s in data["statuses"]:
        for field, text in (("DisplayName", s["nameEn"]), ("Description", s["descriptionEn"])):
            # UUID 必须与状态条目 DisplayName/Description 字段值完全一致（含 _DisplayName/_Description 后缀）
            files.setdefault((f"Status_{s['statusType']}", field), []).append(
                (f"{s['id']}_{field}", fmt_handle(text), f"|{text}|"))

    # 2026-08-18 实证迭代：游戏查文本【只走游戏级 loca】（Data/Localization），mod 语言 xml 不被查。
    # Stats.lsb 的 value 是唯一能直达显示文本的通道：
    #   竖线 value="|Fireball|" = 引用（去游戏级 loca 查，查不到则回退竖线内文本——英文场景就是这么显示的）
    #   无竖线 value="Fireball Scroll" = 直接显示（vanilla SCROLL_Fireball 实证）
    # 因此 value 直接填【中文纯文本】：游戏显示 value 即中文（英文模式也中文，个人 mod 取舍）。
    cn_by_text = {j["nameEn"]: j["nameCn"] for j in data["jutsus"]}
    cn_by_text.update({j["descriptionEn"]: j["descriptionCn"] for j in data["jutsus"]})
    cn_by_text.update({s["nameEn"]: s["nameCn"] for s in data["statuses"]})
    cn_by_text.update({s["descriptionEn"]: s["descriptionCn"] for s in data["statuses"]})
    files = {k: [(uuid, handle, cn_by_text.get(text.strip("|"), text))
                 for uuid, handle, text in entries]
             for k, entries in files.items()}

    written = []
    for (stype, field), entries in sorted(files.items()):
        lines = ['<?xml version="1.0" encoding="utf-8"?>', "<save>",
                 '<version major="3" minor="6" revision="6" build="0" lslib_meta="v1,bswap_guids" />',
                 '<region id="TranslatedStringKeys">', '\t<node id="root">', '\t\t<children>']
        for uuid, handle, content in entries:
            lines += [
                '\t\t\t<node id="TranslatedStringKey">',
                f'\t\t\t\t<attribute id="Content" type="28" handle="{handle}" value="{content}" />',
                '\t\t\t\t<attribute id="ExtraData" type="23" value="" />',
                '\t\t\t\t<attribute id="Speaker" type="22" value="" />',
                '\t\t\t\t<attribute id="Stub" type="19" value="True" />',
                f'\t\t\t\t<attribute id="UUID" type="22" value="{uuid}" />',
                '\t\t\t</node>']
        lines += ['\t\t</children>', '\t</node>', '</region>', '</save>', '']
        f = loc_dir / f"{stype}_{field}.lsx"
        f.write_text("\n".join(lines), encoding="utf-8")
        written.append(f)
    return written

# ---------- DOS2 组装 ----------

def gen_language_lsx(lang: str) -> str:
    """语言文件夹注册表（对照 vanilla English.pak/Chinese.pak 内 language.lsx 原格式）。
    没有它，游戏不识别 Localization/Chinese/ 为非英语言文件夹（English 是 mod 硬编码默认语言）。
    实测：v0.2.0 首次发中文包时缺此文件，游戏显示原始键 NRT_*_DisplayName。"""
    return f'''<?xml version="1.0" encoding="UTF-8" ?>
<save>
    <header version="2" time="1367571612" />
    <version major="1" minor="3" revision="0" build="0" />
    <region id="Config">
        <node id="root">
            <children>
                <node id="ConfigEntry">
                    <attribute id="MapKey" value="Language" type="22" />
                    <attribute id="Type" value="1" type="5" />
                    <attribute id="Value" value="{lang}" type="20" />
                </node>
            </children>
        </node>
    </region>
</save>
'''

def gen_dos2():
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    stats_dir = OUT / "DOS2" / "Public" / "NarutoJutsu" / "Stats" / "Generated" / "Data"
    stats_dir.mkdir(parents=True, exist_ok=True)

    # 按形态分发到官方文件名（vanilla 多模组先例：同名文件共存按条目合并；
    # 自定义文件名实测不被游戏加载——2026-08-17 GM 模式搜索不到）
    shape_files = {}
    loca_entries = []  # (handle, version, enText, cnText) —— handle = h<md5(英文文本)>
    ids = set()
    for j in data["jutsus"]:
        assert j["id"] not in ids, f"重复 id: {j['id']}"
        ids.add(j["id"])
        shape = j["dos2"]["shape"]
        aid = f"NRT_{j['id']}"
        shape_files.setdefault(shape, []).append(gen_dos2_entry(j, shape))
        loca_entries.append((fmt_handle(j["nameEn"]), 1, j["nameEn"], j["nameCn"]))
        loca_entries.append((fmt_handle(j["descriptionEn"]), 1, j["descriptionEn"], j["descriptionCn"]))
    # 清理旧命名文件（如果存在）
    for old in stats_dir.glob("Skill_*.txt"):
        if old.name not in {f"Skill_{s}.txt" for s in shape_files}:
            old.unlink()
    written = []
    for shape, entries in shape_files.items():
        fname = f"Skill_{shape}.txt"
        (stats_dir / fname).write_text("\n\n".join(entries) + "\n", encoding="utf-8")
        written.append(stats_dir / fname)

    # 自定义状态 + SKILLBOOST 增益 + DoT 伤害条目
    status_files, loca_status = gen_dos2_statuses(data)
    written += status_files
    loca_entries += loca_status

    # 双语言本地化（2026-08-18 实证：DOS2 游戏【只读 mod 的 English loca 文件夹】——
    # 中文模式下也读它（先读 English/english.xml），chinese.xml 实测不被读（中文字段显示英文）。
    # 因此 english.xml 内容用【中文文本】（键/handle 不变），chinese.xml 保留同内容双保险；
    # 英文模式会显示中文——个人 mod 可接受，README 已注明。
    en_dir = OUT / "DOS2" / "Localization" / "English"
    cn_dir = OUT / "DOS2" / "Localization" / "Chinese"
    en_dir.mkdir(parents=True, exist_ok=True)
    cn_dir.mkdir(parents=True, exist_ok=True)
    # 键 = h<md5(英文文本)>（Stats.lsb 的 handle 一致），文本 = 中文
    en_xml = loca_xml([(uid, ver, cn) for uid, ver, _, cn in loca_entries], with_version=False)
    cn_xml = loca_xml([(uid, ver, cn) for uid, ver, _, cn in loca_entries], with_version=False)
    (en_dir / "english.xml").write_text(en_xml, encoding="utf-8")
    (cn_dir / "chinese.xml").write_text(cn_xml, encoding="utf-8")
    # 语言文件夹注册表（必配，见 gen_language_lsx 说明）
    (en_dir / "language.lsx").write_text(gen_language_lsx("English"), encoding="utf-8")
    (cn_dir / "language.lsx").write_text(gen_language_lsx("Chinese"), encoding="utf-8")

    # 断言：双语言键集合相等 + 每个技能 ref 的文本都存在于 XML（按键查找）
    assert xml_keys(en_xml) == xml_keys(cn_xml), "双语言本地化键集合不一致！"
    for j in data["jutsus"]:
        for text in (j["nameEn"], j["descriptionEn"]):
            assert fmt_handle(text) in xml_keys(en_xml), f"本地化缺少键 h<md5({text})>"
    for s in data["statuses"]:
        for text in (s["nameEn"], s["descriptionEn"]):
            assert fmt_handle(text) in xml_keys(en_xml), f"状态本地化缺少键 h<md5({text})>"
    return written, en_dir / "english.xml", cn_dir / "chinese.xml"

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
    stats_dir = OUT / "BG3" / "Public" / "NarutoJutsu" / "Stats" / "Generated" / "Data"
    # BG3 本地化：pak 根 Localization/English/english.xml + .loca 二进制（BG3 游戏内为 .loca）
    loca_dir = OUT / "BG3" / "Localization" / "English"
    stats_dir.mkdir(parents=True, exist_ok=True)
    loca_dir.mkdir(parents=True, exist_ok=True)

    # 按形态分发到官方文件名（同 DOS2 理由）；无 bg3 段的术（DOS2 专用）跳过
    shape_files = {}
    loca_entries = []
    for j in data["jutsus"]:
        if "bg3" not in j:
            continue
        shape = j["bg3"]["shape"]
        entry, disp, desc = gen_bg3_entry(j, shape)
        shape_files.setdefault(shape, []).append(entry)
        loca_entries.extend([disp, desc])
    for old in stats_dir.glob("Spell_*.txt"):
        if old.name not in {f"Spell_{s}.txt" for s in shape_files}:
            old.unlink()
    written = []
    for shape, entries in shape_files.items():
        fname = f"Spell_{shape}.txt"
        (stats_dir / fname).write_text("\n\n".join(entries) + "\n", encoding="utf-8")
        written.append(stats_dir / fname)
    (loca_dir / "english.xml").write_text(loca_xml(loca_entries), encoding="utf-8")
    return written, loca_dir / "english.xml"

# ---------- meta.lsx（两游戏格式不同，均已对照游戏本体 pak 内 meta.lsx 实测）----------

DOS2_MOD_UUID = "5d2e3f1a-8c4b-4e6d-9f0a-2b3c4d5e6f70"  # 随机生成，固定
BG3_MOD_UUID = "7a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"  # 随机生成，固定

def gen_meta_lsx(game: str) -> str:
    """pak 内路径必须为 Mods/<Folder>/meta.lsx（两游戏一致）"""
    if game == "dos2de":
        # 对照 DefEd/Data/Shared.pak 内 Mods/Shared/meta.lsx（version 3.6）+ myFirstMod 工程格式
        return '''<?xml version="1.0" encoding="UTF-8" ?>
<save>
    <header version="2" />
    <version major="3" minor="6" revision="0" build="3" />
    <region id="Config">
        <node id="root">
            <children>
                <node id="Dependencies">
                    <children>
                        <node id="ModuleShortDesc">
                            <attribute id="Folder" value="DivinityOrigins_1301db3d-1f54-4e98-9be5-5094030916e4" type="30" />
                            <attribute id="MD5" value="73d13f95607b70c953cc32e56d62b7d7" type="23" />
                            <attribute id="Name" value="Divinity: Original Sin 2" type="22" />
                            <attribute id="UUID" value="1301db3d-1f54-4e98-9be5-5094030916e4" type="22" />
                            <attribute id="Version" value="373234071" type="4" />
                        </node>
                    </children>
                </node>
                <node id="ModuleInfo">
                    <attribute id="Author" value="LarianModLearn" type="30" />
                    <attribute id="CharacterCreationLevelName" value="" type="22" />
                    <attribute id="Description" value="" type="30" />
                    <attribute id="Folder" value="NarutoJutsu" type="30" />
                    <attribute id="GMTemplate" value="" type="22" />
                    <attribute id="LobbyLevelName" value="" type="22" />
                    <attribute id="MD5" value="" type="23" />
                    <attribute id="MenuLevelName" value="" type="22" />
                    <attribute id="Name" value="NarutoJutsu" type="22" />
                    <attribute id="NumPlayers" value="2" type="1" />
                    <attribute id="PhotoBooth" value="" type="22" />
                    <attribute id="StartupLevelName" value="" type="22" />
                    <attribute id="Tags" value="" type="30" />
                    <attribute id="Type" value="Add-on" type="22" />
                    <attribute id="UUID" value="''' + DOS2_MOD_UUID + '''" type="22" />
                    <attribute id="Version" value="268435456" type="4" />
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version" value="909321303" type="4" />
                        </node>
                        <node id="Scripts" />
                        <node id="TargetModes">
                            <children>
                                <node id="Target">
                                    <attribute id="Object" value="Story" type="22" />
                                </node>
                                <node id="Target">
                                    <attribute id="Object" value="GM" type="22" />
                                </node>
                            </children>
                        </node>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
'''
    # BG3：对照 Shared.pak 内 Mods/Shared/meta.lsx（version 4.8；Version64 为 int64 字段）
    return '''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="8" revision="0" build="500"/>
    <region id="Config">
        <node id="root">
            <children>
                <node id="Conflicts"/>
                <node id="Dependencies"/>
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="LarianModLearn"/>
                    <attribute id="CharacterCreationLevelName" type="FixedString" value=""/>
                    <attribute id="Description" type="LSString" value=""/>
                    <attribute id="FileSize" type="uint64" value="0"/>
                    <attribute id="Folder" type="LSString" value="NarutoJutsu"/>
                    <attribute id="LobbyLevelName" type="FixedString" value=""/>
                    <attribute id="MD5" type="LSString" value=""/>
                    <attribute id="MenuLevelName" type="FixedString" value=""/>
                    <attribute id="Name" type="LSString" value="NarutoJutsu"/>
                    <attribute id="NumPlayers" type="uint8" value="4"/>
                    <attribute id="PhotoBooth" type="FixedString" value=""/>
                    <attribute id="PublishHandle" type="uint64" value="0"/>
                    <attribute id="StartupLevelName" type="FixedString" value=""/>
                    <attribute id="UUID" type="FixedString" value="''' + BG3_MOD_UUID + '''"/>
                    <attribute id="Version64" type="int64" value="36028797018963968"/>
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="36028797018963968"/>
                        </node>
                        <node id="Scripts"/>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
'''

def gen_build_script(dos2_stats, dos2_loca, bg3_stats, bg3_loca, stats_lsx_files):
    divine = str(ROOT / "tools" / "ExportTool-v1.20.4" / "Packed" / "Tools" / "Divine.exe").replace("/", "\\")
    dos2_root = OUT / "DOS2"
    bg3_root = OUT / "BG3"
    lines = [
        "# 忍术原型打包脚本（在项目根目录运行：powershell -File mods/NarutoJutsu/build.ps1）",
        "$divine = '%s'" % divine,
        "# 0) TranslatedStringKeys .lsx -> .lsb（Stats.lsb 是 mod 本地化映射表，缺它技能名显示原始键）",
    ]
    for lsx in stats_lsx_files:
        lines.append(
            f'& $divine -g dos2de --action convert-resource -s "{lsx}" -d "{lsx.with_suffix(".lsb")}"')
    lines += [
        "# 1) BG3 本地化 XML -> .loca（DOS2 直接发布 XML，游戏原生格式）",
        f'& $divine -g bg3 --action convert-loca -s "{bg3_loca}" -d "{bg3_loca.with_suffix(".loca")}"',
        "# 2) 打包（-s 传含 meta.lsx 的目录；DOS2 双语言 Localization/English + Localization/Chinese 一并入包）",
        f'& $divine -g dos2de --action create-package -s "{dos2_root}" -d "{dos2_root}.pak"',
        f'& $divine -g bg3 --action create-package -s "{bg3_root}" -d "{bg3_root}.pak"',
        "# 3) 安装：复制 .pak 到 Mods 目录",
        '#   BG3:  %LocalAppData%\\Larian Studios\\Baldur\'s Gate 3\\Mods\\',
        '#   DOS2: %USERPROFILE%\\Documents\\Larian Studios\\Divinity Original Sin 2 Definitive Edition\\Mods\\（DOS2 用 Documents，不是 LocalAppData）',
    ]
    return "\n".join(lines) + "\n"

def main():
    dos2_files, dos2_loca, dos2_loca_cn = gen_dos2()
    stats_lsx_files = gen_stats_lsx_files(json.loads(SPEC.read_text(encoding="utf-8")))
    bg3_stats, bg3_loca = gen_bg3()
    # meta.lsx：pak 内路径必须为 Mods/<Folder>/meta.lsx（两游戏一致，对照游戏本体实测）
    dos2_meta = OUT / "DOS2" / "Mods" / "NarutoJutsu" / "meta.lsx"
    bg3_meta = OUT / "BG3" / "Mods" / "NarutoJutsu" / "meta.lsx"
    dos2_meta.parent.mkdir(parents=True, exist_ok=True)
    bg3_meta.parent.mkdir(parents=True, exist_ok=True)
    dos2_meta.write_text(gen_meta_lsx("dos2de"), encoding="utf-8")
    bg3_meta.write_text(gen_meta_lsx("bg3"), encoding="utf-8")
    (OUT / "build.ps1").write_text(
        gen_build_script(dos2_files, dos2_loca, bg3_stats, bg3_loca, stats_lsx_files), encoding="utf-8")
    print(f"[OK] DOS2 stats/status: {len(dos2_files)} 个文件（Skill_*/Status_*/Potion/Weapon）")
    for f in dos2_files:
        print(f"     {f.relative_to(OUT)}")
    print(f"[OK] TranslatedStringKeys lsx: {len(stats_lsx_files)} 个（build 时转 .lsb）")
    print(f"[OK] DOS2 loca: {dos2_loca.relative_to(OUT)} + {dos2_loca_cn.relative_to(OUT)}（键集合断言通过）")
    print(f"[OK] BG3: {bg3_stats}")
    print(f"[OK] BG3 loca: {bg3_loca}")
    print(f"[OK] DOS2 meta: {dos2_meta}")
    print(f"[OK] BG3 meta: {bg3_meta}")
    print("[OK] build.ps1 已生成（含 Stats.lsb 转换 + loca 转换 + 打包命令）")

if __name__ == "__main__":
    main()

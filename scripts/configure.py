#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfiguration für Quarto-Kurswebsite anwenden.

- Standard: non-interactive (keine Rückfragen; bricht bei fehlenden Pflichtwerten ab)
- Flags:
    --interactive / -i     → fehlende Werte abfragen
    --noninteractive / -n  → keine Rückfragen (Default)
    --config PATH          → Pfad zu site-config.yaml (optional)

Beispiele:
  python3 scripts/configure.py --interactive
  python3 scripts/configure.py --noninteractive
  python3 scripts/configure.py --noninteractive --config ./site-config.yaml
"""

from pathlib import Path
import argparse, os, sys, re

# ---------- CLI ----------
p = argparse.ArgumentParser(description="Apply site-config.yaml to project files.")
m = p.add_mutually_exclusive_group()
m.add_argument("-i","--interactive", action="store_true", help="Ask for missing values.")
m.add_argument("-n","--noninteractive", action="store_true", help="No prompts; fail if required are missing.")
p.add_argument("-c","--config", default=None, help="Path to site-config.yaml")
args = p.parse_args()
NONINTERACTIVE = True if args.noninteractive or not args.interactive else False  # default non-interactive

# ---------- locate project root/base ----------
ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "_quarto.yml").exists():
    BASE = ROOT
elif (ROOT / "template" / "_quarto.yml").exists():
    BASE = ROOT / "template"
else:
    print("❌ _quarto.yml not found (root or ./template).")
    sys.exit(1)

# ---------- config path ----------
CFG_ROOT = ROOT / "site-config.yaml"
CFG_ALT  = BASE / "site-config.yaml"
CFG_PATH = Path(args.config) if args.config else (CFG_ROOT if CFG_ROOT.exists() else (CFG_ALT if CFG_ALT.exists() else CFG_ROOT))

# ---------- YAML load/save (PyYAML if available, else naive) ----------
def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        data = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or ":" not in s:
                continue
            key, val = s.split(":", 1)
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            data[key] = val
        return data

def dump_yaml(path: Path, data: dict) -> None:
    try:
        import yaml  # type: ignore
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception:
        lines=[]
        for k,v in data.items():
            v = "" if v is None else str(v)
            if any(c in v for c in [":","#"]) or v == "" or " " in v:
                v = f'"{v}"'
            lines.append(f"{k}: {v}")
        path.write_text("\n".join(lines)+"\n", encoding="utf-8")

# ---------- schema (key, label, default, required) ----------
SCHEMA = [
    ("site_title","Website-Titel","your title", True),
    ("org_name","Organisation (Footer)","your organisation", True),
    ("site_url","Site-URL","https://your-github-name.github.io/your-repo", True),
    ("repo_url","Repo-URL","https://github.com/your-github-name/your-repo", True),
    ("logo_path","Logo-Pfad","images/your-logo.png", False),
    ("portal_text","Navbar rechts: Link-Text","Interne Lernplattform", False),
    ("portal_url","Navbar rechts: URL","https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de", False),
    ("impressum_href","Footer: Impressum-Link","#", False),
    ("brand_hex","Markenfarbe Light (HEX)","#FB7171", True),
    ("brand_hex_dark","Markenfarbe Dark (HEX, leer = wie Light)","", False),
    ("brand_font","Primär-Schriftfamilie (CSS)","system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif", False),
    ("dark_theme","Dark-Theme aktivieren? (yes/no)","yes", False),
    # Impressum
    ("responsible_name","Verantwortliche Person","", False),
    ("responsible_address","Verantwortliche Adresse (HTML mit <br />)","<br />", False),
    ("responsible_email","E-Mail-Adresse","", False),
    ("uni_name","Universität","", False),
    ("uni_url","Universitäts-URL","", False),
    ("institute_name","Institut","", False),
    ("institute_url","Institut-URL","", False),
    ("chair_name","Lehrstuhl/AG","", False),
    ("chair_url","Lehrstuhl/AG-URL","", False),
    ("imprint_url","URL offizielles Uni-Impressum","", False),
    # QMD-Platzhalter
    ("course_code","Kurs-Kürzel","", False),
    ("contact_email","Kontakt E-Mail","", False),
]

def ask(label, default):
    try:
        v = input(f"{label} [{default}]: ").strip()
        return v if v else default
    except EOFError:
        return default

def prompt_missing(cfg: dict) -> dict:
    changed=False
    for key,label,default,required in SCHEMA:
        cur = str(cfg.get(key,"") or "").strip()
        if cur:
            continue
        if NONINTERACTIVE:
            if required:
                print(f"❌ Missing required value: {key}")
                sys.exit(1)
            else:
                continue
        cfg[key] = ask(label, default)
        changed=True
    return cfg, changed

# ---------- helpers for robust file edits ----------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def replace_entire_line(text: str, key: str, value: str) -> str:
    """
    Ersetzt die gesamte YAML-Zeile 'key: ...' durch 'key: value' (idempotent).
    Beispiel: key='href' -> '  href: https://...'
    Achtung: ersetzt alle Zeilen mit exakt diesem key.
    """
    pattern = re.compile(rf'^(\s*{re.escape(key)}:\s*).*$',
                         flags=re.M)
    if pattern.search(text):
        text = pattern.sub(rf'\1{value}', text)
    return text

def simple_replace(text: str, pairs: dict) -> str:
    for old, new in pairs.items():
        text = text.replace(old, new)
    return text

def set_light_brand_line(text: str) -> str:
    """
    Macht aus 'light: lumen' (oder 'light: [lumen]') die gebrandete Zeile
    '      light: [lumen, css/custom.scss]'. Idempotent.
    """
    pat = re.compile(r'(^\s*light:\s*(?:\[\s*)?lumen(?:\s*\])?\s*$)', flags=re.M)
    if "custom.scss" in text:
        return text  # schon gebrandet
    if pat.search(text):
        text = pat.sub('      light: [lumen, css/custom.scss]', text, count=1)
    return text

def set_dark_line(text: str, dark_line: str) -> str:
    # 1) Platzhalter ersetzen (beide Varianten sicher)
    if "__DARK_THEME_LINE__" in text or "# __DARK_THEME_LINE__" in text:
        text = text.replace("__DARK_THEME_LINE__", dark_line)
        text = text.replace("# __DARK_THEME_LINE__", dark_line)
        return text
    # 2) vorhandene dark-Zeile (kommentiert oder nicht) ersetzen
    pat = re.compile(r'^\s*#?\s*dark:\s*\[.*theme-dark.*\].*$', flags=re.M)
    if pat.search(text):
        text = pat.sub(dark_line, text)
        return text
    # 3) Fallback: nach 'light:' suchen und Zeile darunter einfügen
    m = re.search(r'(^\s*light:\s*\[.*\]\s*$)', text, flags=re.M)
    if m:
        insert_pos = m.end(1)
        text = text[:insert_pos] + "\n" + dark_line + text[insert_pos:]
    return text

# ---------- updates ----------
def update_quarto_yaml(base: Path, v: dict):
    yml_path = base / "_quarto.yml"
    if not yml_path.exists():
        return
    yml = read_text(yml_path)

    # 1) Light-Theme: aus 'light: lumen' → gebrandeter Stack
    yml = set_light_brand_line(yml)

    # 2) Dark-Theme-Zeile (Platzhalter + idempotente Ersetzung)
    dark_line = (
        '      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
        if str(v.get("dark_theme", "yes")).lower() == "yes"
        else '      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
    )
    yml = set_dark_line(yml, dark_line)

    # 3) Idempotente Zeilenersetzungen
    yml = replace_entire_line(yml, "title", f'"{v["site_title"]}"')
    yml = replace_entire_line(yml, "site-url", v["site_url"])
    yml = replace_entire_line(yml, "repo-url", v["repo_url"])
    yml = replace_entire_line(yml, "logo", v["logo_path"])
    yml = replace_entire_line(yml, "text", v["portal_text"])
    yml = replace_entire_line(yml, "href", v["portal_url"])

    # 4) Footer: Org-Name + Impressum-Link robust
    yml = simple_replace(yml, {
        'your organisation (<span class="year"></span>) —':
            f'{v["org_name"]} (<span class="year"></span>) —',
    })
    href_cfg = (v.get("impressum_href", "#") or "#").strip()
    href_cfg = re.sub(r'\.(qmd|md)$', '.html', href_cfg, flags=re.I)  # .qmd/.md → .html für Footer-HTML
    yml_new = re.sub(
        r'(<a[^>]*class="impressum-link"[^>]*href=")[^"]*(")',
        rf'\1{href_cfg}\2',
        yml,
        flags=re.I
    )
    if yml_new == yml:
        yml_new = yml.replace(
            '(<span class="year"></span>) —',
            f'(<span class="year"></span>) —\n      '
            f'<a class="impressum-link" href="{href_cfg}">Impressum</a>'
        )
    yml = yml_new

    write_text(yml_path, yml)

def update_scss(base: Path, v: dict):
    css = base / "css" / "custom.scss"
    if css.exists():
        t = read_text(css)
        t = simple_replace(t, {
            '$brand: #FB7171;': f'$brand: {v["brand_hex"]};',
            '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
                f'$brand-font: {v["brand_font"]};',
        })
        write_text(css, t)

    tdark = base / "css" / "theme-dark.scss"
    if tdark.exists():
        t = read_text(tdark)
        brand_dark = v["brand_hex_dark"] if v.get("brand_hex_dark") else v["brand_hex"]
        t = simple_replace(t, {
            '$brand: #FB7171;': f'$brand: {brand_dark};',
            '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
                f'$brand-font: {v["brand_font"]};',
        })
        write_text(tdark, t)

def update_impressum(base: Path, v: dict):
    imp = base / "base" / "impressum.qmd"
    if not imp.exists():
        return
    t = read_text(imp)
    for k in ["responsible_name","responsible_address","responsible_email","imprint_url",
              "uni_name","uni_url","institute_name","institute_url","chair_name","chair_url"]:
        t = t.replace(f"{{{{{k}}}}}", str(v.get(k,"")))
    write_text(imp, t)

def update_qmd_placeholders(base: Path, v: dict):
    keys = ["site_title","org_name","course_code","contact_email"]
    repl = {f"{{{{{k}}}}}": str(v.get(k,"")) for k in keys}
    for path in base.rglob("*.qmd"):
        t = read_text(path); orig = t
        for old,new in repl.items():
            t = t.replace(old, new)
        if t != orig:
            write_text(path, t)

def main():
    # 1) Konfig laden / fehlende ggf. abfragen
    cfg = load_yaml(CFG_PATH)
    cfg, changed = prompt_missing(cfg)

    # normalize to string
    for k,_,_,_ in SCHEMA:
        cfg[k] = str(cfg.get(k,"") or "")

    if changed or not CFG_PATH.exists():
        dump_yaml(CFG_PATH, cfg)
        print(f"📝 saved config -> {CFG_PATH}")

    # 2) Updates anwenden
    update_quarto_yaml(BASE, cfg)
    update_scss(BASE, cfg)
    update_impressum(BASE, cfg)
    update_qmd_placeholders(BASE, cfg)

    # 3) .nojekyll optional
    docs = ROOT / "docs"
    if docs.exists():
        (docs / ".nojekyll").write_text("", encoding="utf-8")

    print("✅ configuration applied. Commit & push to build on CI.")

if __name__=="__main__":
    main()

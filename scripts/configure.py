#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/configure.py
Liest site-config.yaml, fragt nur fehlende Werte ab, schreibt zurück
und ersetzt die Platzhalter in den Projektdateien.

Aufruf:
  python3 scripts/configure.py
Optionen:
  NONINTERACTIVE=1  -> keine Abfragen; bricht ab, wenn Felder fehlen
"""

from pathlib import Path
import os
import sys

# ----------------- Pfade erkennen (Root oder ./template) -----------------
ROOT = Path(__file__).resolve().parents[1]
if (ROOT / "_quarto.yml").exists():
    BASE = ROOT
elif (ROOT / "template" / "_quarto.yml").exists():
    BASE = ROOT / "template"
else:
    print("❌ _quarto.yml nicht gefunden – weder im Projekt-Root noch in ./template/")
    sys.exit(1)

# Konfig-Datei: bevorzugt im Projekt-Root
CFG_ROOT = ROOT / "site-config.yaml"
CFG_ALT  = BASE / "site-config.yaml"
CFG_PATH = CFG_ROOT if CFG_ROOT.exists() else (CFG_ALT if CFG_ALT.exists() else CFG_ROOT)

# ----------------- Mini-YAML Loader (fallback ohne PyYAML) -----------------
def load_yaml(path: Path) -> dict:
    data = {}
    if not path.exists():
        return data
    try:
        import yaml  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        # Fallback: sehr einfache key: value Paare (eine Zeile)
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            data[key] = val
        return data

def dump_yaml(path: Path, data: dict) -> None:
    try:
        import yaml  # type: ignore
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    except Exception:
        # Fallback: naive Ausgabe (verliert Kommentare)
        lines = []
        for k, v in data.items():
            if v is None:
                v = ""
            if isinstance(v, str) and (":" in v or "#" in v or v.strip() == "" or " " in v):
                v_out = f'"{v}"'
            else:
                v_out = str(v)
            lines.append(f"{k}: {v_out}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

# ----------------- Schema (Prompts nur für leere Felder) -----------------
SCHEMA = [
    ("site_title",       'Website-Titel',                         "your title", True),
    ("org_name",         'Organisation (Footer)',                 "your organisation", True),
    ("site_url",         'Site-URL',                              "https://your-github-name.github.io/your-repo", True),
    ("repo_url",         'Repo-URL',                              "https://github.com/your-github-name/your-repo", True),
    ("logo_path",        'Logo-Pfad',                             "images/your-logo.png", False),
    ("portal_text",      'Navbar rechts: Link-Text',              "Interne Lernplattform", False),
    ("portal_url",       'Navbar rechts: URL',                    "https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de", False),
    ("impressum_href",   'Footer: Impressum-Link (href)',         "#", False),
    ("brand_hex",        'Markenfarbe Light (HEX)',               "#FB7171", True),
    ("brand_hex_dark",   'Markenfarbe Dark (HEX, leer = wie Light)', "", False),
    ("brand_font",       'Primär-Schriftfamilie (CSS)',           "system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif", False),
    ("dark_theme",       'Dark-Theme aktivieren? (yes/no)',       "yes", False),
    ("responsible_name", 'Verantwortliche Person',                "", False),
    ("responsible_address", 'Verantwortliche Adresse (HTML mit <br />)', "<br />", False),
    ("responsible_email",'E-Mail-Adresse',                        "", False),
    ("uni_name",         'Universität',                           "", False),
    ("uni_url",          'Universitäts-URL',                      "", False),
    ("institute_name",   'Institut',                              "", False),
    ("institute_url",    'Institut-URL',                          "", False),
    ("chair_name",       'Lehrstuhl/AG',                          "", False),
    ("chair_url",        'Lehrstuhl/AG-URL',                      "", False),
    ("imprint_url",      'URL offizielles Uni-Impressum',         "", False),
]

NONINTERACTIVE = os.getenv("NONINTERACTIVE") == "1"

def prompt_missing(cfg: dict) -> dict:
    changed = False
    for key, label, default, required in SCHEMA:
        cur = cfg.get(key, "")
        if isinstance(cur, str):
            cur = cur.strip()
        if cur:
            continue
        if NONINTERACTIVE:
            if required:
                print(f"❌ Fehlender Pflichtwert: {key}")
                sys.exit(1)
            else:
                continue
        # Abfrage
        val = input(f"{label} [{default}]: ").strip() or default
        cfg[key] = val
        changed = True
    return cfg, changed

# ----------------- Datei-Ersetzungen -----------------
def replace_in_file(path: Path, replacements: dict) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in replacements.items():
        text = text.replace(old, new)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False

def update_quarto_yaml(base: Path, v: dict):
    repl = {
        'title: "your title"': f'title: "{v["site_title"]}"',
        'site-url: https://your-github-name.github.io/your-repo': f'site-url: {v["site_url"]}',
        'repo-url: https://github.com/your-github-name/your-repo': f'repo-url: {v["repo_url"]}',
        'logo: images/your-logo.png': f'logo: {v["logo_path"]}',
        'text: Interne Lernplattform': f'text: {v["portal_text"]}',
        'href: https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de': f'href: {v["portal_url"]}',
        'your organisation (<span class="year"></span>) —': f'{v["org_name"]} (<span class="year"></span>) —',
        '<a class="impressum-link" href="#">Impressum</a>': f'<a class="impressum-link" href="{v["impressum_href"]}">Impressum</a>',
    }
    # Dark-Theme Schalter
    repl['__DARK_THEME_LINE__'] = (
        '      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
        if str(v.get("dark_theme", "yes")).lower() == "yes"
        else '      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
    )
    replace_in_file(base / "_quarto.yml", repl)

def update_scss(base: Path, v: dict):
    replace_in_file(base / "css" / "custom.scss", {
        '$brand: #FB7171;': f'$brand: {v["brand_hex"]};',
        '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
            f'$brand-font: {v["brand_font"]};',
    })
    tdark = base / "css" / "theme-dark.scss"
    if tdark.exists():
        brand_dark = v["brand_hex_dark"] if v.get("brand_hex_dark") else v["brand_hex"]
        replace_in_file(tdark, {
            '$brand: #FB7171;': f'$brand: {brand_dark};',
            '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
                f'$brand-font: {v["brand_font"]};',
        })

def update_impressum(base: Path, v: dict):
    imp = base / "base" / "impressum.qmd"
    if not imp.exists():
        return
    text = imp.read_text(encoding="utf-8")
    # wenn moustache-Platzhalter vorhanden sind → ersetzen
    if "{{responsible_name}}" in text or "{{uni_name}}" in text:
        text = (text
            .replace("{{responsible_name}}", v.get("responsible_name",""))
            .replace("{{responsible_address}}", v.get("responsible_address",""))
            .replace("{{responsible_email}}", v.get("responsible_email",""))
            .replace("{{imprint_url}}", v.get("imprint_url",""))
            .replace("{{uni_name}}", v.get("uni_name",""))
            .replace("{{uni_url}}", v.get("uni_url",""))
            .replace("{{institute_name}}", v.get("institute_name",""))
            .replace("{{institute_url}}", v.get("institute_url",""))
            .replace("{{chair_name}}", v.get("chair_name",""))
            .replace("{{chair_url}}", v.get("chair_url",""))
        )
        imp.write_text(text, encoding="utf-8")

def main():
    # 1) Konfig laden / nachfragen / zurückschreiben
    cfg = load_yaml(CFG_PATH)
    cfg, changed = prompt_missing(cfg)
    # Sicherstellen: Strings
    for k, *_ in SCHEMA:
        cfg[k] = str(cfg.get(k, "") or "")
    if changed or not CFG_PATH.exists():
        dump_yaml(CFG_PATH, cfg)
        print(f"📝 Konfiguration gespeichert: {CFG_PATH.relative_to(ROOT)}")

    # 2) Ersetzungen anwenden
    update_quarto_yaml(BASE, cfg)
    update_scss(BASE, cfg)
    update_impressum(BASE, cfg)

    # 3) .nojekyll optional anlegen, falls docs/ schon existiert
    docs = ROOT / "docs"
    if docs.exists():
        (docs / ".nojekyll").write_text("", encoding="utf-8")

    print("✅ Konfiguration angewendet. Jetzt committen und pushen — der CI-Workflow rendert.")

if __name__ == "__main__":
    main()

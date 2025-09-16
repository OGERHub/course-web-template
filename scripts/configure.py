#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfiguration für Quarto-Kurswebsite anwenden.
- Standard: non-interactive (keine Rückfragen; bricht bei fehlenden Pflichtwerten ab)
- Flags:
    --interactive / -i     → fehlende Werte abfragen
    --noninteractive / -n  → keine Rückfragen (Default)
    --config PATH          → Pfad zu site-config.yaml (optional)

Beispiel:
  python3 scripts/configure.py --interactive
  python3 scripts/configure.py --noninteractive
  python3 scripts/configure.py --noninteractive --config ./site-config.yaml
"""

from pathlib import Path
import argparse, os, sys

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
    print("❌ _quarto.yml not found (root or ./template)."); sys.exit(1)

# ---------- config path ----------
CFG_ROOT = ROOT / "site-config.yaml"
CFG_ALT  = BASE / "site-config.yaml"
CFG_PATH = Path(args.config) if args.config else (CFG_ROOT if CFG_ROOT.exists() else (CFG_ALT if CFG_ALT.exists() else CFG_ROOT))

# ---------- YAML load/save (PyYAML if available, else naive) ----------
def load_yaml(path: Path) -> dict:
    if not path.exists(): return {}
    try:
        import yaml  # type: ignore
        with open(path,"r",encoding="utf-8") as f: return yaml.safe_load(f) or {}
    except Exception:
        data={}
        for line in path.read_text(encoding="utf-8").splitlines():
            s=line.strip()
            if not s or s.startswith("#") or ":" not in s: continue
            k,v=s.split(":",1); data[k.strip()] = v.strip().strip("'").strip('"')
        return data

def dump_yaml(path: Path, data: dict) -> None:
    try:
        import yaml  # type: ignore
        with open(path,"w",encoding="utf-8") as f: yaml.safe_dump(data,f,sort_keys=False,allow_unicode=True)
    except Exception:
        lines=[]
        for k,v in data.items():
            if v is None: v=""
            v=str(v)
            if any(c in v for c in [":","#"," "]) or v=="":
                v=f'"{v}"'
            lines.append(f"{k}: {v}")
        path.write_text("\n".join(lines)+"\n",encoding="utf-8")

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
        if cur: continue
        if NONINTERACTIVE:
            if required:
                print(f"❌ Missing required value: {key}")
                sys.exit(1)
            else:
                continue
        cfg[key] = ask(label, default)
        changed=True
    return cfg, changed

# ---------- replacements ----------
def replace_in_file(path: Path, replacements: dict) -> bool:
    if not path.exists(): return False
    txt = path.read_text(encoding="utf-8")
    orig = txt
    for old,new in replacements.items():
        txt = txt.replace(old, new)
    if txt != orig:
        path.write_text(txt, encoding="utf-8")
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
    repl['__DARK_THEME_LINE__'] = (
        '      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
        if str(v.get("dark_theme","yes")).lower()=="yes"
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
    if not imp.exists(): return
    t = imp.read_text(encoding="utf-8")
    for k in ["responsible_name","responsible_address","responsible_email","imprint_url",
              "uni_name","uni_url","institute_name","institute_url","chair_name","chair_url"]:
        t = t.replace(f"{{{{{k}}}}}", str(v.get(k,"")))
    imp.write_text(t, encoding="utf-8")

def main():
    cfg = load_yaml(CFG_PATH)
    cfg, changed = prompt_missing(cfg)
    # normalize to string
    for k,_,_,_ in SCHEMA: cfg[k] = str(cfg.get(k,"") or "")
    if changed or not CFG_PATH.exists():
        dump_yaml(CFG_PATH, cfg)
        print(f"📝 saved config -> {CFG_PATH}")

    update_quarto_yaml(BASE, cfg)
    update_scss(BASE, cfg)
    update_impressum(BASE, cfg)

    # optional: ensure .nojekyll if docs/ exists
    docs = ROOT / "docs"
    if docs.exists():
        (docs/".nojekyll").write_text("", encoding="utf-8")

    print("✅ configuration applied. Commit & push to build on CI.")

if __name__=="__main__":
    main()

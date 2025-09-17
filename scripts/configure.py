#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
configure.py — wendet site-config.yaml auf ein Quarto-Projekt an.

• Default: non-interactive (keine Rückfragen; bricht bei fehlenden Pflichtwerten ab)
• Flags:
    --interactive / -i       fehlende Werte abfragen
    --noninteractive / -n    keine Rückfragen (Default)
    --config PATH            Pfad zur site-config.yaml (optional)

Beispiele:
  python3 scripts/configure.py --interactive
  python3 scripts/configure.py --noninteractive --config ./site-config.yaml
"""

from pathlib import Path
from datetime import datetime
import argparse, sys, re
from urllib.parse import urlparse

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

# ---------- logging (einfach) ----------
LOG_PATH = ROOT / "configure.log"
LOG = []

def _log(msg: str):
    LOG.append(msg)

def _line_no_for_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1

# ---------- config path ----------
CFG_ROOT = ROOT / "site-config.yaml"
CFG_ALT  = BASE / "site-config.yaml"
CFG_PATH = Path(args.config) if args.config else (CFG_ROOT if CFG_ROOT.exists() else (CFG_ALT if CFG_ALT.exists() else CFG_ROOT))

# ---------- YAML load/save (PyYAML if verfügbar, sonst einfache Parser-Fallbacks) ----------
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
    ("brand_hex","Markenfarbe Light (HEX)","#FB7171", False),  # leer = vanilla
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

def prompt_missing(cfg: dict):
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

# ---------- helpers for robuste Dateiedits + Logging ----------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def replace_entire_line(text: str, key: str, value: str, file_path: Path = None) -> str:
    """
    Ersetzt die gesamte YAML-Zeile 'key: ...' durch 'key: value' (idempotent) und loggt Fundstellen.
    """
    pattern = re.compile(rf'^(\s*{re.escape(key)}:\s*).*$',
                         flags=re.M)
    matches = list(pattern.finditer(text))
    if matches:
        lines = [_line_no_for_pos(text, m.start()) for m in matches]
        _log(f"[{file_path.name if file_path else '?'}] replace_line key='{key}' → '{value}' (count={len(lines)}, lines={lines})")
        text = pattern.sub(rf'\1{value}', text)
    else:
        _log(f"[{file_path.name if file_path else '?'}] replace_line key='{key}' → keine Fundstelle")
    return text

def simple_replace(text: str, pairs: dict, file_path: Path = None) -> str:
    for old, new in pairs.items():
        cnt = text.count(old)
        if cnt:
            _log(f"[{file_path.name if file_path else '?'}] simple_replace '{old}' → '{new}' (count={cnt})")
            text = text.replace(old, new)
        else:
            _log(f"[{file_path.name if file_path else '?'}] simple_replace '{old}' → keine Fundstelle")
    return text

def set_light_brand_line(text: str, use_brand: bool) -> str:
    """
    Branding AN: 'light: lumen' → 'light: [lumen, css/custom.scss]'
    Branding AUS: 'light: [lumen, css/custom.scss]' → 'light: lumen'
    Idempotent.
    """
    if use_brand:
        pat = re.compile(r'(^\s*light:\s*(?:\[\s*)?lumen(?:\s*\])?\s*$)', flags=re.M)
        if "custom.scss" in text:
            return text
        return pat.sub('      light: [lumen, css/custom.scss]', text, count=1)
    # use_brand False → zurück auf vanilla
    text = re.sub(r'^\s*light:\s*\[.*?custom\.scss.*?\]\s*$', '      light: lumen', text, flags=re.M)
    return text

def set_dark_line(text: str, use_brand: bool, dark_on: bool) -> str:
    """
    Setzt/ersetzt die dark-Zeile passend zu Branding+Schalter.
    """
    if dark_on and use_brand:
        dark_line = '      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
    elif dark_on and not use_brand:
        dark_line = '      dark:  lumen'
    else:
        dark_line = '      #dark:  lumen' if not use_brand else '      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]'

    # Platzhalter ersetzen
    if "__DARK_THEME_LINE__" in text or "# __DARK_THEME_LINE__" in text:
        return text.replace("__DARK_THEME_LINE__", dark_line).replace("# __DARK_THEME_LINE__", dark_line)

    # Existierende dark-Zeile (Stack oder lumen; kommentiert oder nicht) ersetzen
    t2 = re.sub(r'^\s*#?\s*dark:\s*\[.*?\]\s*$', dark_line, text, flags=re.M)
    t2 = re.sub(r'^\s*#?\s*dark:\s*lumen\s*$', dark_line, t2, flags=re.M)
    if t2 != text:
        return t2

    # Falls keine dark-Zeile existiert: unter 'light:' einfügen
    m = re.search(r'(^\s*light:.*$)', text, flags=re.M)
    if m:
        return text[:m.end(1)] + "\n" + dark_line + text[m.end(1):]
    return text
  
def _escape_for_regex_path(host_plus_path: str) -> str:
    # regex-escape und Slashes als '\/' schreiben
    return re.escape(host_plus_path).replace("/", r"\/")

def set_link_external_filter_line(text: str, site_url: str, file_path: Path = None) -> str:
    """
    Setzt/aktualisiert 'link-external-filter:' in _quarto.yml so, dass die eigene site_url
    als 'intern' gilt. Idempotent: fügt den Host/Pfad nur hinzu, wenn noch nicht enthalten.
    Beispiel-Resultat:
      link-external-filter: '^(?:http:|https:)\/\/(user\.github\.io\/repo|www\.quarto\.org\/custom)'
    """
    if not (site_url or "").strip():
        _log(f"[{file_path.name if file_path else '?'}] link-external-filter: site_url leer → übersprungen")
        return text

    u = urlparse(site_url.strip())
    if not u.scheme or not u.netloc:
        _log(f"[{file_path.name if file_path else '?'}] link-external-filter: ungültige site_url → '{site_url}'")
        return text

    # host + optional Pfad (für GH Pages z.B. user.github.io/repo)
    host_path = u.netloc + (("/" + u.path.strip("/")) if u.path and u.path.strip("/") else "")
    site_piece = _escape_for_regex_path(host_path)

    wanted_val = f"'^(?:http:|https:)\\/\\/({site_piece}|www\\.quarto\\.org\\/custom)'"
    line_re = re.compile(r'^\s*link-external-filter:\s*.*$', re.M)

    # Falls Zeile bereits existiert: überschreiben, außer unser Host ist schon drin
    m = line_re.search(text)
    if m:
        current_line = m.group(0)
        if site_piece in current_line:
            _log(f"[{file_path.name if file_path else '?'}] link-external-filter: eigener Host bereits enthalten")
            return text
        new_line = re.sub(r':\s*.*$', f": {wanted_val}", current_line)
        text = text[:m.start()] + new_line + text[m.end():]
        _log(f"[{file_path.name if file_path else '?'}] link-external-filter aktualisiert → {wanted_val}")
        return text

    # Sonst einfügen: bevorzugt nach 'md-extensions:', sonst unter 'html:', sonst ans Ende
    md_match = re.search(r'^(\s*)md-extensions:\s*.*$', text, re.M)
    if md_match:
        indent = md_match.group(1)
        insert = f"\n{indent}link-external-filter: {wanted_val}"
        pos = md_match.end(0)
        text = text[:pos] + insert + text[pos:]
        _log(f"[{file_path.name if file_path else '?'}] link-external-filter eingefügt nach md-extensions → {wanted_val}")
        return text

    html_match = re.search(r'^(\s*)html:\s*$', text, re.M)
    if html_match:
        indent = html_match.group(1) + "  "
        insert = f"\n{indent}link-external-filter: {wanted_val}"
        pos = html_match.end(0)
        text = text[:pos] + insert + text[pos:]
        _log(f"[{file_path.name if file_path else '?'}] link-external-filter eingefügt unter html → {wanted_val}")
        return text

    # Fallback: einfach am Ende mit üblicher Einrückung ergänzen
    text = text.rstrip() + f"\n      link-external-filter: {wanted_val}\n"
    _log(f"[{file_path.name if file_path else '?'}] link-external-filter angehängt → {wanted_val}")
    return text


# ---------- updates ----------
def update_quarto_yaml(base: Path, v: dict):
    yml_path = base / "_quarto.yml"
    if not yml_path.exists():
        return
    yml = read_text(yml_path)

    USE_BRAND = bool((v.get("brand_hex") or "").strip())
    DARK_ON   = str(v.get("dark_theme","yes")).lower() == "yes"

    # 1) Light-Theme je nach Branding
    yml = set_light_brand_line(yml, USE_BRAND)

    # 2) Dark-Theme je nach Branding + Schalter
    yml = set_dark_line(yml, USE_BRAND, DARK_ON)

    # 3) Idempotente Zeilenersetzungen + Logging
    yml = replace_entire_line(yml, "title", f'"{v["site_title"]}"', yml_path)
    yml = replace_entire_line(yml, "site-url", v["site_url"], yml_path)
    yml = replace_entire_line(yml, "repo-url", v["repo_url"], yml_path)
    yml = replace_entire_line(yml, "logo", v["logo_path"], yml_path)
    yml = replace_entire_line(yml, "text", v["portal_text"], yml_path)
    yml = replace_entire_line(yml, "href", v["portal_url"], yml_path)

    # 4) Footer: Org-Name + Impressum-Link robust
    yml = simple_replace(yml, {
        'your organisation (<span class="year"></span>) —':
            f'{v["org_name"]} (<span class="year"></span>) —',
    }, yml_path)

    href_cfg = (v.get("impressum_href", "#") or "#").strip()
    href_cfg = re.sub(r'\.(qmd|md)$', '.html', href_cfg, flags=re.I)  # .qmd/.md → .html für Footer-HTML
    before = yml
    yml = re.sub(r'(<a[^>]*class="impressum-link"[^>]*href=")[^"]*(")',
                 rf'\1{href_cfg}\2', yml, flags=re.I)
    if yml != before:
        _log(f"[{yml_path.name}] regex_replace impressum-link → '{href_cfg}'")
    else:
        _log(f"[{yml_path.name}] impressum-link nicht gefunden (keine Änderung)")
    yml = set_link_external_filter_line(yml, v.get("site_url",""), yml_path)

    write_text(yml_path, yml)

def update_scss(base: Path, v: dict):
    # Branding leer → keine SCSS-Anpassung
    if not (v.get("brand_hex") or "").strip():
        _log("[custom.scss/theme-dark.scss] Branding leer → keine Änderungen")
        return

    css = base / "css" / "custom.scss"
    if css.exists():
        t = read_text(css)
        t2 = simple_replace(t, {
            '$brand: #FB7171;': f'$brand: {v["brand_hex"]};',
            '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
                f'$brand-font: {v["brand_font"]};',
        }, css)
        if t2 != t:
            write_text(css, t2)

    tdark = base / "css" / "theme-dark.scss"
    if tdark.exists():
        t = read_text(tdark)
        brand_dark = v["brand_hex_dark"] if (v.get("brand_hex_dark") or "").strip() else v.get("brand_hex","")
        if not brand_dark:
            _log("[theme-dark.scss] Dark-Brand leer → keine Änderungen")
            return
        t2 = simple_replace(t, {
            '$brand: #FB7171;': f'$brand: {brand_dark};',
            '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
                f'$brand-font: {v["brand_font"]};',
        }, tdark)
        if t2 != t:
            write_text(tdark, t2)

def update_impressum(base: Path, v: dict):
    imp = base / "base" / "impressum.qmd"
    if not imp.exists():
        return
    t = read_text(imp); before = t
    for k in ["responsible_name","responsible_address","responsible_email","imprint_url",
              "uni_name","uni_url","institute_name","institute_url","chair_name","chair_url"]:
        t = t.replace(f"{{{{{k}}}}}", str(v.get(k,"")))
    if t != before:
        write_text(imp, t)
        _log("[impressum.qmd] placeholders aktualisiert")
    else:
        _log("[impressum.qmd] keine placeholders gefunden/geändert")

def update_qmd_placeholders(base: Path, v: dict):
    keys = ["site_title","org_name","course_code","contact_email"]
    repl = {f"{{{{{k}}}}}": str(v.get(k,"")) for k in keys}
    changed = 0
    for path in base.rglob("*.qmd"):
        t = read_text(path); orig = t
        for old,new in repl.items():
            t = t.replace(old, new)
        if t != orig:
            write_text(path, t)
            _log(f"[{path.relative_to(BASE)}] placeholders aktualisiert")
            changed += 1
    if not changed:
        _log("[*.qmd] keine placeholders geändert")

def main():
    _log(f"=== configure.py run @ {datetime.now().isoformat(timespec='seconds')} ===")

    # 1) Konfig laden / fehlende ggf. abfragen
    cfg = load_yaml(CFG_PATH)
    cfg, changed = prompt_missing(cfg)

    # normalize to string
    for k,_,_,_ in SCHEMA:
        cfg[k] = str(cfg.get(k,"") or "")

    if changed or not CFG_PATH.exists():
        dump_yaml(CFG_PATH, cfg)
        _log(f"save config → {CFG_PATH}")

    # 2) Updates anwenden
    update_quarto_yaml(BASE, cfg)
    update_scss(BASE, cfg)
    update_impressum(BASE, cfg)
    update_qmd_placeholders(BASE, cfg)

    # 3) .nojekyll optional (nur falls docs/ bereits existiert)
    docs = ROOT / "docs"
    if docs.exists():
        (docs / ".nojekyll").write_text("", encoding="utf-8")
        _log("ensure docs/.nojekyll")

    # 4) Log schreiben (liegt im Repo-Root; wird nicht veröffentlicht)
    LOG_PATH.write_text("\n".join(LOG) + "\n", encoding="utf-8")
    print(f"🧾 Log geschrieben nach: {LOG_PATH}")
    print("✅ configuration applied. Commit & push to build on CI.")

if __name__=="__main__":
    main()

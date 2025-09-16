#!/usr/bin/env python3
# scripts/configure.py
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def ask(prompt, default=""):
    val = input(f"{prompt} [{default}]: ").strip()
    return val if val else default

# 1) Prompts
vals = {}
vals["site_title"]      = ask("Website-Titel", "your title")
vals["org_name"]        = ask("Organisation (Footer)", "your organisation")
vals["site_url"]        = ask("Site-URL", "https://your-github-name.github.io/your-repo")
vals["repo_url"]        = ask("Repo-URL",  "https://github.com/your-github-name/your-repo")
vals["logo_path"]       = ask("Logo-Pfad", "images/your-logo.png")
vals["portal_text"]     = ask("Navbar rechts: Link-Text", "Interne Lernplattform")
vals["portal_url"]      = ask("Navbar rechts: URL", "https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de")
vals["impressum_href"]  = ask("Footer: Impressum-Link (href)", "#")
vals["brand_hex"]       = ask("Markenfarbe Light (HEX)", "#FB7171")
vals["brand_hex_dark"]  = ask("Markenfarbe Dark (HEX, leer = wie Light)", "")
vals["brand_font"]      = ask("Primär-Schriftfamilie (CSS)", "system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif")
vals["dark_theme"]      = ask("Dark-Theme aktivieren? (yes/no)", "yes").lower()
vals["responsible_name"]    = ask("Verantwortliche Person", "")
vals["responsible_address"] = ask("Verantwortliche Adresse (HTML mit <br />)", "<br />")
vals["responsible_email"]   = ask("E-Mail-Adresse", "")
vals["uni_name"]            = ask("Universität", "")
vals["uni_url"]             = ask("Universitäts-URL", "")
vals["institute_name"]      = ask("Institut", "")
vals["institute_url"]       = ask("Institut-URL", "")
vals["chair_name"]          = ask("Lehrstuhl/AG", "")
vals["chair_url"]           = ask("Lehrstuhl/AG-URL", "")
vals["imprint_url"]         = ask("URL offizielles Uni-Impressum", "")

# 2) Ersetzungen (genau deine bisherigen Muster)
def replace_in_file(path, replacements):
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")

# _quarto.yml
quarto_repl = {
    'title: "your title"': f'title: "{vals["site_title"]}"',
    'site-url: https://your-github-name.github.io/your-repo': f'site-url: {vals["site_url"]}',
    'repo-url: https://github.com/your-github-name/your-repo': f'repo-url: {vals["repo_url"]}',
    'logo: images/your-logo.png': f'logo: {vals["logo_path"]}',
    'text: Interne Lernplattform': f'text: {vals["portal_text"]}',
    'href: https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de': f'href: {vals["portal_url"]}',
    'your organisation (<span class="year"></span>) —': f'{vals["org_name"]} (<span class="year"></span>) —',
    '<a class="impressum-link" href="#">Impressum</a>': f'<a class="impressum-link" href="{vals["impressum_href"]}">Impressum</a>',
}
# Dark-Theme Platzhalter
dark_line_on  = '      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
dark_line_off = '      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
quarto_repl['__DARK_THEME_LINE__'] = dark_line_on if vals["dark_theme"] == "yes" else dark_line_off
replace_in_file(ROOT / "_quarto.yml", quarto_repl)

# css/custom.scss
custom_repl = {
    '$brand: #FB7171;': f'$brand: {vals["brand_hex"]};',
    '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
        f'$brand-font: {vals["brand_font"]};',
}
replace_in_file(ROOT / "css" / "custom.scss", custom_repl)

# css/theme-dark.scss (falls vorhanden)
tdark = ROOT / "css" / "theme-dark.scss"
if tdark.exists():
    brand_dark = vals["brand_hex_dark"] if vals["brand_hex_dark"] else vals["brand_hex"]
    theme_dark_repl = {
        '$brand: #FB7171;': f'$brand: {brand_dark};',
        '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;':
            f'$brand-font: {vals["brand_font"]};',
    }
    replace_in_file(tdark, theme_dark_repl)

# base/impressum.qmd – Platzhalter einsetzen (wenn vorhanden)
imp = ROOT / "base" / "impressum.qmd"
if imp.exists():
    imp_repl = {
        "{{responsible_name}}": vals["responsible_name"],
        "{{responsible_address}}": vals["responsible_address"],
        "{{responsible_email}}": vals["responsible_email"],
        "{{imprint_url}}": vals["imprint_url"],
        "{{uni_name}}": vals["uni_name"],
        "{{uni_url}}": vals["uni_url"],
        "{{institute_name}}": vals["institute_name"],
        "{{institute_url}}": vals["institute_url"],
        "{{chair_name}}": vals["chair_name"],
        "{{chair_url}}": vals["chair_url"],
    }
    replace_in_file(imp, imp_repl)

print("\n✅ Konfiguration angewendet. Jetzt `git commit` und der CI-Workflow rendert.\n")

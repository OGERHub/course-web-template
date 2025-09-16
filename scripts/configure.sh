#!/usr/bin/env bash
# Konfiguration für Quarto-Kurswebsite anwenden (Bash).
# Default: non-interactive; --interactive erzwingt Abfragen.
# Optional: --config PATH zu site-config.yaml

set -euo pipefail

INTERACTIVE=0
CFG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--interactive) INTERACTIVE=1; shift ;;
    -n|--noninteractive) INTERACTIVE=0; shift ;;
    -c|--config) CFG="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 2 ;;
  esac
done

# locate ROOT/BASE
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ -f "$ROOT/_quarto.yml" ]]; then BASE="$ROOT"
elif [[ -f "$ROOT/template/_quarto.yml" ]]; then BASE="$ROOT/template"
else echo "❌ _quarto.yml not found (root or ./template)"; exit 1; fi

# config path
if [[ -n "$CFG" ]]; then CFG_PATH="$CFG"
elif [[ -f "$ROOT/site-config.yaml" ]]; then CFG_PATH="$ROOT/site-config.yaml"
elif [[ -f "$BASE/site-config.yaml" ]]; then CFG_PATH="$BASE/site-config.yaml"
else CFG_PATH="$ROOT/site-config.yaml"; fi
touch "$CFG_PATH"

# naive YAML get/set
yaml_get() { grep -E "^$1:" "$CFG_PATH" | head -n1 | sed -E 's/^[^:]+:[[:space:]]*//; s/^"//; s/"$//; s/^'\''//; s/'\''$//'; }
yaml_set() {
  local key="$1" val="$2"
  if grep -qE "^$key:" "$CFG_PATH"; then
    # escape slashes
    local esc="${val//\//\\/}"
    sed -i.bak -E "s|^($key:).*|\1 ${esc}|" "$CFG_PATH"
  else
    echo "$key: \"$val\"" >> "$CFG_PATH"
  fi
}

ask() { local label="$1" def="$2"; read -r -p "$label [$def]: " v || v=""; echo "${v:-$def}"; }

need() {
  local key="$1" label="$2" def="$3" required="$4"
  local cur
  cur="$(yaml_get "$key" || true)"
  if [[ -z "$cur" ]]; then
    if [[ "$INTERACTIVE" -eq 1 ]]; then
      cur="$(ask "$label" "$def")"
      yaml_set "$key" "$cur"
    else
      if [[ "$required" == "1" ]]; then
        echo "❌ Missing required value: $key"; exit 1
      else
        yaml_set "$key" "$def"
        cur="$def"
      fi
    fi
  fi
  eval "$key=\"\$cur\""
}

# schema (key label default required[0/1])
need site_title "Website-Titel" "your title" 1
need org_name "Organisation (Footer)" "your organisation" 1
need site_url "Site-URL" "https://your-github-name.github.io/your-repo" 1
need repo_url "Repo-URL" "https://github.com/your-github-name/your-repo" 1
need logo_path "Logo-Pfad" "images/your-logo.png" 0
need portal_text "Navbar rechts: Link-Text" "Interne Lernplattform" 0
need portal_url "Navbar rechts: URL" "https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de" 0
need impressum_href "Footer: Impressum-Link" "#" 0
need brand_hex "Markenfarbe Light (HEX)" "#FB7171" 1
need brand_hex_dark "Markenfarbe Dark (HEX, leer = wie Light)" "" 0
need brand_font "Primär-Schriftfamilie (CSS)" "system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif" 0
need dark_theme "Dark-Theme aktivieren? (yes/no)" "yes" 0
need responsible_name "Verantwortliche Person" "" 0
need responsible_address "Verantwortliche Adresse (HTML mit <br />)" "<br />" 0
need responsible_email "E-Mail-Adresse" "" 0
need uni_name "Universität" "" 0
need uni_url "Universitäts-URL" "" 0
need institute_name "Institut" "" 0
need institute_url "Institut-URL" "" 0
need chair_name "Lehrstuhl/AG" "" 0
need chair_url "Lehrstuhl/AG-URL" "" 0
need imprint_url "URL offizielles Uni-Impressum" "" 0

# sed helper (portable)
sedi() {
  if sed --version >/dev/null 2>&1; then sed -i "$@"; else sed -i '' "$@"; fi
}

replace_file() {
  local file="$1"; shift
  [[ -f "$file" ]] || return 0
  local tmp="$file.tmp.__cfg"
  cp "$file" "$tmp"
  while (( "$#" )); do
    local from="$1"; local to="$2"; shift 2
    from="${from//\//\\/}"
    to="${to//\//\\/}"
    sedi -e "s|$from|$to|g" "$tmp"
  done
  mv "$tmp" "$file"
}

# _quarto.yml
qt="$BASE/_quarto.yml"
dark_on='      dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
dark_off='      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]'
dark_line="$dark_on"; [[ "${dark_theme,,}" == "no" ]] && dark_line="$dark_off"

replace_file "$qt" \
  'title: "your title"' "title: \"$site_title\"" \
  'site-url: https://your-github-name.github.io/your-repo' "site-url: $site_url" \
  'repo-url: https://github.com/your-github-name/your-repo' "repo-url: $repo_url" \
  'logo: images/your-logo.png' "logo: $logo_path" \
  'text: Interne Lernplattform' "text: $portal_text" \
  'href: https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de' "href: $portal_url" \
  'your organisation (<span class="year"></span>) —' "$org_name (<span class=\"year\"></span>) —" \
  '<a class="impressum-link" href="#">Impressum</a>' "<a class=\"impressum-link\" href=\"$impressum_href\">Impressum</a>" \
  '__DARK_THEME_LINE__' "$dark_line" \
  '# __DARK_THEME_LINE__' "$dark_line"

# css/custom.scss
replace_file "$BASE/css/custom.scss" \
  '$brand: #FB7171;' "\$brand: $brand_hex;" \
  '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;' "\$brand-font: $brand_font;"

# css/theme-dark.scss
td="$BASE/css/theme-dark.scss"
if [[ -f "$td" ]]; then
  bd="$brand_hex"; [[ -n "$brand_hex_dark" ]] && bd="$brand_hex_dark"
  replace_file "$td" \
    '$brand: #FB7171;' "\$brand: $bd;" \
    '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;' "\$brand-font: $brand_font;"
fi

# base/impressum.qmd (Mustache-Platzhalter)
imp="$BASE/base/impressum.qmd"
if [[ -f "$imp" ]]; then
  replace_file "$imp" \
    '{{responsible_name}}' "$responsible_name" \
    '{{responsible_address}}' "$responsible_address" \
    '{{responsible_email}}' "$responsible_email" \
    '{{imprint_url}}' "$imprint_url" \
    '{{uni_name}}' "$uni_name" \
    '{{uni_url}}' "$uni_url" \
    '{{institute_name}}' "$institute_name" \
    '{{institute_url}}' "$institute_url" \
    '{{chair_name}}' "$chair_name" \
    '{{chair_url}}' "$chair_url"
fi

# ensure .nojekyll if docs exists
[[ -d "$ROOT/docs" ]] && : > "$ROOT/docs/.nojekyll"

echo "✅ configuration applied. Commit & push to build on CI."

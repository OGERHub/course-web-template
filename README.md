# Course Website Template (Quarto)

Ein Quarto-Gerüst für Kurs-Webseiten mit **Branding**, **Impressum** und **Auto-Deploy auf GitHub Pages**.

Ein Blick auf die [Demo Seite](https://ogerhub.github.io/course-web-template/) zeigt das Default-setup.

------------------------------------------------------------------------

1.  **Repo erstellen**

    -   GitHub: **Use this template** *(empfohlen)* – oder –
    -   CLI: `quarto use template ORG/REPO`

2.  **Konfigurieren**

    -   `site-config.yaml` ausfüllen **und**
    -   `python3 scripts/configure.py` ausführen (fragt nur fehlende Felder)

3.  **Pushen** → GitHub Actions baut → **Pages** veröffentlicht aus `docs/` .

    -   **Settings → Pages** *Build and deployment* → **Deploy from a branch** **Branch:** `main` • **Folder:** `/docs`
    -   **Settings → Actions → General** *Workflow permissions* → **Read and write permissions**

------------------------------------------------------------------------

## Voraussetzungen

-   Quarto CLI (empfohlen ≥ 1.5): `quarto --version`
-   Python 3 zum Setup: `python3 --version`
-   GitHub-Repo mit Schreibrechten

------------------------------------------------------------------------

# Neues Repo anlegen

## Variante A – GitHub Button

1.  Im Template-Repo: **Use this template** → neues Repo erstellen.

2.  Klonen:

    ``` bash
    git clone https://github.com/<USER>/<REPO>.git
    cd <REPO>
    ```

## Variante B – Quarto CLI

In einem **leeren** Ordner:

``` bash
quarto use template ORG/REPO
# Trust? Y
# Create subdirectory? n   # sonst landet alles in ./template/
```

> Quarto kopiert Dateien 1:1. Interaktive Abfragen übernimmt das Setup-Script (nächster Schritt).

------------------------------------------------------------------------

### Konfiguration anwenden (eine Variante wählen)

Im Repo befindet sich die **`site-config.yaml`** (in Ruhe ausfüllen). Dann das Config-Skript **`scripts/configure.py]`** (setzt Werte in Projektdateien) aufrufen. Falls Interaktiv gewählt wird werden alle Felder abgefragt.

#### Python

``` bash
# Python (Default: non-interactive)
python3 scripts/configure.py
# interaktiv:
python3 scripts/configure.py --interactive
# explizite Config-Datei:
python3 scripts/configure.py --noninteractive --config ./site-config.yaml
```

**Wichtige Felder (Beispiele):**

``` yaml
site_title: "lv007-SOSE-2030"
site_url:  "https://<USER>.github.io/<REPO>"
repo_url:  "https://github.com/<USER>/<REPO>"
logo_path: "images/your-logo.png"

brand_hex: "#FB7171"
brand_hex_dark: ""      # leer = wie Light
dark_theme: "yes"       # "yes" oder "no"

responsible_name: "Prof. Dr. …"
responsible_address: "Straße 1<br />12345 Ort"
responsible_email: "name@uni.de"
imprint_url: "https://www.uni.de/impressum"
```

Das Script aktualisiert u. a.:

-   `_quarto.yml` (Titel/URLs/Navbar/Impressum + Dark-Theme-Umschalter)
-   `css/custom.scss` (Markenfarbe, Schriftfamilie)
-   `css/theme-dark.scss` (optionale Dark-Farbe)
-   `base/impressum.qmd` (falls Platzhalter vorhanden)

------------------------------------------------------------------------

## Build & Deploy (GitHub Actions)

Der Workflow `.github/workflows/quarto-build.yml`:

1.  rendert mit Quarto (HTML + ggf. PDF/DOCX)
2.  schreibt das Ergebnis nach **`docs/`**
3.  committet `docs/` in den Branch

### Einmalige GitHub-Einstellungen im Ziel-Repo

-   **Settings → Pages** *Build and deployment* → **Deploy from a branch** **Branch:** `main` • **Folder:** `/docs`
-   **Settings → Actions → General** *Workflow permissions* → **Read and write permissions**

Seite live unter:

```         
https://<USER>.github.io/<REPO>/
```

## Täglicher Workflow

-   Inhalte anpassen (`index.qmd`, `base/*.qmd`, `session-*/…`, Bilder)

-   Branding ändern? → `site-config.yaml` anpassen → `python3 scripts/configure.py`

-   `git commit` → `git push` → CI baut → Pages aktualisiert

-   Konfiguration erneut anwenden: `python3 scripts/configure.py`

## Fehlerbehebung

-   **404**: Pages auf *Deploy from a branch* (`main`/`docs`) stellen; existiert `docs/index.html`? `site_url` exakt?
-   **Pages/Jekyll-Fehler**: `docs/.nojekyll` nicht vorhanden anlegen
-   **Workflow kann nicht pushen**: *Read & write permissions* setzen; bei strenger Orga ggf. PAT-Secret `GH_PAT` im Push-Step nutzen.
-   **Alles in `./template/` gelandet**: beim `quarto use` „Create subdirectory?“ mit **`n`** antworten – oder Inhalte aus `template/` eine Ebene hoch verschieben.

## Grundstruktur

```         
.
├─ _quarto.yml
├─ base/
│  ├─ about.qmd
│  ├─ faq.qmd
│  └─ impressum.qmd
├─ css/
│  ├─ custom.scss
│  ├─ theme-dark.scss
│  └─ styles.css
├─ images/
│  └─ your-logo.png
├─ scripts/
│  └─ configure.py
├─ site-config.yaml
├─ _footer-year.html
└─ .github/
   └─ workflows/
      └─ quarto-build.yml
```

------------------------------------------------------------------------

## 

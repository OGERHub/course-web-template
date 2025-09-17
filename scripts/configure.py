project:
  type: website
  output-dir: _site
  resources:
    - images/**
resource-path:
  - images
  - .

website:
  title: "your title"
  site-url: https://gisma-courses.github.io/test-template
  repo-url: https://github.com/gisma-courses/test-template
  repo-actions: []   # [source, issue, edit] bei Bedarf manuell setzen
  page-navigation: true
  bread-crumbs: false
  open-graph: true
  image: images/banner.png
  page-footer:
    center: |
      your organisation (<span class="year"></span>) —
      <a class="impressum-link" href="base/impressum.html">Impressum</a>

  search:
    location: navbar
    type: textbox

  navbar:
    background: primary
    foreground: light
    logo: images/your-logo.png
    left:
      - icon: question-square-fill
        text: Hotzenplotz
        href: https://www.ilias.uni-koeln.de/ilias/login.php
    right:
      - icon: chat-left-text-fill
        text: Hotzenplotz
        href: https://www.ilias.uni-koeln.de/ilias/login.php

  sidebar:
    pinned: true
    align: center
    style: docked
    collapse-level: 1
    contents:
      - section: "Willkommen"
        contents:
          - index.qmd
          - base/about.qmd
      - text: "---"
      - section: "Kurs-Sitzungen"
        contents:
          - section: "Sitzung 1"
            contents:
              - session-1/sitzung-1-01.qmd
          - section: "Sitzung 2"
            contents:
              - session-2/sitzung-2-01.qmd
              - session-2/sitzung-2-02.qmd

format:
  html:
    theme:
      light: [lumen]
      dark:  lumen

    css: css/styles.css
    toc: true
    code-copy: true
    code-background: true
    link-external-icon: true
    link-external-newwindow: true
    link-external-filter: '^(?:http:|https:)//(gisma\-courses\.github\.io/test\-template|www\.quarto\.org/custom)'
    md-extensions: +fenced_divs+bracketed_spans+link_attributes
    include-after-body:
      - "includes/_footer-year.html"


lang: de

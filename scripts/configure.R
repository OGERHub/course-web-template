#!/usr/bin/env Rscript
# Konfiguration anwenden (R).
# Default: non-interactive; --interactive fragt fehlende Werte.
# Optional: --config PATH

args <- commandArgs(trailingOnly = TRUE)
interactive <- FALSE  # default non-interactive = FALSE (keine Fragen)
cfg_path <- NULL
i <- 1
while (i <= length(args)) {
  if (args[[i]] %in% c("--interactive","-i")) { interactive <- TRUE; i <- i+1
  } else if (args[[i]] %in% c("--noninteractive","-n")) { interactive <- FALSE; i <- i+1
  } else if (args[[i]] %in% c("--config","-c")) { cfg_path <- args[[i+1]]; i <- i+2
  } else { stop(paste("Unknown arg:", args[[i]])) }
}

here <- normalizePath(file.path(dirname(sys.frame(1)$ofile %||% ""), ".."), mustWork = FALSE)
root <- normalizePath(file.path(here), mustWork = FALSE)
base <- if (file.exists(file.path(root, "_quarto.yml"))) root else
        if (file.exists(file.path(root, "template", "_quarto.yml"))) file.path(root, "template") else
        stop("_quarto.yml not found (root or ./template)")

cfg_root <- file.path(root, "site-config.yaml")
cfg_alt  <- file.path(base, "site-config.yaml")
cfg_file <- if (!is.null(cfg_path)) cfg_path else if (file.exists(cfg_root)) cfg_root else if (file.exists(cfg_alt)) cfg_alt else cfg_root

# YAML helpers
read_yaml <- function(path) {
  if (!file.exists(path)) return(list())
  out <- tryCatch({
    if (requireNamespace("yaml", quietly=TRUE)) yaml::read_yaml(path) else stop()
  }, error=function(e) NULL)
  if (!is.null(out)) return(out)
  # naive fallback
  lines <- readLines(path, warn=FALSE, encoding="UTF-8")
  kv <- list()
  for (ln in lines) {
    s <- trimws(ln)
    if (s=="" || substr(s,1,1)=="#" || !grepl(":", s)) next
    parts <- strsplit(s, ":", fixed=TRUE)[[1]]
    key <- trimws(parts[1]); val <- trimws(paste(parts[-1], collapse=":"))
    val <- sub('^"', "", sub('"$', "", sub("^'", "", sub("'$", "", val))))
    kv[[key]] <- val
  }
  kv
}

write_yaml <- function(path, lst) {
  ok <- tryCatch({
    if (requireNamespace("yaml", quietly=TRUE)) { yaml::write_yaml(lst, path); TRUE } else stop()
  }, error=function(e) FALSE)
  if (ok) return(invisible())
  con <- file(path, "w", encoding="UTF-8")
  on.exit(close(con))
  for (k in names(lst)) {
    v <- as.character(ifelse(is.null(lst[[k]]), "", lst[[k]]))
    if (grepl('[:# ]', v) || nchar(v)==0) v <- paste0('"', v, '"')
    writeLines(paste0(k, ": ", v), con)
  }
}

schema <- list(
  list("site_title","Website-Titel","your title", TRUE),
  list("org_name","Organisation (Footer)","your organisation", TRUE),
  list("site_url","Site-URL","https://your-github-name.github.io/your-repo", TRUE),
  list("repo_url","Repo-URL","https://github.com/your-github-name/your-repo", TRUE),
  list("logo_path","Logo-Pfad","images/your-logo.png", FALSE),
  list("portal_text","Navbar rechts: Link-Text","Interne Lernplattform", FALSE),
  list("portal_url","Navbar rechts: URL","https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de", FALSE),
  list("impressum_href","Footer: Impressum-Link","#", FALSE),
  list("brand_hex","Markenfarbe Light (HEX)","#FB7171", TRUE),
  list("brand_hex_dark","Markenfarbe Dark (HEX, leer = wie Light)","", FALSE),
  list("brand_font","Primär-Schriftfamilie (CSS)","system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif", FALSE),
  list("dark_theme","Dark-Theme aktivieren? (yes/no)","yes", FALSE),
  list("responsible_name","Verantwortliche Person","", FALSE),
  list("responsible_address","Verantwortliche Adresse (HTML mit <br />)","<br />", FALSE),
  list("responsible_email","E-Mail-Adresse","", FALSE),
  list("uni_name","Universität","", FALSE),
  list("uni_url","Universitäts-URL","", FALSE),
  list("institute_name","Institut","", FALSE),
  list("institute_url","Institut-URL","", FALSE),
  list("chair_name","Lehrstuhl/AG","", FALSE),
  list("chair_url","Lehrstuhl/AG-URL","", FALSE),
  list("imprint_url","URL offizielles Uni-Impressum","", FALSE)
)

cfg <- read_yaml(cfg_file)
changed <- FALSE
for (row in schema) {
  key <- row[[1]]; label <- row[[2]]; def <- row[[3]]; req <- isTRUE(row[[4]])
  cur <- trimws(as.character(ifelse(is.null(cfg[[key]]), "", cfg[[key]])))
  if (nzchar(cur)) next
  if (!interactive) {
    if (req) stop(paste("Missing required value:", key), call.=FALSE) else next
  } else {
    cat(sprintf("%s [%s]: ", label, def))
    inp <- readLines("stdin", n=1)
    if (length(inp)==0 || trimws(inp)== "") inp <- def
    cfg[[key]] <- inp
    changed <- TRUE
  }
}
# normalize to character
for (row in schema) {
  k <- row[[1]]; cfg[[k]] <- as.character(ifelse(is.null(cfg[[k]]), "", cfg[[k]]))
}
if (changed || !file.exists(cfg_file)) { write_yaml(cfg_file, cfg); cat("📝 saved config ->", cfg_file, "\n") }

read_text <- function(path) { paste(readLines(path, warn=FALSE, encoding="UTF-8"), collapse="\n") }
write_text <- function(path, txt) { con<-file(path,"w",encoding="UTF-8"); writeLines(txt, con); close(con) }
replace_all <- function(path, pairs) {
  if (!file.exists(path)) return(invisible(FALSE))
  txt <- read_text(path); orig <- txt
  for (i in seq(1, length(pairs), by=2)) {
    from <- pairs[[i]]; to <- pairs[[i+1]]
    txt <- gsub(from, to, txt, fixed=TRUE)
  }
  if (!identical(orig, txt)) write_text(path, txt)
  invisible(TRUE)
}

# _quarto.yml
qt <- file.path(base, "_quarto.yml")
dark_on  <- "      dark:  [lumen, css/theme-dark.scss, css/custom.scss]"
dark_off <- "      #dark:  [lumen, css/theme-dark.scss, css/custom.scss]"
dark_line <- if (tolower(cfg$dark_theme %||% "yes") == "yes") dark_on else dark_off
replace_all(qt, list(
  'title: "your title"', sprintf('title: "%s"', cfg$site_title),
  'site-url: https://your-github-name.github.io/your-repo', sprintf('site-url: %s', cfg$site_url),
  'repo-url: https://github.com/your-github-name/your-repo', sprintf('repo-url: %s', cfg$repo_url),
  'logo: images/your-logo.png', sprintf('logo: %s', cfg$logo_path),
  'text: Interne Lernplattform', cfg$portal_text,
  'href: https://www.ilias.uni-koeln.de/ilias/login.php?client_id=uk&cmd=force_login&lang=de', sprintf('href: %s', cfg$portal_url),
  'your organisation (<span class="year"></span>) —', sprintf('%s (<span class="year"></span>) —', cfg$org_name),
  '<a class="impressum-link" href="#">Impressum</a>', sprintf('<a class="impressum-link" href="%s">Impressum</a>', cfg$impressum_href),
  '__DARK_THEME_LINE__', dark_line,
  '# __DARK_THEME_LINE__', dark_line
))

# css/custom.scss
replace_all(file.path(base,"css","custom.scss"), list(
  '$brand: #FB7171;', sprintf('$brand: %s;', cfg$brand_hex),
  '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;', 
  sprintf('$brand-font: %s;', cfg$brand_font)
))

# css/theme-dark.scss
td <- file.path(base,"css","theme-dark.scss")
if (file.exists(td)) {
  bd <- if (nzchar(cfg$brand_hex_dark)) cfg$brand_hex_dark else cfg$brand_hex
  replace_all(td, list(
    '$brand: #FB7171;', sprintf('$brand: %s;', bd),
    '$brand-font: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;', 
    sprintf('$brand-font: %s;', cfg$brand_font)
  ))
}

# base/impressum.qmd
imp <- file.path(base,"base","impressum.qmd")
if (file.exists(imp)) {
  replace_all(imp, list(
    "{{responsible_name}}", cfg$responsible_name %||% "",
    "{{responsible_address}}", cfg$responsible_address %||% "",
    "{{responsible_email}}", cfg$responsible_email %||% "",
    "{{imprint_url}}", cfg$imprint_url %||% "",
    "{{uni_name}}", cfg$uni_name %||% "",
    "{{uni_url}}", cfg$uni_url %||% "",
    "{{institute_name}}", cfg$institute_name %||% "",
    "{{institute_url}}", cfg$institute_url %||% "",
    "{{chair_name}}", cfg$chair_name %||% "",
    "{{chair_url}}", cfg$chair_url %||% ""
  ))
}

# ensure .nojekyll if docs exists
if (dir.exists(file.path(root,"docs"))) {
  file.create(file.path(root,"docs",".nojekyll"))
}

cat("✅ configuration applied. Commit & push to build on CI.\n")

`%||%` <- function(a,b) if (is.null(a)) b else a

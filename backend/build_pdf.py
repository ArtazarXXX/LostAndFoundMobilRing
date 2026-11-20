"""Convert REVIEW.md into a styled HTML, then to PDF via Chrome headless."""
import subprocess
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).parent
MD_PATH = ROOT / "REVIEW.md"
HTML_PATH = ROOT / "REVIEW.html"
PDF_PATH = ROOT / "REVIEW.pdf"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

md = markdown.Markdown(
    extensions=[
        "fenced_code",
        "codehilite",
        "tables",
        "toc",
        "sane_lists",
        "attr_list",
    ],
    extension_configs={
        "codehilite": {
            "guess_lang": False,
            "noclasses": False,
            "pygments_style": "default",
        },
        "toc": {
            "title": "Содержание",
            "anchorlink": False,
            "permalink": False,
        },
    },
)

with MD_PATH.open(encoding="utf-8") as f:
    body_html = md.convert(f.read())

pygments_css = HtmlFormatter(style="default").get_style_defs(".codehilite")

CSS = """
@page {
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 9pt;
        color: #888;
    }
}

* { box-sizing: border-box; }

html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PT Sans", "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1f2328;
    max-width: 100%;
    margin: 0;
    padding: 0;
}

h1, h2, h3, h4 {
    font-weight: 700;
    line-height: 1.25;
    margin-top: 1.6em;
    margin-bottom: 0.5em;
    color: #0b1e3f;
    page-break-after: avoid;
}

h1 {
    font-size: 26pt;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 0.3em;
    margin-top: 0;
    color: #0b1e3f;
}

h2 {
    font-size: 18pt;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 0.25em;
    color: #1e3a8a;
    margin-top: 2em;
}

h3 {
    font-size: 14pt;
    color: #1d4ed8;
}

h4 {
    font-size: 12pt;
    color: #1f2937;
}

p { margin: 0.6em 0; }

a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }

strong { color: #0b1e3f; font-weight: 700; }

ul, ol {
    margin: 0.5em 0 0.8em 0;
    padding-left: 1.6em;
}

li { margin: 0.25em 0; }

li > ul, li > ol { margin: 0.25em 0; }

/* inline code */
code {
    font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
    font-size: 0.9em;
    background: #eef2ff;
    color: #1e3a8a;
    padding: 0.12em 0.38em;
    border-radius: 4px;
    border: 1px solid #e0e7ff;
}

/* code blocks */
pre {
    font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
    font-size: 9.5pt;
    line-height: 1.45;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 6px;
    padding: 12px 14px;
    overflow-x: auto;
    margin: 0.8em 0;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: inherit;
    font-size: inherit;
}

.codehilite {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 6px;
    margin: 0.8em 0;
    page-break-inside: avoid;
    overflow: hidden;
}
.codehilite pre {
    border: none;
    background: transparent;
    margin: 0;
    border-left: none;
    border-radius: 0;
}

/* tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #d1d5db;
    padding: 8px 10px;
    text-align: left;
    vertical-align: top;
}

th {
    background: #1e3a8a;
    color: white;
    font-weight: 600;
}

tr:nth-child(even) td { background: #f8fafc; }

/* blockquote */
blockquote {
    border-left: 4px solid #f59e0b;
    background: #fffbeb;
    padding: 10px 14px;
    margin: 1em 0;
    color: #78350f;
    border-radius: 4px;
}

blockquote p:first-child { margin-top: 0; }
blockquote p:last-child { margin-bottom: 0; }

/* horizontal rule */
hr {
    border: none;
    border-top: 2px dashed #cbd5e1;
    margin: 2em 0;
}

/* checklist */
ul.task-list { list-style: none; padding-left: 0.5em; }
li input[type="checkbox"] { margin-right: 0.5em; }

/* keep section headings on the same page as their first paragraph */
h2 + p, h3 + p, h2 + ul, h3 + ul, h2 + ol, h3 + ol { page-break-before: avoid; }

/* cover */
.cover {
    text-align: center;
    padding: 80px 20px 60px;
    page-break-after: always;
}
.cover .title {
    font-size: 32pt;
    font-weight: 800;
    color: #0b1e3f;
    margin-bottom: 12px;
    line-height: 1.2;
}
.cover .subtitle {
    font-size: 14pt;
    color: #475569;
    margin-bottom: 40px;
}
.cover .meta {
    display: inline-block;
    text-align: left;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    padding: 18px 26px;
    border-radius: 6px;
    font-size: 11pt;
    color: #1f2937;
    line-height: 1.8;
}
.cover .meta strong { color: #0b1e3f; }
.cover .accent {
    width: 60px;
    height: 4px;
    background: #2563eb;
    margin: 24px auto 32px;
    border-radius: 2px;
}
"""

html_doc = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Ревью бэкенда — ИТ-Куб</title>
<style>
{CSS}
{pygments_css}
</style>
</head>
<body>

<div class="cover">
    <div class="title">Ревью бэкенда<br>сервиса потерянных вещей</div>
    <div class="accent"></div>
    <div class="subtitle">Подробный разбор с примерами и инструкциями</div>
    <div class="meta">
        <strong>Проект:</strong> ИТ-Куб, итоговая работа<br>
        <strong>Файлы:</strong> <code>main.py</code>, <code>db.py</code><br>
        <strong>Технологии:</strong> Python 3, FastAPI, SQLite<br>
        <strong>Уровень:</strong> школьный итоговый проект
    </div>
</div>

{body_html}

</body>
</html>
"""

HTML_PATH.write_text(html_doc, encoding="utf-8")
print(f"HTML written: {HTML_PATH}")

print("Running Chrome headless to produce PDF...")
result = subprocess.run(
    [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_PATH}",
        f"file://{HTML_PATH}",
    ],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print("Chrome stderr:", result.stderr)
    raise SystemExit(result.returncode)

print(f"PDF written: {PDF_PATH} ({PDF_PATH.stat().st_size // 1024} KB)")

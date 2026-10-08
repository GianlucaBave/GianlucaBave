"""Generate the profile SVGs: hero, roadmap, tech map, career, footer.

Style: monochrome editorial (condensed display type, mono labels, square panels),
an ASCII-art texture, and blackletter accents. All display type is converted to
vector paths, so viewers need no fonts installed.

Run from the repo root:
    pip install fonttools
    python3 scripts/build_svgs.py --fonts path/to/fonts
The fonts folder must hold Anton-Regular.ttf and UnifrakturMaguntia-Book.ttf,
both under the SIL Open Font License (github.com/google/fonts).
"""
import argparse
import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parent.parent / "assets"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif"

WHITE, BLACK = "#ffffff", "#000000"
FONTS = {}  # "display" (Anton), "goth" (UnifrakturMaguntia); set in main


# ---------------------------------------------------------------- type helpers

def type_path(font, s, size, x, y, anchor="start", tracking=0.0):
    """Return (svg path d, width) for s set in one of FONTS."""
    f = FONTS[font]
    gs, cmap, hmtx = f.getGlyphSet(), f.getBestCmap(), f["hmtx"]
    k = size / f["head"].unitsPerEm
    names = [cmap.get(ord(ch), ".notdef") for ch in s]
    width = sum(hmtx[n][0] * k + tracking for n in names) - tracking
    cur = x - (width / 2 if anchor == "middle" else width if anchor == "end" else 0)
    pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}")
    for n in names:
        gs[n].draw(TransformPen(pen, (k, 0, 0, -k, cur, y)))
        cur += hmtx[n][0] * k + tracking
    return pen.getCommands(), width


def type_width(font, s, size, tracking=0.0):
    return type_path(font, s, size, 0, 0, tracking=tracking)[1]


def mono_w(s, size):
    return len(s) * size * 0.6


def mono(x, y, s, size=11, op=1.0, anchor="start", weight=400, fill=None, cls=""):
    c = f' class="{cls}"' if cls else ""
    fill = fill or WHITE
    return (f'<text{c} x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}" fill-opacity="{op}" letter-spacing=".04em">{escape(s)}</text>')


def sans(x, y, s, size=14, op=1.0, weight=400, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{SANS}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{WHITE}" fill-opacity="{op}">{escape(s)}</text>')


STYLE = """<style>
  .flow { stroke-dasharray: 3 6; animation: flow 1.4s linear infinite; }
  .blink { animation: blink 1.1s steps(1) infinite; }
  .pulse { animation: pulse 2.8s ease-out infinite; transform-box: fill-box; transform-origin: center; }
  @keyframes flow { to { stroke-dashoffset: -18; } }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes pulse { 0% { opacity: .6; transform: scale(1); } 80%,100% { opacity: 0; transform: scale(2.6); } }
  @keyframes ga { 0%,88%,96%,100% { opacity: 0; transform: none; clip-path: inset(0 0 0 0); }
    89% { opacity: .75; transform: translate(-7px,0); clip-path: inset(12% 0 62% 0); }
    91% { opacity: .75; transform: translate(6px,0); clip-path: inset(55% 0 20% 0); }
    93% { opacity: .75; transform: translate(-4px,0); clip-path: inset(30% 0 48% 0); }
    95% { opacity: .75; transform: translate(5px,0); clip-path: inset(78% 0 4% 0); } }
  @keyframes gb { 0%,88%,96%,100% { transform: none; } 90% { transform: translate(3px,0) skewX(-6deg); } 94% { transform: translate(-2px,0) skewX(4deg); } }
  .glitch-ghost { opacity: 0; animation: ga 6s steps(1) infinite; }
  .glitch-base { animation: gb 6s steps(1) infinite; transform-box: fill-box; transform-origin: center; }
  EXTRA
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }
</style>"""


def svg_open(w, h, title, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'
            f'{STYLE.replace("EXTRA", extra_css)}<rect width="{w}" height="{h}" fill="{BLACK}"/>')


def hairline(x1, y1, x2, y2, op=0.15, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{WHITE}" stroke-opacity="{op}"{d}/>'


def glitch_text(font, s, size, x, y, anchor="start", tracking=0.0, ident="t"):
    d, w = type_path(font, s, size, x, y, anchor, tracking)
    return (f'<defs><path id="{ident}" d="{d}"/></defs>'
            f'<g class="glitch-base"><use href="#{ident}" fill="{WHITE}"/></g>'
            f'<use class="glitch-ghost" href="#{ident}" fill="{WHITE}" fill-opacity=".55"/>'), w


def section_header(label, title, sub, numeral, w):
    d, _ = type_path("display", title.upper(), 44, 32, 104, tracking=0.5)
    nd, _ = type_path("goth", numeral, 150, w - 40, 140, anchor="end")
    return (mono(32, 46, f"( {label} )", 12, .7) +
            f'<path d="{nd}" fill="{WHITE}" fill-opacity=".14"/>'
            f'<path d="{d}" fill="{WHITE}"/>' +
            sans(32, 132, sub, 13.5, .6))


def wrap(s, limit):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > limit:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    return lines + [cur]


# ---------------------------------------------------------------- ASCII art

def ascii_orb(x0, y0, cols, rows, size=12, line=10.5, seed=3):
    """A lit sphere rendered in characters, with a cross cut out of it."""
    rnd = random.Random(seed)
    ramp = " .:-=+*#%@"
    cw = size * 0.6
    aspect = (rows * line) / (cols * cw)
    out = [f'<g font-family="{MONO}" font-size="{size}" fill="{WHITE}" xml:space="preserve">']
    for r in range(rows):
        cells = []
        for c in range(cols):
            nx = (c - cols / 2 + 0.5) / (cols / 2)
            ny = (r - rows / 2 + 0.5) / (rows / 2) * aspect
            d = math.hypot(nx, ny)
            cross = (abs(nx) < 0.11 and -0.82 < ny < 0.86) or (abs(ny + 0.28) < 0.1 and abs(nx) < 0.52)
            if d <= 1 and not cross:
                z = math.sqrt(1 - d * d)
                b = max(0.0, -0.45 * nx - 0.55 * ny + 0.7 * z)
                b = min(1.0, 0.08 + 0.95 * b)
            elif d > 1 and rnd.random() < 0.035:
                b = 0.2
            else:
                b = 0.0
            cells.append(b)
        # Run-length encode by opacity level to keep the file small.
        runs, cur_lvl, start, chars = [], None, 0, ""
        for c, b in enumerate(cells + [None]):
            lvl = None if b is None else (0 if b < 0.05 else min(4, int(b * 5)))
            if lvl != cur_lvl:
                if cur_lvl not in (None, 0) and chars.strip():
                    runs.append((start, cur_lvl, chars))
                cur_lvl, start, chars = lvl, c, ""
            if b is not None:
                chars += ramp[min(9, int(b * 9.99))] if lvl else " "
        y = y0 + r * line
        for start, lvl, chars in runs:
            out.append(f'<text x="{x0 + start * cw:.1f}" y="{y:.1f}" fill-opacity="{0.2 + 0.2 * lvl:.2f}">{escape(chars)}</text>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- hero

PHRASES = ["training risk models", "shipping LLM agents", "mapping 15,350 artists", "hunting target leaks"]
STATS = [("09", "PROJECTS"), ("#1", "KAGGLE PUBLIC LB"), ("15,350", "ARTISTS MAPPED"), ("470K", "MERCHANTS SCORED")]


def hero():
    W, H = 960, 600
    slot, n_ph = 3.2, len(PHRASES)
    cycle, share, typed = slot * n_ph, 100 / n_ph, 100 * 1.4 / (slot * n_ph)
    css = [f"@keyframes show {{ 0%,{share:.2f}% {{ opacity: 1; }} {share + .01:.2f}%,100% {{ opacity: 0; }} }}",
           f".phrase {{ opacity: 0; animation: show {cycle:.1f}s steps(1) infinite; }} .ph0 {{ opacity: 1; }}",
           "@keyframes scan { from { transform: translateY(0); } to { transform: translateY(380px); } }",
           ".scan { animation: scan 4.5s linear infinite; }"]
    for i, ph in enumerate(PHRASES):
        n, wpx = len(ph), mono_w(ph, 15)
        css += [f"@keyframes ty{i} {{ 0% {{ transform: scaleX(0); }} {typed:.2f}%,100% {{ transform: scaleX(1); }} }}",
                f"@keyframes cu{i} {{ 0% {{ transform: translateX(0); }} {typed:.2f}%,100% {{ transform: translateX({wpx:.1f}px); }} }}",
                f".ty{i} {{ transform-box: fill-box; transform-origin: left center; animation: ty{i} {cycle:.1f}s steps({n}) infinite; animation-delay: {slot*i:.1f}s; }}",
                f".cu{i} {{ animation: cu{i} {cycle:.1f}s steps({n}) infinite; animation-delay: {slot*i:.1f}s; }}",
                f".ph{i} {{ animation-delay: {slot*i:.1f}s; }}"]
    out = [svg_open(W, H, "Gianluca Bavelloni, MSc Business Analytics and AI", "\n  ".join(css))]

    # Top bar.
    out.append(mono(32, 40, "GIANLUCABAVE", 12, 1, weight=700))
    out.append(mono(W / 2, 40, "( PORTFOLIO · CV )", 12, .6, anchor="middle"))
    bw = mono_w("# SWITZERLAND", 12) + 28
    out.append(f'<rect x="{W - 32 - bw:.1f}" y="22" width="{bw:.1f}" height="28" fill="{WHITE}"/>'
               + mono(W - 32 - bw / 2, 40.5, "# SWITZERLAND", 12, 1, anchor="middle", weight=700, fill=BLACK))
    out.append(hairline(32, 66, W - 32, 66))

    # ASCII orb with a moving scan band.
    ox, oy, cols, rows = 640, 104, 40, 36
    out.append(ascii_orb(ox, oy, cols, rows))
    out.append(f'<defs><linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{WHITE}" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="{WHITE}" stop-opacity=".07"/><stop offset="1" stop-color="{WHITE}" stop-opacity="0"/></linearGradient></defs>'
               f'<rect class="scan" x="{ox - 6}" y="{oy - 14}" width="{cols * 7.2 + 12:.1f}" height="44" fill="url(#band)"/>')
    out.append(mono(ox, oy + rows * 10.5 + 8, "// RENDER: ORB.TXT  ·  40×36  ·  †", 10, .45))

    # Name: blackletter first name, condensed display surname with glitch.
    gd, _ = type_path("goth", "Gianluca", 96, 30, 196)
    out.append(mono(32, 104, "# 01   MSC BUSINESS ANALYTICS & AI", 12, .8))
    out.append(f'<path d="{gd}" fill="{WHITE}"/>')
    g, _ = glitch_text("display", "BAVELLONI", 136, 30, 352, tracking=1, ident="surname")
    out.append(g)

    # Intro and typed line.
    out.append(sans(32, 398, "I build cool stuff with AI agents. Sometimes it's even useful.", 17, 1, weight=700))
    out.append(sans(32, 422, "Risk models, recommenders, a DJ copilot, a finance bot that talks back.", 15, .6))
    tx = 32 + mono_w("> ", 15)
    out.append(mono(32, 470, ">", 15, .6))
    for i, ph in enumerate(PHRASES):
        out.append(f'<g class="phrase ph{i}"><clipPath id="cp{i}"><rect class="ty{i}" x="{tx:.1f}" y="454" width="{mono_w(ph, 15):.1f}" height="22"/></clipPath>'
                   f'<g clip-path="url(#cp{i})">{mono(tx, 470, ph, 15)}</g>'
                   f'<g class="cu{i}"><rect class="blink" x="{tx + 2:.1f}" y="457" width="8" height="16" fill="{WHITE}"/></g></g>')

    # Stats row.
    out.append(hairline(32, 500, W - 32, 500))
    colw = (W - 64) / len(STATS)
    for i, (num, label) in enumerate(STATS):
        x = 32 + i * colw
        if i:
            out.append(hairline(x, 500, x, H - 24))
        nd, _ = type_path("display", num, 40, x + (14 if i else 0), 556)
        out.append(f'<path d="{nd}" fill="{WHITE}"/>' + mono(x + (14 if i else 0), 578, f"// {label}", 10.5, .6))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- roadmap

LANES = [("ai", "AI PRODUCTS & LLM AGENTS"), ("web", "WEB & DATA VISUALISATION"), ("ml", "MACHINE LEARNING: RISK & PRICING")]

# Chronological order. "col" is the station column; projects in different lanes may share one.
PROJECTS = [
    dict(key="portfolio", name="AI Portfolio", date="OCT 2025", lane="web", col=0,
         tech=["Node.js·Express", "LLM chat", "Vercel"]),
    dict(key="artsync", name="ArtSync", date="JAN 2026", lane="web", col=1,
         tech=["Next.js·React", "Tailwind", "GenAI preview"]),
    dict(key="cvfit", name="CV Job Fit Checker", date="JAN 2026", lane="ai", col=1,
         tech=["Node.js", "Gemini API", "PDF parsing"]),
    dict(key="crowdloop", name="CrowdLoop AI", date="FEB 2026", lane="ai", col=2,
         tech=["Next.js", "Claude agent", "RAG·Web Audio"]),
    dict(key="fynn", name="Fynn", date="APR 2026", lane="ai", col=3, tag="TEAM PROJECT",
         tech=["Claude·SQL", "FastAPI", "LightGBM"]),
    dict(key="risk", name="Merchant Risk Scoring", date="APR 2026", lane="ml", col=3, tag="PRIVATE·NDA",
         tech=["XGBoost", "SHAP", "470k merchants"]),
    dict(key="credit", name="Credit Decision", date="JUN 2026", lane="ml", col=4, tag="#1 PUBLIC LB",
         tech=["CatBoost", "LightGBM", "XGBoost"]),
    dict(key="iphone", name="iPhone Deal-Finder", date="JUN 2026", lane="ml", col=5,
         tech=["Scraping", "LightGBM", "13.7k prices"]),
    dict(key="tunescape", name="Tunescape", date="JUN 2026", lane="web", col=6,
         tech=["8 recommenders", "Next.js", "deck.gl"]),
]

# (from, to, label, label position override or None)
LINKS = [
    ("portfolio", "cvfit", "NODE.JS·LLM", (94, 290)),
    ("portfolio", "artsync", "VERCEL", None),
    ("artsync", "tunescape", "NEXT.JS·REACT", (805, 370)),
    ("cvfit", "crowdloop", "GEMINI→CLAUDE", None),
    ("crowdloop", "fynn", "CLAUDE AGENTS", None),
    ("fynn", "risk", "TRANSACTIONS", (480, 492)),
    ("risk", "credit", "RISK·XGBOOST", None),
    ("credit", "iphone", "BOOSTING", None),
    ("iphone", "tunescape", "PYTHON ML", (730, 492)),
]


def label_box(x, y, s, size=9.5, inverted=False):
    w = mono_w(s, size) + 14
    fill, txt = (WHITE, BLACK) if inverted else (BLACK, WHITE)
    stroke = "" if inverted else f' stroke="{WHITE}" stroke-opacity=".35"'
    return (f'<rect x="{x - w/2:.1f}" y="{y - 9}" width="{w:.1f}" height="18" fill="{fill}"{stroke}/>'
            + mono(x, y + 3.5, s, size, 1 if inverted else .85, anchor="middle", fill=txt, weight=700 if inverted else 400))


def roadmap():
    W, H = 960, 810
    lane_y = {"ai": 194, "web": 394, "ml": 594}
    pos = {p["key"]: (90 + 130 * p["col"], lane_y[p["lane"]]) for p in PROJECTS}
    lane_of = {p["key"]: p["lane"] for p in PROJECTS}
    out = [svg_open(W, H, "Project roadmap: nine projects and the technology they share"),
           section_header("01 · PROJECT ROADMAP", "From analytics to AI products",
                          "Nine projects, Oct 2025 to Jun 2026. Lines link projects that share technology or domain.", "R", W)]
    for key, label in LANES:
        y = lane_y[key]
        lx = 520 if key == "web" else 32  # web label sits in the gap between link lines
        out.append(hairline(24, y, W - 24, y, .14, "1 4") + mono(lx, y - 18, f"// {label}", 10, .55))

    labels = []
    for a, b, label, at in LINKS:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        if y1 == y2:
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{WHITE}" stroke-width="2"/>')
            px, py = at if at else ((x1 + x2) / 2, y1 - 22)
        else:
            mx = (x1 + x2) / 2
            out.append(f'<path class="flow" d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" stroke="{WHITE}" stroke-opacity=".6" stroke-width="1.4"/>')
            px, py = at if at else (mx, (y1 + y2) / 2)
        labels.append(label_box(px, py, label))

    for p in PROJECTS:
        x, y = pos[p["key"]]
        name_lines = wrap(p["name"], 14)
        rows = ([(p["tag"], True)] if p.get("tag") else []) + [(t_, False) for t_ in p["tech"]]
        cw, cx0, cy0 = 120, x - 60, y + 20
        rows_y = cy0 + 34 + 16 * len(name_lines)
        ch = (rows_y - cy0) + 19 * len(rows) + 4
        out.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" fill="{WHITE}" fill-opacity=".06" stroke="{WHITE}" stroke-opacity=".16"/>'
                   + mono(cx0 + 10, cy0 + 19, p["date"], 9.5, .55))
        for j, ln in enumerate(name_lines):
            out.append(sans(cx0 + 10, cy0 + 38 + 16 * j, ln, 13, 1, weight=700))
        for j, (t_, is_tag) in enumerate(rows):
            ty = rows_y + 19 * j
            if is_tag:
                tw = mono_w(t_, 8.5) + 10
                out.append(f'<rect x="{cx0 + 10}" y="{ty - 6}" width="{tw:.1f}" height="15" fill="{WHITE}"/>'
                           + mono(cx0 + 15, ty + 4.5, t_, 8.5, 1, weight=700, fill=BLACK))
            else:
                out.append(mono(cx0 + 10, ty + 5, "—", 9.5, .4) + mono(cx0 + 24, ty + 5, t_, 9.5, .85))
        out.append(f'<rect class="pulse" x="{x - 6}" y="{y - 6}" width="12" height="12" fill="none" stroke="{WHITE}"/>'
                   f'<rect x="{x - 6}" y="{y - 6}" width="12" height="12" fill="{BLACK}" stroke="{WHITE}" stroke-width="2"/>'
                   f'<rect x="{x - 2.5}" y="{y - 2.5}" width="5" height="5" fill="{WHITE}"/>')
    out.extend(labels)
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- tech map

TECH_ROWS = [
    ("MACHINE LEARNING", [
        ("Python", {"risk", "credit", "iphone", "fynn"}),
        ("pandas · scikit-learn", {"risk", "credit", "iphone", "fynn"}),
        ("XGBoost", {"risk", "credit", "iphone"}),
        ("LightGBM", {"credit", "iphone", "fynn"}),
        ("CatBoost", {"credit"}),
        ("SHAP explainability", {"risk"}),
        ("Recommender algorithms", {"tunescape"}),
    ]),
    ("AI & LLM", [
        ("Claude API · tool use", {"crowdloop", "fynn"}),
        ("LangChain · text-to-SQL", {"fynn"}),
        ("Gemini API", {"cvfit"}),
        ("OpenRouter", {"portfolio"}),
        ("RAG · embeddings", {"crowdloop"}),
    ]),
    ("WEB & PRODUCT", [
        ("Next.js · React · TS", {"artsync", "crowdloop", "fynn", "tunescape"}),
        ("Tailwind CSS", {"artsync", "fynn", "tunescape"}),
        ("FastAPI", {"fynn"}),
        ("Node.js · Express", {"portfolio", "cvfit"}),
        ("deck.gl", {"tunescape"}),
        ("Web Audio API", {"crowdloop"}),
        ("Vercel", {"portfolio", "artsync", "cvfit", "crowdloop", "tunescape"}),
    ]),
    ("DATA", [
        ("Web scraping", {"iphone"}),
        ("PDF parsing", {"cvfit"}),
        ("Bank CSV ingestion", {"fynn"}),
    ]),
]

SHORT = {"portfolio": "PORTFOLIO", "artsync": "ARTSYNC", "fynn": "FYNN", "cvfit": "CV CHECK", "crowdloop": "CROWDLOOP",
         "risk": "RISK", "credit": "CREDIT", "iphone": "IPHONE", "tunescape": "TUNESCAPE"}


def techmap():
    rows = sum(len(r) for _, r in TECH_ROWS)
    W, top, rh, gh = 960, 196, 24, 32
    H = top + rows * rh + len(TECH_ROWS) * gh + 40
    col0, cstep = 262, 66
    cols = {p["key"]: col0 + cstep * i for i, p in enumerate(PROJECTS)}
    out = [svg_open(W, H, "Technology map: which tools each project uses"),
           section_header("02 · TECH MATRIX", "What the projects share",
                          "Each square is a tool used in a project. Rows with several squares are the shared foundations.", "T", W)]
    for p in PROJECTS:
        x = cols[p["key"]]
        out.append(mono(x, top - 20, SHORT[p["key"]], 9.5, .8, anchor="middle", weight=700)
                   + hairline(x, top - 8, x, H - 30, .1))
    out.append(mono(W - 36, top - 20, "USED IN", 9.5, .5, anchor="end", weight=700))
    y = top
    for group, items in TECH_ROWS:
        y += gh
        out.append(mono(32, y - 10, f"( {group} )", 10, .6))
        for label, used in items:
            out.append(f'<rect x="24" y="{y}" width="{W - 48}" height="{rh - 3}" fill="{WHITE}" fill-opacity=".045"/>'
                       + sans(36, y + 15, label, 12.5, .9))
            xs_used = [cols[k] for k in cols if k in used]
            if len(xs_used) > 1:
                out.append(f'<line x1="{min(xs_used)}" y1="{y + 10.5}" x2="{max(xs_used)}" y2="{y + 10.5}" stroke="{WHITE}" stroke-opacity=".4"/>')
            for k in used:
                x = cols[k]
                out.append(f'<rect x="{x - 4.5}" y="{y + 6}" width="9" height="9" fill="{WHITE}"/>')
            n = len(used)
            for s in range(5):  # segmented meter
                out.append(f'<rect x="{W - 132 + s * 14}" y="{y + 6}" width="10" height="9" fill="{WHITE}" fill-opacity="{1 if s < n else .12}"/>')
            out.append(mono(W - 36, y + 15, str(n), 11, 1, anchor="end", weight=700))
            y += rh
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- career

CAREER = [
    ("EDUCATION", [
        ("USI Lugano", "BA Economics, Finance major", (2021, 9), (2024, 9), "Thesis 9/10"),
        ("ESADE", "MSc Business Analytics", (2025, 8), (2026, 6), ""),
    ]),
    ("EXPERIENCE", [
        ("Neptun S.r.l.", "Business Operations Associate", (2021, 1), (2025, 5), ""),
        ("HMY Group", "Project Manager intern", (2024, 9), (2025, 1), ""),
        ("Fineco Bank", "Private Banking intern", (2025, 5), (2025, 7), ""),
        ("Global Payments", "Risk Analyst, graduate project", (2026, 2), (2026, 6), ""),
    ]),
]


def career():
    W = 960
    x0, x1, y0, rh = 270, W - 40, 178, 44
    span = (2027 - 2021) * 12

    def xm(ym):
        return x0 + (x1 - x0) * ((ym[0] - 2021) * 12 + ym[1] - 1) / span

    nrows = sum(len(r) for _, r in CAREER)
    H = y0 + nrows * rh + len(CAREER) * 30 + 34
    out = [svg_open(W, H, "Career timeline: education and experience 2021 to 2026"),
           section_header("03 · CAREER LOG", "Finance first, then data and AI",
                          "Economics in Lugano, operations and risk in Milan, analytics in Barcelona.", "C", W)]
    for yr in range(2021, 2027):
        x = xm((yr, 1))
        out.append(hairline(round(x, 1), y0 - 6, round(x, 1), H - 26, .12, "1 4") + mono(x + 4, y0 - 12, str(yr), 10.5, .55, weight=700))
    y = y0
    for gi, (group, items) in enumerate(CAREER):
        y += 30
        out.append(mono(32, y - 9, f"( {group} )", 10, .6))
        for org, role, a, b, note in items:
            xa, xb = xm(a), xm((b[0] + (b[1] // 12), b[1] % 12 + 1))
            out.append(sans(32, y + 17, org, 14, 1, weight=700) + sans(32, y + 33, role, 11.5, .55))
            solid = gi == 0
            out.append(f'<rect x="{xa:.1f}" y="{y + 8}" width="{max(xb - xa, 10):.1f}" height="22" fill="{WHITE}" '
                       f'fill-opacity="{1 if solid else .12}" stroke="{WHITE}" stroke-opacity="{0 if solid else .7}"/>')
            dates = f"{a[1]:02d}/{a[0] % 100:02d} → {b[1]:02d}/{b[0] % 100:02d}"
            label = f"{dates}  ·  {note}" if note else dates
            if xb - xa > mono_w(label, 10) + 20:
                out.append(mono(xa + 10, y + 23, label, 10, 1, weight=700, fill=BLACK if solid else WHITE))
            else:
                out.append(mono(xb + 8, y + 23, label, 10, .6))
            y += rh
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- footer

def footer():
    W = 960
    cap = FONTS["display"]["OS/2"].sCapHeight / FONTS["display"]["head"].unitsPerEm
    size = 100 * (W - 48) / type_width("display", "BAVELLONI", 100, 2)
    top = 150
    H = int(top + cap * size * 0.86)          # crop the bottom 14% of the wordmark
    base = top + cap * size
    out = [svg_open(W, H, "Gianluca Bavelloni")]
    out.append(hairline(32, 30, W - 32, 30))
    out.append(mono(32, 58, "( MSC BUSINESS ANALYTICS & AI )", 11, .6)
               + mono(W / 2, 58, "† MMXXVI †", 11, .6, anchor="middle")
               + mono(W - 32, 58, "SWITZERLAND", 11, .6, anchor="end"))
    gd, _ = type_path("goth", "Gianluca", 58, 32, 128)
    out.append(f'<path d="{gd}" fill="{WHITE}"/>')
    out.append(mono(W - 32, 126, "END OF FILE_", 11, .6, anchor="end", cls="blink"))
    g, _ = glitch_text("display", "BAVELLONI", size, W / 2, base, anchor="middle", tracking=2, ident="wordmark")
    out.append(g)
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="folder with Anton-Regular.ttf and UnifrakturMaguntia-Book.ttf")
    folder = Path(ap.parse_args().fonts)
    FONTS["display"] = TTFont(folder / "Anton-Regular.ttf")
    FONTS["goth"] = TTFont(folder / "UnifrakturMaguntia-Book.ttf")
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    for name, fn, inverted in (("hero", hero, False), ("roadmap", roadmap, False), ("techmap", techmap, True),
                               ("career", career, False), ("footer", footer, False)):
        # The tech matrix is printed light-on-dark inverted, to give the page a light/dark rhythm.
        WHITE, BLACK = ("#111111", "#ececec") if inverted else ("#ffffff", "#000000")
        (OUT / f"{name}.svg").write_text(fn())
    print("written:", sorted(p.name for p in OUT.glob("*.svg")))

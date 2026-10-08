"""Generate the profile SVGs (roadmap, tech map, career) in light and dark themes.

Run from the repo root:  python3 scripts/build_svgs.py
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"

THEMES = {
    "light": dict(bg="#ffffff", panel="#f6f8fa", fg="#1f2328", muted="#59636e", faint="#d1d9e0",
                  border="#d1d9e0", chip="#ffffff",
                  lanes={"ai": "#8250df", "web": "#0969da", "ml": "#1a7f37"}),
    "dark": dict(bg="#0d1117", panel="#151b23", fg="#e6edf3", muted="#9198a1", faint="#30363d",
                 border="#3d444d", chip="#0d1117",
                 lanes={"ai": "#a371f7", "web": "#4493f8", "ml": "#3fb950"}),
}

LANES = [
    ("ai", "AI PRODUCTS & LLM AGENTS"),
    ("web", "WEB & DATA VISUALISATION"),
    ("ml", "MACHINE LEARNING: RISK & PRICING"),
]

# Chronological order. "col" is the station column; projects in different lanes may share one.
PROJECTS = [
    dict(key="portfolio", name="AI Portfolio", date="OCT 2025", lane="web", col=0,
         tech=["Node.js · Express", "LLM chat", "Vercel"]),
    dict(key="artsync", name="ArtSync", date="JAN 2026", lane="web", col=1,
         tech=["Next.js · React", "Tailwind", "GenAI preview"]),
    dict(key="cvfit", name="CV Job Fit Checker", date="JAN 2026", lane="ai", col=1,
         tech=["Node.js", "Gemini API", "PDF parsing"]),
    dict(key="crowdloop", name="CrowdLoop AI", date="FEB 2026", lane="ai", col=2,
         tech=["Next.js", "Claude agent", "RAG · Web Audio"]),
    dict(key="fynn", name="Fynn", date="APR 2026", lane="ai", col=3, tag="team project",
         tech=["Claude agent · SQL", "FastAPI", "LightGBM"]),
    dict(key="risk", name="Merchant Risk Scoring", date="APR 2026", lane="ml", col=3, tag="private · NDA",
         tech=["XGBoost", "SHAP", "470k merchants"]),
    dict(key="credit", name="Credit Decision", date="JUN 2026", lane="ml", col=4, tag="#1 public LB",
         tech=["CatBoost", "LightGBM", "XGBoost"]),
    dict(key="iphone", name="iPhone Deal-Finder", date="JUN 2026", lane="ml", col=5,
         tech=["Scraping", "LightGBM", "13.7k prices"]),
    dict(key="tunescape", name="Tunescape", date="JUN 2026", lane="web", col=6,
         tech=["8 recommenders", "Next.js", "deck.gl"]),
]

# (from, to, label, label position override or None)
LINKS = [
    ("portfolio", "cvfit", "Node.js · LLM chat", (94, 250)),
    ("portfolio", "artsync", "Vercel", None),
    ("artsync", "tunescape", "Next.js · React", (805, 328)),
    ("cvfit", "crowdloop", "Gemini → Claude", None),
    ("crowdloop", "fynn", "Claude tool-use agents", None),
    ("fynn", "risk", "transaction data", (480, 450)),
    ("risk", "credit", "risk scoring · XGBoost", None),
    ("credit", "iphone", "gradient boosting", None),
    ("iphone", "tunescape", "Python ML pipelines", (722, 450)),
]

STYLE = """
<style>
  .flow { stroke-dasharray: 5 5; animation: flow 1.4s linear infinite; }
  .pulse { animation: pulse 2.4s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }
  @keyframes flow { to { stroke-dashoffset: -20; } }
  @keyframes pulse { 0%,100% { opacity: .35; transform: scale(1); } 50% { opacity: 0; transform: scale(2.1); } }
  @media (prefers-reduced-motion: reduce) { .flow, .pulse { animation: none; } }
</style>
"""


def text_w(s, size):
    """Rough width estimate for the system UI font."""
    return sum(0.33 if c in " .,:·'ilI|" else 0.62 if c.isupper() or c.isdigit() else 0.55 for c in s) * size


def svg_open(w, h, t, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>{STYLE}'
            f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>')


def header(t, eyebrow, title, sub, color):
    return (f'<text x="32" y="40" font-size="11" font-weight="700" letter-spacing="1.6" fill="{color}">{escape(eyebrow)}</text>'
            f'<text x="32" y="66" font-size="21" font-weight="700" fill="{t["fg"]}">{escape(title)}</text>'
            f'<text x="32" y="88" font-size="12.5" fill="{t["muted"]}">{escape(sub)}</text>')


def pill(x, y, label, t, color, size=10):
    w = text_w(label, size) + 16
    return (f'<rect x="{x - w/2:.1f}" y="{y - 10}" width="{w:.1f}" height="20" rx="10" fill="{t["bg"]}" stroke="{color}" stroke-opacity=".55"/>'
            f'<text x="{x}" y="{y + 3.6:.1f}" font-size="{size}" text-anchor="middle" fill="{color}" font-weight="600">{escape(label)}</text>')


def wrap(s, limit):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        if cur and len(cur) + 1 + len(wd) > limit:
            lines.append(cur)
            cur = wd
        else:
            cur = f"{cur} {wd}".strip()
    return lines + [cur]


def roadmap(t):
    W, H = 960, 750
    lane_y = {"ai": 150, "web": 350, "ml": 550}
    xs = {p["key"]: 90 + 130 * p["col"] for p in PROJECTS}
    pos = {p["key"]: (xs[p["key"]], lane_y[p["lane"]]) for p in PROJECTS}
    lane_of = {p["key"]: p["lane"] for p in PROJECTS}
    out = [svg_open(W, H, t, "Project roadmap: seven projects and the technology they share"),
           header(t, "PROJECT ROADMAP", "From analytics to AI products",
                  "9 projects, Oct 2025 to Jun 2026. Lines link projects that share technology or domain.",
                  t["lanes"]["ai"])]

    # Lane rails and labels.
    for key, label in LANES:
        y, c = lane_y[key], t["lanes"][key]
        out.append(f'<line x1="24" y1="{y}" x2="{W-24}" y2="{y}" stroke="{t["faint"]}" stroke-width="2" stroke-linecap="round"/>')
        lx = 520 if key == "web" else 30  # web label sits in the gap between link lines
        out.append(f'<circle cx="{lx}" cy="{y - 22}" r="4" fill="{c}"/>'
                   f'<text x="{lx + 10}" y="{y - 18}" font-size="10" font-weight="700" letter-spacing="1.2" fill="{c}">{escape(label)}</text>')

    # Links: same lane = solid coloured segment, cross lane = dashed animated curve.
    pills = []
    for a, b, label, at in LINKS:
        (x1, y1), (x2, y2) = pos[a], pos[b]
        ca, cb = t["lanes"][lane_of[a]], t["lanes"][lane_of[b]]
        if y1 == y2:
            out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ca}" stroke-width="4" stroke-linecap="round"/>')
            px, py = at if at else ((x1 + x2) / 2, y1 - 22)
            pills.append(pill(px, py, label, t, ca))
        else:
            mx = (x1 + x2) / 2
            gid = f"g_{a}_{b}"
            out.append(f'<defs><linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" gradientUnits="userSpaceOnUse">'
                       f'<stop offset="0" stop-color="{ca}"/><stop offset="1" stop-color="{cb}"/></linearGradient></defs>')
            out.append(f'<path class="flow" d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" '
                       f'stroke="url(#{gid})" stroke-width="2"/>')
            px, py = at if at else (mx, (y1 + y2) / 2)
            pills.append(pill(px, py, label, t, t["muted"]))

    # Station cards.
    for i, p in enumerate(PROJECTS):
        x, y = pos[p["key"]]
        c = t["lanes"][p["lane"]]
        name_lines = wrap(p["name"], 15)
        cw, cx0, cy0 = 120, x - 60, y + 18
        chips = ([(p["tag"], True)] if p.get("tag") else []) + [(x_, False) for x_ in p["tech"]]
        chips_y = cy0 + 34 + 15 * len(name_lines)
        ch = (chips_y - cy0) + 22 * len(chips) + 6
        g = [f'<g class="rise" style="animation-delay:{i * 0.12:.2f}s">']
        g.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="10" fill="{t["panel"]}" stroke="{t["border"]}"/>')
        g.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="3" rx="1.5" fill="{c}"/>')
        g.append(f'<text x="{cx0 + 10}" y="{cy0 + 20}" font-size="9.5" font-weight="700" letter-spacing="1" fill="{t["muted"]}">{p["date"]}</text>')
        for j, ln in enumerate(name_lines):
            g.append(f'<text x="{cx0 + 10}" y="{cy0 + 38 + 15 * j}" font-size="12.5" font-weight="700" fill="{t["fg"]}">{escape(ln)}</text>')
        for j, (tech, is_tag) in enumerate(chips):
            ty = chips_y + 22 * j
            tw = text_w(tech, 10) + 14
            if is_tag:
                g.append(f'<rect x="{cx0 + 10}" y="{ty - 6}" width="{tw:.1f}" height="18" rx="9" fill="{c}" fill-opacity=".15" stroke="{c}" stroke-opacity=".5"/>'
                         f'<text x="{cx0 + 17}" y="{ty + 6.5}" font-size="10" font-weight="700" fill="{c}">{escape(tech)}</text>')
            else:
                g.append(f'<rect x="{cx0 + 10}" y="{ty - 6}" width="{tw:.1f}" height="18" rx="9" fill="{t["chip"]}" stroke="{t["border"]}"/>'
                         f'<text x="{cx0 + 17}" y="{ty + 6.5}" font-size="10" fill="{t["fg"]}">{escape(tech)}</text>')
        g.append("</g>")
        out.extend(g)
        # Node on the rail, drawn last so it sits on top of links.
        out.append(f'<circle class="pulse" cx="{x}" cy="{y}" r="7" fill="{c}"/>'
                   f'<circle cx="{x}" cy="{y}" r="7" fill="{t["bg"]}" stroke="{c}" stroke-width="3"/>')

    out.extend(pills)
    out.append("</svg>")
    return "".join(out)


TECH_ROWS = [
    ("MACHINE LEARNING", "ml", [
        ("Python", {"risk", "credit", "iphone", "fynn"}),
        ("pandas · scikit-learn", {"risk", "credit", "iphone", "fynn"}),
        ("XGBoost", {"risk", "credit", "iphone"}),
        ("LightGBM", {"credit", "iphone", "fynn"}),
        ("CatBoost", {"credit"}),
        ("SHAP explainability", {"risk"}),
        ("Recommender algorithms", {"tunescape"}),
    ]),
    ("AI & LLM", "ai", [
        ("Claude API · tool use", {"crowdloop", "fynn"}),
        ("LangChain · text-to-SQL", {"fynn"}),
        ("Gemini API", {"cvfit"}),
        ("OpenRouter", {"portfolio"}),
        ("RAG · embeddings", {"crowdloop"}),
    ]),
    ("WEB & PRODUCT", "web", [
        ("Next.js · React · TypeScript", {"artsync", "crowdloop", "fynn", "tunescape"}),
        ("Tailwind CSS", {"artsync", "fynn", "tunescape"}),
        ("FastAPI", {"fynn"}),
        ("Node.js · Express", {"portfolio", "cvfit"}),
        ("deck.gl", {"tunescape"}),
        ("Web Audio API", {"crowdloop"}),
        ("Vercel", {"portfolio", "artsync", "cvfit", "crowdloop", "tunescape"}),
    ]),
    ("DATA", "web", [
        ("Web scraping", {"iphone"}),
        ("PDF parsing", {"cvfit"}),
        ("Bank CSV ingestion", {"fynn"}),
    ]),
]

SHORT = {"portfolio": "Portfolio", "artsync": "ArtSync", "fynn": "Fynn", "cvfit": "CV Checker", "crowdloop": "CrowdLoop", "risk": "Risk Score",
         "credit": "Credit", "iphone": "Deal-Finder", "tunescape": "Tunescape"}


def techmap(t):
    rows = sum(len(r) for _, _, r in TECH_ROWS)
    W, top, rh, gh = 960, 150, 24, 30
    H = top + rows * rh + len(TECH_ROWS) * gh + 36
    col0, cstep = 262, 68
    cols = {p["key"]: col0 + cstep * i for i, p in enumerate(PROJECTS)}
    out = [svg_open(W, H, t, "Technology map: which tools each project uses"),
           header(t, "TECHNOLOGY MAP", "What the projects have in common",
                  "Each dot is a tool used in a project. Rows with several dots are the shared foundations.",
                  t["lanes"]["ml"])]
    for p in PROJECTS:
        x, c = cols[p["key"]], t["lanes"][p["lane"]]
        out.append(f'<text x="{x}" y="{top - 22}" font-size="10.5" font-weight="700" text-anchor="middle" fill="{t["fg"]}">{SHORT[p["key"]]}</text>'
                   f'<rect x="{x - 16}" y="{top - 14}" width="32" height="3" rx="1.5" fill="{c}"/>'
                   f'<line x1="{x}" y1="{top}" x2="{x}" y2="{H - 30}" stroke="{t["faint"]}" stroke-dasharray="2 4"/>')
    out.append(f'<text x="{W - 32}" y="{top - 22}" font-size="11" font-weight="700" text-anchor="end" fill="{t["muted"]}">USED IN</text>')
    y = top
    for gi, (group, gcolor, items) in enumerate(TECH_ROWS):
        y += gh
        out.append(f'<text x="32" y="{y - 8}" font-size="10" font-weight="700" letter-spacing="1.2" fill="{t["lanes"][gcolor]}">{escape(group)}</text>')
        for label, used in items:
            out.append(f'<rect x="24" y="{y}" width="{W - 48}" height="{rh - 2}" rx="6" fill="{t["panel"]}"/>')
            out.append(f'<text x="36" y="{y + 15}" font-size="12" fill="{t["fg"]}">{escape(label)}</text>')
            xs_used = [cols[k] for k in cols if k in used]
            if len(xs_used) > 1:
                out.append(f'<line x1="{min(xs_used)}" y1="{y + 11}" x2="{max(xs_used)}" y2="{y + 11}" '
                           f'stroke="{t["muted"]}" stroke-opacity=".45" stroke-width="2"/>')
            for p in PROJECTS:
                if p["key"] in used:
                    out.append(f'<circle cx="{cols[p["key"]]}" cy="{y + 11}" r="6" fill="{t["lanes"][p["lane"]]}"/>')
            n = len(used)
            bx = W - 120
            out.append(f'<rect x="{bx}" y="{y + 7}" width="60" height="8" rx="4" fill="{t["faint"]}"/>'
                       f'<rect x="{bx}" y="{y + 7}" width="{n * 12}" height="8" rx="4" fill="{t["lanes"][gcolor]}"/>'
                       f'<text x="{W - 36}" y="{y + 15}" font-size="11" font-weight="700" text-anchor="end" fill="{t["fg"]}">{n}</text>')
            y += rh
    out.append("</svg>")
    return "".join(out)


CAREER = [
    ("EDUCATION", [
        ("USI Lugano", "BA Economics, Finance major", (2021, 9), (2024, 9), "web", "Thesis 9/10"),
        ("ESADE", "MSc Business Analytics", (2025, 8), (2026, 6), "web", ""),
    ]),
    ("EXPERIENCE", [
        ("Neptun S.r.l.", "Business Operations Associate", (2021, 1), (2025, 5), "ml", ""),
        ("HMY Group", "Project Manager intern", (2024, 9), (2025, 1), "ml", ""),
        ("Fineco Bank", "Private Banking intern", (2025, 5), (2025, 7), "ml", ""),
        ("Global Payments", "Risk Analyst, graduate project", (2026, 2), (2026, 6), "ai", ""),
    ]),
]


def career(t):
    W = 960
    x0, x1, y0, rh = 250, W - 40, 130, 44
    years = list(range(2021, 2027))
    span = (2027 - 2021) * 12

    def xm(ym):
        return x0 + (x1 - x0) * ((ym[0] - 2021) * 12 + ym[1] - 1) / span

    nrows = sum(len(r) for _, r in CAREER)
    H = y0 + nrows * rh + len(CAREER) * 28 + 30
    out = [svg_open(W, H, t, "Career timeline: education and experience 2021 to 2026"),
           header(t, "CAREER", "Finance first, then data and AI",
                  "Economics in Lugano, operations and risk in Milan, analytics in Barcelona.", t["lanes"]["web"])]
    for yr in years:
        x = xm((yr, 1))
        out.append(f'<line x1="{x:.1f}" y1="{y0 - 6}" x2="{x:.1f}" y2="{H - 24}" stroke="{t["faint"]}" stroke-dasharray="2 4"/>'
                   f'<text x="{x + 4:.1f}" y="{y0 - 12}" font-size="11" font-weight="700" fill="{t["muted"]}">{yr}</text>')
    y = y0
    i = 0
    for group, items in CAREER:
        y += 28
        out.append(f'<text x="32" y="{y - 8}" font-size="10" font-weight="700" letter-spacing="1.2" fill="{t["muted"]}">{group}</text>')
        for org, role, a, b, lane, note in items:
            c = t["lanes"][lane]
            xa, xb = xm(a), xm((b[0] + (b[1] // 12), b[1] % 12 + 1))
            out.append(f'<text x="32" y="{y + 17}" font-size="13" font-weight="700" fill="{t["fg"]}">{escape(org)}</text>'
                       f'<text x="32" y="{y + 33}" font-size="11" fill="{t["muted"]}">{escape(role)}</text>')
            out.append(f'<g class="rise" style="animation-delay:{i * 0.1:.2f}s">'
                       f'<rect x="{xa:.1f}" y="{y + 8}" width="{max(xb - xa, 8):.1f}" height="22" rx="11" fill="{c}" fill-opacity=".9"/>')
            dates = f"{a[1]:02d}/{a[0] % 100:02d} – {b[1]:02d}/{b[0] % 100:02d}"
            label = f"{dates}  ·  {note}" if note else dates
            lw = text_w(label, 10.5) + 20
            if xb - xa > lw:
                out.append(f'<text x="{xa + 11:.1f}" y="{y + 23}" font-size="10.5" font-weight="700" fill="{t["bg"]}">{escape(label)}</text>')
            else:
                out.append(f'<text x="{xb + 8:.1f}" y="{y + 23}" font-size="10.5" font-weight="600" fill="{t["muted"]}">{escape(label)}</text>')
            out.append("</g>")
            y += rh
            i += 1
    out.append("</svg>")
    return "".join(out)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in (("roadmap", roadmap), ("techmap", techmap), ("career", career)):
        for theme, t in THEMES.items():
            (OUT / f"{name}-{theme}.svg").write_text(fn(t))
    print("written:", sorted(p.name for p in OUT.glob("*.svg")))

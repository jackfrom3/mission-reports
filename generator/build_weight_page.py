"""Generator for the per-athlete mobile weight-tracking page.

One page per athlete: logo header, the line graph, footer. Nothing else.
Same visual system as build_mobile_report.py — dark monochrome, Barlow headings.

Usage from anywhere:
    import sys; sys.path.insert(0, "/Users/jackanderson/Desktop/Mission Performance SB/mission-reports/generator")
    from build_weight_page import build_weight_page, build_weight_og, weight_slug

    entries = [("2026-06-03", 148), ("2026-07-15", 152), ("2026-09-02", 157)]
    slug = weight_slug("Brandon Weaver")          # -> brandon-weaver-weight
    open(f"{slug}.html","w").write(build_weight_page("Brandon Weaver", entries))
    build_weight_og("Brandon Weaver", slug)

Entries are (ISO date, weight in lbs). Order doesn't matter — they get sorted.
A single entry renders as one labeled dot, no line.
"""
import html as _html
import os
from datetime import date

GEN_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(GEN_DIR)
ASSETS = f"{GEN_DIR}/assets"

with open(f"{GEN_DIR}/head_template.html") as f:
    HEAD_CSS = f.read()
with open(f"{ASSETS}/logo_src.txt") as f:
    LOGO_SRC = f.read().strip()

# Chart geometry (SVG user units; the svg scales to card width)
CW, CH = 320, 132
PAD_L, PAD_R, PAD_T, PAD_B = 12, 12, 22, 26
MIN_SPAN = 10.0  # lbs — floor on the y-window so small changes don't look dramatic

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def esc(s):
    return _html.escape(str(s), quote=False)


def _d(iso):
    y, m, dd = (int(x) for x in iso.split("-"))
    return date(y, m, dd)


def fmt_short(iso):
    d = _d(iso)
    return f"{MONTHS[d.month - 1]} {d.day}"


def fmt_long(iso):
    d = _d(iso)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def fmt_w(w):
    """152.0 -> '152', 152.5 -> '152.5'"""
    return f"{w:g}"


def _chart_svg(entries):
    """entries: sorted list of (iso, weight). Returns (svg_html, point_data)."""
    weights = [w for _, w in entries]
    lo, hi = min(weights), max(weights)
    mid = (lo + hi) / 2
    span = max(hi - lo, MIN_SPAN)
    y_lo, y_hi = mid - span / 2, mid + span / 2

    def ypx(w):
        t = (w - y_lo) / (y_hi - y_lo)
        return PAD_T + (1 - t) * (CH - PAD_T - PAD_B)

    d0 = _d(entries[0][0])
    total_days = (_d(entries[-1][0]) - d0).days

    def xpx(iso):
        if total_days <= 0:
            return CW / 2
        t = (_d(iso) - d0).days / total_days
        return PAD_L + t * (CW - PAD_L - PAD_R)

    pts = [(xpx(iso), ypx(w), iso, w) for iso, w in entries]

    # recessive baseline grid: top and bottom of the y-window
    grid = (
        f'<line x1="0" y1="{ypx(y_hi):.1f}" x2="{CW}" y2="{ypx(y_hi):.1f}" class="g"/>'
        f'<line x1="0" y1="{ypx(y_lo):.1f}" x2="{CW}" y2="{ypx(y_lo):.1f}" class="g"/>'
    )

    line = ""
    if len(pts) > 1:
        dpath = " ".join(
            ("M" if i == 0 else "L") + f"{x:.1f} {y:.1f}"
            for i, (x, y, _, _) in enumerate(pts)
        )
        line = f'<path d="{dpath}" class="ln"/>'

    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" class="pt" '
        f'data-date="{esc(fmt_long(iso))}" data-w="{esc(fmt_w(w))}"/>'
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" class="hit" '
        f'data-date="{esc(fmt_long(iso))}" data-w="{esc(fmt_w(w))}"/>'
        for x, y, iso, w in pts
    )

    # direct labels: first and last only (never every point)
    labels = ""
    fx, fy, fiso, fw = pts[0]
    if len(pts) > 1:
        lx, ly, liso, lw = pts[-1]
        labels += (
            f'<text x="{fx:.1f}" y="{fy - 11:.1f}" class="vl" text-anchor="start">{esc(fmt_w(fw))}</text>'
            f'<text x="{lx:.1f}" y="{ly - 11:.1f}" class="vl" text-anchor="end">{esc(fmt_w(lw))}</text>'
            f'<text x="{fx:.1f}" y="{CH - 7}" class="dl" text-anchor="start">{esc(fmt_short(fiso))}</text>'
            f'<text x="{lx:.1f}" y="{CH - 7}" class="dl" text-anchor="end">{esc(fmt_short(liso))}</text>'
        )
    else:
        labels += (
            f'<text x="{fx:.1f}" y="{fy - 11:.1f}" class="vl" text-anchor="middle">{esc(fmt_w(fw))}</text>'
            f'<text x="{fx:.1f}" y="{CH - 7}" class="dl" text-anchor="middle">{esc(fmt_short(fiso))}</text>'
        )

    svg = (
        f'<svg class="chart" viewBox="0 0 {CW} {CH}" preserveAspectRatio="none" '
        f'role="img" aria-label="Weight over time">'
        f'{grid}{line}{dots}{labels}</svg>'
    )
    return svg


EXTRA_CSS = '''
  .wcard {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 20px 14px;
  }
  .chart { width: 100%; height: 132px; display: block; overflow: visible; }
  .chart .g { stroke: rgba(255,255,255,0.10); stroke-width: 1; }
  .chart .ln { fill: none; stroke: var(--text); stroke-width: 2;
               stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
  .chart .pt { fill: var(--text); stroke: var(--bg-2); stroke-width: 2; }
  .chart .hit { fill: transparent; cursor: pointer; }
  .chart .vl { fill: var(--text); font-size: 12px; font-weight: 700;
               font-family: \'Helvetica Neue\', Helvetica, Arial, sans-serif; }
  .chart .dl { fill: var(--text-faint); font-size: 11px;
               font-family: \'Helvetica Neue\', Helvetica, Arial, sans-serif; }
  .chart .pt.on { r: 6; }

  .chartwrap { position: relative; }
  .tip {
    position: absolute;
    transform: translate(-50%, -100%);
    background: #ffffff;
    color: #0c0c0d;
    font-size: 13px;
    font-weight: 700;
    line-height: 1.25;
    padding: 6px 9px;
    border-radius: 7px;
    white-space: nowrap;
    pointer-events: none;
    z-index: 2;
  }
  .tip[hidden] { display: none; }
  .tip .tip-d { display: block; font-weight: 400; color: rgba(12,12,13,0.62); font-size: 11px; }

  .readout { font-size: 13px; color: var(--text-dim); margin-top: 10px; min-height: 18px; }
  .hint { font-size: 13px; color: var(--text-faint); margin-bottom: 14px; }
'''

TAP_JS = '''
<script>
document.querySelectorAll('.chartwrap').forEach(function (wrap) {
  var svg = wrap.querySelector('.chart');
  var tip = wrap.querySelector('.tip');
  var out = wrap.parentElement.querySelector('.readout');

  function show(hit) {
    var dot = hit.previousElementSibling;
    svg.querySelectorAll('.pt').forEach(function (p) { p.classList.remove('on'); });
    dot.classList.add('on');

    tip.innerHTML = '';
    var w = document.createElement('span');
    w.textContent = hit.dataset.w + ' lbs';
    var d = document.createElement('span');
    d.className = 'tip-d';
    d.textContent = hit.dataset.date;
    tip.appendChild(w); tip.appendChild(d);
    tip.hidden = false;

    var wr = wrap.getBoundingClientRect();
    var hr = hit.getBoundingClientRect();
    var x = hr.left + hr.width / 2 - wr.left;
    var y = hr.top + hr.height / 2 - wr.top - 10;
    var half = tip.offsetWidth / 2;
    if (x - half < 0) x = half;
    if (x + half > wr.width) x = wr.width - half;
    tip.style.left = x + 'px';
    tip.style.top = y + 'px';

    if (out) out.textContent = hit.dataset.date + ' \\u00b7 ' + hit.dataset.w + ' lbs';
  }

  function hide() {
    tip.hidden = true;
    svg.querySelectorAll('.pt').forEach(function (p) { p.classList.remove('on'); });
  }

  svg.querySelectorAll('.hit').forEach(function (hit) {
    hit.addEventListener('mouseenter', function () { show(hit); });
    hit.addEventListener('click', function (e) { e.stopPropagation(); show(hit); });
  });
  svg.addEventListener('mouseleave', hide);
  document.addEventListener('click', function (e) {
    if (!wrap.contains(e.target)) hide();
  });
});
</script>
'''


def weight_slug(name):
    import re
    s = name.lower().strip()
    s = re.sub(r"[\u2019\']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") + "-weight"


def build_weight_page(name, entries, updated=None, slug=None):
    """One athlete, one page. entries: [(iso_date, lbs), ...]"""
    entries = sorted(entries, key=lambda e: e[0])
    slug = slug or weight_slug(name)
    updated = updated or fmt_long(entries[-1][0])

    base_url = "https://jackfrom3.github.io/mission-reports"
    page_url = f"{base_url}/{slug}.html"
    og_image = f"{base_url}/assets/og-{slug}.png"
    title = f"{name} — Weight"

    meta = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="Mission Performance SB weight tracking for {esc(name)}.">

<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="Mission Performance SB — weight over time.">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{page_url}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="Mission Performance SB — weight over time.">
<meta name="twitter:image" content="{og_image}">

<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@700;800&display=swap">
'''

    css = HEAD_CSS.replace("</style>", EXTRA_CSS + "</style>")

    body = f'''<div class="wrap">

  <div class="header">
    <img class="logo" src="{LOGO_SRC}" alt="Mission Performance SB" />
    <div class="name">{esc(name)}</div>
    <div class="meta">Weight &middot; updated {esc(updated)}</div>
  </div>

  <div class="section">
    <div class="section-label">Weight Over Time</div>
    <div class="hint">Tap or hover any point to see that date and weight.</div>
    <div class="wcard">
      <div class="chartwrap">
        {_chart_svg(entries)}
        <div class="tip" hidden></div>
      </div>
      <div class="readout" aria-live="polite"></div>
    </div>
  </div>

  <div class="footer">
    Mission Performance SB &nbsp;&middot;&nbsp; 135 E Carrillo St, Santa Barbara, CA &nbsp;&middot;&nbsp; jack@missionperformsb.com
  </div>

</div>
'''
    return meta + css + "\n</head>\n<body>\n" + body + TAP_JS + "\n</body>\n</html>\n"


def build_weight_og(name, slug=None):
    from PIL import Image, ImageDraw, ImageFont

    slug = slug or weight_slug(name)
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (12, 12, 13))
    draw = ImageDraw.Draw(img)

    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    top, mid, bot = (12, 12, 13), (24, 24, 26), (9, 9, 10)
    for y in range(H):
        t = y / H
        c = lerp(top, mid, t / 0.45) if t < 0.45 else lerp(mid, bot, (t - 0.45) / 0.55)
        draw.line([(0, y), (W, y)], fill=c)

    icon = Image.open(f"{ASSETS}/mountain_white_raw.png")
    icon_w = 130
    icon_h = int(icon.height * icon_w / icon.width)
    icon = icon.resize((icon_w, icon_h), Image.LANCZOS)
    img.paste(icon, (80, 70), icon)

    font_bold = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 58)
    font_reg = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 30)
    font_small = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", 26)

    draw.text((80, 190), "MISSION PERFORMANCE SB", font=font_small, fill=(255, 255, 255))
    draw.text((80, 240), f"{name} \u2014 Weight", font=font_bold, fill=(255, 255, 255))
    draw.text((80, 330), "Weight over time", font=font_reg, fill=(180, 180, 182))

    out_path = f"{REPO}/assets/og-{slug}.png"
    img.save(out_path)
    return out_path

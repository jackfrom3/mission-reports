"""Reusable generator for the mobile testing-report pages. Import and call build_page().

Usage from anywhere:
    import sys; sys.path.insert(0, "/Users/jackanderson/Desktop/Mission Performance SB/mission-reports/generator")
    from build_mobile_report import build_page, build_og_image, slugify
"""
import html as _html
import os

GEN_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(GEN_DIR)
ASSETS = f"{GEN_DIR}/assets"

with open(f"{GEN_DIR}/head_template.html") as f:
    HEAD_CSS = f.read()
with open(f"{ASSETS}/logo_src.txt") as f:
    LOGO_SRC = f.read().strip()


def esc(s):
    return _html.escape(str(s), quote=False)


def perf_row(cat, name, val, pct, note=None):
    pct_html = f'<span class="pct">{esc(pct)}</span>' if pct and pct != "—" else ""
    note_html = f'<div class="metric-note">{esc(note)}</div>' if note else ""
    return f'''    <div class="metric-card">
      <div class="metric-cat">{esc(cat)}</div>
      <div class="metric-name">{esc(name)}</div>
      {note_html}
      <div class="metric-value"><span class="val">{esc(val)}</span>{pct_html}</div>
    </div>
'''


def need_card(label, text):
    return f'''    <div class="need-card">
      <div class="need-label">{esc(label)}</div>
      <div class="need-text">{esc(text)}</div>
    </div>
'''


def coach_card(name, blurb, rating, note, flag):
    flag_cls = " flag" if flag else ""
    tag_html = '<div class="flag-tag">Focus area</div>' if flag else ""
    note_html = f'<div class="coach-note">{esc(note)}</div>' if note else ""
    return f'''    <div class="coach-card{flag_cls}">
      <div class="coach-name">{esc(name)}</div>
      <div class="coach-rating">{esc(rating)}</div>
      {tag_html}
      {note_html}
      <details class="coach-desc">
        <summary>What this measures</summary>
        <div class="desc-body">{esc(blurb)}</div>
      </details>
    </div>
'''


COACH_BLURBS = {
    "Effort / Attitude": "Work ethic and mindset in the gym",
    "Coachability": "How well the athlete takes and applies feedback",
    "Ownership": "Does the athlete drive their own training/habits?",
    "Recovery": "Sleep, nutrition, mobility",
}


def rating_is_flagged(rating_str):
    # rating_str like "3.5 / 5" or "— / 5"; flag if numeric and <= 2.5
    try:
        num = float(rating_str.split("/")[0].strip())
        return num <= 2.5
    except (ValueError, IndexError):
        return False


def gaps_flagged(gap_note):
    return "more than" in (gap_note or "").lower()


def build_body(data):
    perf_html = "".join(
        perf_row(r["cat"], r["name"], r["val"], r.get("pct"), r.get("note"))
        for r in data["performance_rows"]
    )
    needs_html = "".join(
        need_card(label, data["needs"][key])
        for label, key in [
            ("Mobility Need", "mobility"),
            ("Performance Need", "performance"),
            ("Lifestyle Need", "lifestyle"),
        ]
    )
    coach_html = "".join(
        coach_card(
            cat,
            COACH_BLURBS[cat],
            data["coach_eval"][cat]["rating"],
            data["coach_eval"][cat].get("note"),
            rating_is_flagged(data["coach_eval"][cat]["rating"]),
        )
        for cat in ["Effort / Attitude", "Coachability", "Ownership", "Recovery"]
    ) if data.get("coach_eval") else ""

    gflag = " flag" if gaps_flagged(data.get("gaps_note", "")) else ""

    blanked = data["sessions_attended"] == "—"
    if blanked:
        attendance_cards = f'''    <div class="card">
        <div class="card-label">Sessions Attended</div>
        <div class="card-number">—</div>
      </div>
      <div class="card">
        <div class="card-label">Gaps (10+ Days)</div>
        <div class="card-number">—</div>
      </div>'''
    else:
        attendance_cards = f'''    <div class="card">
        <div class="card-label">Sessions Attended</div>
        <div class="card-number">{esc(data["sessions_attended"])}</div>
        <div class="card-sub">{esc(data["sessions_rank"])}</div>
      </div>
      <div class="card{gflag}">
        <div class="card-label">Gaps (10+ Days)</div>
        <div class="card-number">{esc(data["gaps_count"])}</div>
        <div class="card-sub down">{esc(data["gaps_note"])}</div>
      </div>'''

    coach_section = f'''  <div class="section">
    <div class="section-label">Coach Evaluation</div>

{coach_html}  </div>

''' if data.get("coach_eval") else ""

    body = f'''<div class="wrap">

  <div class="header">
    <img class="logo" src="__LOGO__" alt="Mission Performance SB" />
    <div class="name">{esc(data["name"])}</div>
    <div class="meta">{esc(data["header_date"])}</div>
  </div>

  <div class="section">
    <div class="section-label">Attendance</div>
    <div class="attendance-period">{esc(data["attendance_period"])}</div>
    <div class="cards">
{attendance_cards}
    </div>
  </div>

  <div class="section">
    <div class="section-label">Performance</div>
{perf_html}  </div>

  <div class="section">
    <div class="section-label">Needs</div>
{needs_html}  </div>

{coach_section}  <div class="footer">
    Mission Performance SB &nbsp;&middot;&nbsp; 135 E Carrillo St, Santa Barbara, CA &nbsp;&middot;&nbsp; jack@missionperformsb.com
  </div>

</div>
'''
    return body.replace("__LOGO__", LOGO_SRC)


def build_page(data, slug):
    base_url = "https://jackfrom3.github.io/mission-reports"
    page_url = f"{base_url}/{slug}.html"
    og_image = f"{base_url}/assets/og-{slug}.png"
    title = f"{data['name']}'s Testing Report"

    meta = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="Mission Performance SB performance report for {esc(data['name'])}.">

<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="Mission Performance SB — Attendance, Performance, and Coach Evaluation.">
<meta property="og:image" content="{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{page_url}">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="Mission Performance SB — Attendance, Performance, and Coach Evaluation.">
<meta name="twitter:image" content="{og_image}">

<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="favicon-192.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@700;800&display=swap">
'''
    body = build_body(data)
    full = meta + HEAD_CSS + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n"
    return full


def build_og_image(name, slug):
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (12, 12, 13))
    draw = ImageDraw.Draw(img)

    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    top = (12, 12, 13)
    mid = (24, 24, 26)
    bot = (9, 9, 10)
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
    title = f"{name}'s Testing Report"
    draw.text((80, 240), title, font=font_bold, fill=(255, 255, 255))
    draw.text((80, 330), "Attendance · Performance · Coach Evaluation", font=font_reg, fill=(180, 180, 182))

    out_path = f"{REPO}/assets/og-{slug}.png"
    img.save(out_path)
    return out_path


def slugify(name):
    import re
    s = name.lower().strip()
    s = re.sub(r"[’']", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

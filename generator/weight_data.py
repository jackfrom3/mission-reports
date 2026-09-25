"""Persistent weigh-in history + page rebuilder.

The full history lives in `generator/weight_data.json` and is committed to the
repo. New sheets are ADDED to it — pages are never rebuilt from a hand-typed
list again.

Typical session after Jack photographs a new sheet:

    import sys; sys.path.insert(0, "/Users/jackanderson/Desktop/Mission Performance SB/mission-reports/generator")
    from weight_data import add_entries, rebuild_all, summary

    add_entries("Rudy Blue", [("2026-09-28", 161.4)])
    add_entries("Kash Ridgell", [("2026-09-28", 155.0)])
    rebuild_all()          # regenerates every athlete's page + OG card

Or from the shell:

    python3 generator/weight_data.py summary
    python3 generator/weight_data.py add "Rudy Blue" 2026-09-28 161.4
    python3 generator/weight_data.py rebuild

Rules:
- An exact (date, weight) duplicate is skipped, so re-transcribing the same
  sheet twice is harmless.
- The same date with a DIFFERENT weight is reported as a conflict and NOT
  written — that's either a correction or a second weigh-in, and it needs a
  human call. Use `replace_entry()` to overwrite deliberately.
"""
import json
import os
import sys

GEN_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(GEN_DIR)
DATA_PATH = f"{GEN_DIR}/weight_data.json"


def load_data():
    if not os.path.exists(DATA_PATH):
        return {"athletes": {}, "notes": []}
    with open(DATA_PATH) as f:
        return json.load(f)


def save_data(data):
    for name in data["athletes"]:
        data["athletes"][name].sort(key=lambda e: e[0])
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def add_entries(name, entries, data=None):
    """entries: [(iso_date, lbs), ...]. Returns (added, duplicates, conflicts)."""
    own = data is None
    data = data or load_data()
    cur = data["athletes"].setdefault(name, [])
    by_date = {d: w for d, w in cur}

    added, dupes, conflicts = [], [], []
    for d, w in entries:
        w = float(w)
        if d in by_date:
            if by_date[d] == w:
                dupes.append((d, w))
            else:
                conflicts.append((d, by_date[d], w))
            continue
        cur.append([d, w])
        by_date[d] = w
        added.append((d, w))

    if own:
        save_data(data)
    for d, old, new in conflicts:
        print(f"  ! CONFLICT {name} {d}: have {old}, got {new} — not written "
              f"(use replace_entry to overwrite)")
    return added, dupes, conflicts


def replace_entry(name, iso_date, weight):
    """Deliberately overwrite the weight on an existing date."""
    data = load_data()
    rows = data["athletes"].get(name, [])
    for row in rows:
        if row[0] == iso_date:
            old, row[1] = row[1], float(weight)
            save_data(data)
            return old
    raise KeyError(f"{name} has no entry on {iso_date}")


def remove_athlete(name):
    data = load_data()
    data["athletes"].pop(name, None)
    save_data(data)


def rebuild_all(updated=None, only=None):
    """Regenerate every athlete's page (and OG card) from stored history."""
    sys.path.insert(0, GEN_DIR)
    from build_weight_page import build_weight_page, build_weight_og, weight_slug

    data = load_data()
    built = []
    for name, rows in sorted(data["athletes"].items()):
        if only and name not in only:
            continue
        if not rows:
            continue
        entries = [(d, w) for d, w in rows]
        slug = weight_slug(name)
        with open(f"{REPO}/{slug}.html", "w") as f:
            f.write(build_weight_page(name, entries, updated=updated))
        build_weight_og(name, slug)
        built.append((name, slug, len(entries)))
    return built


def summary():
    data = load_data()
    rows = []
    for name, e in sorted(data["athletes"].items()):
        if not e:
            rows.append((name, 0, "—", "—"))
            continue
        e = sorted(e, key=lambda r: r[0])
        rows.append((name, len(e), f"{e[0][0]} {e[0][1]:g}", f"{e[-1][0]} {e[-1][1]:g}"))
    return rows


def _main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "summary":
        for name, n, first, last in summary():
            print(f"{name:22} {n:>2} weigh-ins   first {first:>18}   last {last:>18}")
    elif cmd == "add":
        name, d, w = sys.argv[2], sys.argv[3], sys.argv[4]
        added, dupes, conflicts = add_entries(name, [(d, w)])
        print(f"added={added} duplicates={dupes} conflicts={len(conflicts)}")
    elif cmd == "rebuild":
        for name, slug, n in rebuild_all():
            print(f"{slug}.html  ({n} pts)  {name}")
    else:
        print(f"unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    _main()

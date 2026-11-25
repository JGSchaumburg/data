"""Pull the Pennsylvania transit projects (SEPTA) out of DVRPC's long-range plan, with costs.

Usage (needs `pdftotext` from poppler):
    python build.py OUTPUT_CSV [CACHE_DIR]

Sources:
    DVRPC, Update: Connections 2050 Long-Range Plan, Appendices (May 2026),
        https://www.dvrpc.org/Reports/25140.pdf, Appendix F, Financial Plan:
        Table F-25 "Pennsylvania Transit MRPs, Funded" (PDF pp. 251-256), millions of
        year-of-expenditure dollars, and the transit rows of Table F-30 "Pennsylvania MRPs,
        Unfunded" (PDF pp. 271-277), millions of 2025 dollars.
    DVRPC, Connections 2050 Amendment 1 (adopted September 2026),
        https://www.dvrpc.org/Reports/26140.pdf, Table 5 "Revised Major Regional Transit
        Projects", which updates six funded SEPTA costs from SEPTA's FY27 capital budget.

Every row is a Major Regional Project (MRP) with an ID beginning PAT. Rows are read from the PDF
text layout; the check at the end fails loudly if the counts change.
"""
import csv
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

APPENDIX = "https://www.dvrpc.org/Reports/25140.pdf"
AMENDMENT = "https://www.dvrpc.org/Reports/26140.pdf"
FUNDED_PAGES, UNFUNDED_PAGES = (251, 256), (271, 277)
EXPECT = {"funded": 39, "unfunded": 45, "amended": 6}


def fetch(url, cache):
    path = Path(cache) / url.rsplit("/", 1)[1]
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req).read())
    return path


def text(pdf, first=None, last=None):
    args = ["pdftotext", "-layout"] + (["-f", str(first), "-l", str(last)] if first else []) + [str(pdf), "-"]
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.split("\n")


STOP = ("Source", "Table", "F-", "Unfunded", "DELAWARE", "MRP ID")


def rows(lines, table, basis):
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)(PAT\d{3})(\s+)", line)
        cost = re.search(r"\$\s?([\d,]+\.\d)", line)
        if not (m and cost):
            i += 1
            continue
        fac0 = m.end()
        sc0 = fac0 + re.search(r"\S(\s{2,})\S", line[fac0:]).end() - 1
        segs = [s.start() for s in re.finditer(r"\S+(?: \S+)*", line)]
        loc0 = next((p for p in segs if sc0 + 40 <= p < cost.start()), cost.start())
        fac, scope, loc = [line[fac0:sc0]], [line[sc0:loc0]], [line[loc0:cost.start()]]
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r"^\s*PA[TR]\d{3}", lines[j]) \
                and not lines[j].strip().startswith(STOP):
            t = lines[j]
            fac.append(t[fac0:sc0]); scope.append(t[sc0:loc0]); loc.append(t[loc0:cost.start()])
            j += 1
        clean = lambda parts: " ".join(p.strip() for p in parts if p.strip() and not re.fullmatch(r"[\d–-]+", p.strip()))
        # the plan-period column (e.g. "1–2") sits beside the location in the layout; drop it
        location = re.sub(r"\s+", " ", re.sub(r"(?<!\S)\d(?:[–-]\d)?(?!\S)", " ", clean(loc))).strip()
        out.append(dict(table=table, mrp_id=m.group(2), facility=clean(fac), scope=clean(scope),
                        location=location, cost_millions=cost.group(1).replace(",", ""), dollar_basis=basis))
        i = j
    return out


def amendments(lines):
    # the last match is the table itself; earlier ones are the table of contents
    start = [i for i, l in enumerate(lines) if l.strip().startswith("Table 5: Revised Major Regional Transit")][-1]
    out = {}
    for i in range(start, min(start + 80, len(lines))):
        m = re.search(r"(PAT\d{3})\s+(.+?)\s{2,}(.+?)\s{2,}\$\s?([\d,]+\.\d)", lines[i])
        if m:
            note = [m.group(3).strip()]
            col = lines[i].find(m.group(3))
            for t in lines[i + 1:i + 20]:
                if re.search(r"PAT\d{3}", t) or t.strip().startswith(("Source", "Table", "Updates to transit")):
                    break
                if re.search(r"MRP ID|YOE|Categories|UPDATE:", t):
                    continue  # repeated header at a page break
                indent = len(t) - len(t.lstrip())
                # after a page break the column sits further right, alone on its line
                piece = t.strip() if indent >= col else (t[col:col + 45].strip() if len(t) > col else "")
                if piece:
                    note.append(piece)
            out[m.group(1)] = (m.group(4).replace(",", ""), " ".join(note))
    return out


def main(out_csv, cache=None):
    cache = cache or tempfile.mkdtemp()
    app, amd = fetch(APPENDIX, cache), fetch(AMENDMENT, cache)
    funded = rows(text(app, *FUNDED_PAGES), "F-25 funded", "year of expenditure")
    unfunded_lines = text(app, *UNFUNDED_PAGES)
    unfunded = rows(unfunded_lines, "F-30 unfunded", "2025 dollars")
    amended = amendments(text(amd))
    got = {"funded": len(funded), "unfunded": len(unfunded), "amended": len(amended)}
    if got != EXPECT:
        raise SystemExit(f"row counts changed: {got} (expected {EXPECT}); check the PDF layout")
    for r in funded + unfunded:
        a = amended.get(r["mrp_id"]) if r["table"] == "F-25 funded" else None
        r["amendment1_cost_millions"] = a[0] if a else ""
        r["amendment1_note"] = a[1] if a else ""
        r["current_cost_millions"] = a[0] if a else r["cost_millions"]
    cols = ["table", "mrp_id", "facility", "scope", "location", "cost_millions", "amendment1_cost_millions",
            "amendment1_note", "current_cost_millions", "dollar_basis"]
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(funded + unfunded)
    print(got)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)

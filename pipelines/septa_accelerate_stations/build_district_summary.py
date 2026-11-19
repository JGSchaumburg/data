"""Summarize the Accelerate station data by PA House, PA Senate and Philadelphia Council district.

Usage:
    python build_district_summary.py OUTPUT_CSV

Reads only files already in this repo (no downloads), relative to the repo root:
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv
    datasets/septa-region/septa-accelerate-station-service/septa-accelerate-trolley-stops-by-district.csv
    datasets/septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv
        (Weekday_Total_Boards, matched on stop_id)
    datasets/pennsylvania/legislators-2025-2026/records/
    datasets/pennsylvania/election-2026-results/records/
    datasets/pennsylvania/transportation-votes/member-votes.csv
        (HB 1788 House final passage, Aug 11 2025; HB 257 Senate final passage, Aug 12 2025)

Run build.py first; this script reads its output.

Counts only. Nothing is scored or ranked.
"""

import csv
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets"
OUT_DIR = D / "septa-region/septa-accelerate-station-service"

# The transit funding final passage vote in each chamber, 2025-26 session.
FUNDING_VOTE = {"house": "hb1788-final", "senate": "hb257-final"}

COLUMNS = [
    "chamber", "district",
    "member_2025_26", "party_2025_26", "seat_2026_status", "winner_2026", "winner_party_2026",
    "transit_funding_vote_bill", "transit_funding_vote_2025_26",
    "regional_rail_stations", "rr_15_min", "rr_30_min", "rr_60_min", "rr_frequency_not_specified",
    "rr_15_min_inferred",
    "metro_stations", "accessibility_rebuilds", "accessible_today_unknown",
    "trolley_routes", "trolley_stops",
    "fy27_named_projects",
    "rr_weekday_boardings", "rr_weekday_boardings_at_15_min_stations", "rr_stations_without_boardings",
    "near_boundary_stations",
]


def records(path):
    return {p.stem: tomllib.loads(p.read_text()) for p in sorted(path.glob("*.toml"))}


def main(out_path):
    stations = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-stations.csv", encoding="utf-8")))
    trolley = list(csv.DictReader(open(OUT_DIR / "septa-accelerate-trolley-stops-by-district.csv", encoding="utf-8")))

    # SEPTA's station layer has one row per station per line; North Philadelphia appears twice with the
    # same count, so take the max per stop_id rather than summing.
    boards = {}
    for r in csv.DictReader(open(D / "septa-region/septa-regional-rail-stations/septa-regional-rail-stations.csv", encoding="utf-8")):
        v = r["Weekday_Total_Boards"].strip()
        if v:
            boards[r["Stop_ID"]] = max(boards.get(r["Stop_ID"], 0), int(float(v)))

    legs = {ch: records(D / f"pennsylvania/legislators-2025-2026/records/{ch}") for ch in ("house", "senate")}
    results = {ch: records(D / f"pennsylvania/election-2026-results/records/{ch}") for ch in ("house", "senate")}
    votes = {ch: {} for ch in FUNDING_VOTE}
    for r in csv.DictReader(open(D / "pennsylvania/transportation-votes/member-votes.csv", encoding="utf-8")):
        if FUNDING_VOTE.get(r["chamber"]) == r["vote_key"]:
            votes[r["chamber"]][r["district"]] = r

    rows = defaultdict(lambda: defaultdict(int))
    routes = defaultdict(set)
    projects = defaultdict(set)

    for s in stations:
        rr = s["mode"] == "Regional Rail"
        for ch in ("house", "senate", "council"):
            d = s[f"{ch}_district"]
            if not d:
                continue
            row = rows[(ch, d)]
            if rr:
                row["regional_rail_stations"] += 1
                f = s["proposed_frequency_minutes"]
                if f:
                    row[f"rr_{f}_min"] += 1
                else:
                    row["rr_frequency_not_specified"] += 1
                if f == "15" and s["frequency_basis"] == "inferred_between_terminals":
                    row["rr_15_min_inferred"] += 1
                if s["stop_id"] in boards:
                    row["rr_weekday_boardings"] += boards[s["stop_id"]]
                    if f == "15":
                        row["rr_weekday_boardings_at_15_min_stations"] += boards[s["stop_id"]]
                else:
                    row["rr_stations_without_boardings"] += 1
            else:
                row["metro_stations"] += 1
            if s["accessibility_rebuild_proposed"] == "true":
                row["accessibility_rebuilds"] += 1
            if s["accessible_today"] == "unknown":
                row["accessible_today_unknown"] += 1
            if s[f"{ch}_near_boundary"] == "true":
                row["near_boundary_stations"] += 1
            for p in filter(None, (x.strip() for x in s["fy27_named_projects"].split(";"))):
                projects[(ch, d)].add(p)

    for t in trolley:
        key = (t["chamber"], t["district"])
        rows[key]["trolley_stops"] += int(t["stop_count"])
        routes[key].add(t["route"])

    out = []
    for (ch, d), counts in rows.items():
        row = {c: counts.get(c, 0) for c in COLUMNS}
        row.update(chamber=ch, district=d,
                   trolley_routes="; ".join(sorted(routes[(ch, d)])),
                   fy27_named_projects=len(projects[(ch, d)]))
        for c in ("member_2025_26", "party_2025_26", "seat_2026_status", "winner_2026", "winner_party_2026",
                  "transit_funding_vote_bill", "transit_funding_vote_2025_26"):
            row[c] = ""
        if ch in legs:
            m, f, v = legs[ch].get(d), results[ch].get(d), votes[ch].get(d)
            row["member_2025_26"] = m["full_name"] if m else ""
            row["party_2025_26"] = m["party"] if m else ""
            row["seat_2026_status"] = f["outcome"] if f else "not_up"
            row["winner_2026"] = f.get("winner", "") if f else ""
            row["winner_party_2026"] = f.get("winner_party", "") if f else ""
            row["transit_funding_vote_bill"] = v["bill"] if v else ""
            row["transit_funding_vote_2025_26"] = v["vote"] if v else ""
        out.append(row)

    order = {"house": 0, "senate": 1, "council": 2}
    out.sort(key=lambda r: (order[r["chamber"]], int(r["district"])))
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} district rows -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else OUT_DIR / "septa-accelerate-district-summary.csv")

"""Check the districts computed for Metro stations (and the few Regional Rail stops not in the repo's
Regional Rail districts file) against the Census Bureau's geocoder.

Usage: python check_with_census_geocoder.py OUTPUT.csv

For each row of septa-accelerate-stations.csv with district_source = point_in_polygon, sends the
station's coordinates to the Census geocoder (public, no key) and compares the State House and
Senate districts it returns. Regional Rail rows taken from regional-rail-station-districts.csv were
already checked by that dataset's own script. About 0.2 s per request. Standard library only.
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATIONS = ROOT / "datasets/septa-region/septa-accelerate-station-service/septa-accelerate-stations.csv"
API = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates?"
LOWER, UPPER = "2026 State Legislative Districts - Lower", "2026 State Legislative Districts - Upper"


def main(out):
    rows = []
    for s in csv.DictReader(open(STATIONS)):
        if s["district_source"] != "point_in_polygon":
            continue
        q = urllib.parse.urlencode({"x": s["longitude"], "y": s["latitude"], "benchmark": "Public_AR_Current",
                                    "vintage": "Current_Current", "layers": "all", "format": "json"})
        r = {"mode": s["mode"], "line": s["line"], "station": s["station"], "our_house": s["house_district"], "our_senate": s["senate_district"],
             "near_house_edge": s["house_near_boundary"], "near_senate_edge": s["senate_near_boundary"],
             "census_house": "", "census_senate": "", "result": ""}
        try:
            g = json.load(urllib.request.urlopen(API + q, timeout=30))["result"]["geographies"]
            r["census_house"] = g[LOWER][0]["BASENAME"] if g.get(LOWER) else ""
            r["census_senate"] = g[UPPER][0]["BASENAME"] if g.get(UPPER) else ""
            r["result"] = "agree" if (r["census_house"], r["census_senate"]) == (r["our_house"], r["our_senate"]) else "differs"
        except Exception as e:
            r["result"] = f"error: {str(e)[:50]}"
        rows.append(r)
        time.sleep(0.2)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}; {sum(r['result'] == 'differs' for r in rows)} differ")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

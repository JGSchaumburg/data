"""Place every SEPTA bus route in legislative and council districts, with how often it runs.

Usage (needs geopandas; run build.py first so the GTFS download is cached):
    python build_bus_routes.py OUTPUT_DIR [CACHE_DIR]

Sources:
    SEPTA GTFS release v202611010 (schedule starting 2026-11-01): routes, trips, stop_times,
        calendars and shapes from google_bus.zip.
    Census TIGER/Line 2024 House and Senate districts and Philadelphia Council Districts 2024,
        through the helpers in build.py.
    SEPTA's frequent network: GTFS `route_color` EF3340 ("Frequent Red"). SEPTA's maps-and-signs
        page defines red routes as arriving "every 15 minutes or better from 6 am to 9 pm weekdays"
        (https://wwww.septa.org/initiatives/bus/maps-signs/). This is the weekday network running
        now (25 routes), not the 29 routes "every 15 minutes or better, 7 days a week" that the
        Accelerate plan counts for the full New Bus Network (phases through 2027). SEPTA has not
        published which routes make up the 29.

Frequency is measured, not taken from SEPTA's labels: for each route and direction, the trips
that start between 7:00 and 19:00 on Wednesday 2026-11-18, Saturday 2026-11-21 and Sunday
2026-11-22. `*_avg_headway_min` is 720 minutes divided by those trips, taking the less frequent
direction. `*_max_gap_min` is the longest wait in that window, counting from 7:00 to the first
trip and from the last trip to 19:00.

Writes to OUTPUT_DIR:
    septa-bus-routes.csv    one row per GTFS bus route (trolley, Metro and shuttle routes left out)
"""
import csv
import importlib.util
import io
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("accelerate_build", HERE / "build.py")
ab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab)

DAYS = {"wed": ("20261118", "wednesday"), "sat": ("20261121", "saturday"), "sun": ("20261122", "sunday")}
WINDOW = (7 * 3600, 19 * 3600)
NOT_BUS = {"L1", "B1", "B2", "B3", "M1", "T1", "T2", "T3", "T4", "T5", "D1", "D2", "G1"}
FREQUENT_RED = "EF3340"  # SEPTA's "Frequent Red" route color
BUS_TYPES = {"3", "11"}  # bus and trackless trolley (Routes 59, 66, 75)
CHAMBERS = ("house", "senate", "council")


def seconds(hms):
    h, m, s = map(int, hms.split(":"))
    return h * 3600 + m * 60 + s


def main(out_dir, cache_dir=None):
    cache_dir = cache_dir or tempfile.mkdtemp()
    outer = zipfile.ZipFile(ab.fetch(f"septa_gtfs_{ab.GTFS_TAG}.zip", ab.GTFS_URL, cache_dir))
    inner = zipfile.ZipFile(io.BytesIO(outer.read("google_bus.zip")))
    read = lambda f: csv.DictReader(io.TextIOWrapper(inner.open(f"{f}.txt"), encoding="utf-8-sig"))

    cal, cdates = list(read("calendar")), list(read("calendar_dates"))
    active = {}
    for k, (date, dow) in DAYS.items():
        s = {c["service_id"] for c in cal if c[dow] == "1" and c["start_date"] <= date <= c["end_date"]}
        for x in cdates:
            if x["date"] == date:
                (s.add if x["exception_type"] == "1" else s.discard)(x["service_id"])
        active[k] = s

    routes = {r["route_id"]: r for r in read("routes") if r["route_id"] not in NOT_BUS and r["route_type"] in BUS_TYPES}
    trips = {t["trip_id"]: t for t in read("trips") if t["route_id"] in routes}
    first = {}
    for st in read("stop_times"):
        tid = st["trip_id"]
        if tid in trips:
            seq = int(st["stop_sequence"])
            if tid not in first or seq < first[tid][0]:
                first[tid] = (seq, seconds(st["departure_time"]))
    starts = defaultdict(list)
    for tid, (_, dep) in first.items():
        t = trips[tid]
        for k in DAYS:
            if t["service_id"] in active[k]:
                starts[(t["route_id"], t["direction_id"], k)].append(dep)

    shape_ids = defaultdict(set)
    for t in trips.values():
        shape_ids[t["route_id"]].add(t["shape_id"])
    wanted = set().union(*shape_ids.values())
    pts = defaultdict(list)
    for s in read("shapes"):
        if s["shape_id"] in wanted:
            pts[s["shape_id"]].append((int(s["shape_pt_sequence"]), float(s["shape_pt_lon"]), float(s["shape_pt_lat"])))

    places = ab.Places(cache_dir)
    rows = []
    for rid in sorted(routes, key=lambda r: (not r.isdigit(), int(r) if r.isdigit() else 0, r)):
        r = routes[rid]
        row = dict(route=r["route_short_name"] or rid, name=r["route_long_name"])
        for k in DAYS:
            avg = gap = None
            for d in ("0", "1"):
                xs = sorted(x for x in starts.get((rid, d, k), []) if WINDOW[0] <= x < WINDOW[1])
                if len(xs) < 2:
                    avg = gap = None
                    break
                gaps = [xs[0] - WINDOW[0]] + [b - a for a, b in zip(xs, xs[1:])] + [WINDOW[1] - xs[-1]]
                a, g = 720 / len(xs), max(gaps) / 60
                avg, gap = (a, g) if avg is None else (max(avg, a), max(gap, g))
            row[f"{k}_avg_headway_min"] = f"{avg:.1f}" if avg is not None else ""
            row[f"{k}_max_gap_min"] = f"{gap:.1f}" if gap is not None else ""
        row["septa_frequent_weekday"] = str(r["route_color"].upper() == FREQUENT_RED).lower()
        lines = [LineString([(x, y) for _, x, y in sorted(pts[s])]) for s in sorted(shape_ids[rid]) if len(pts[s]) > 1]
        if lines:
            g = gpd.GeoDataFrame(geometry=[MultiLineString(lines)], crs="EPSG:4326").to_crs(ab.PROJ)
            for ch in CHAMBERS:
                j = gpd.sjoin(g, places.layers[ch], how="inner", predicate="intersects")
                row[f"{ch}_districts"] = "; ".join(sorted(set(j["district"].astype(str)), key=lambda d: (len(d), d)))
        else:
            for ch in CHAMBERS:
                row[f"{ch}_districts"] = ""
        rows.append(row)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ab.write(out / "septa-bus-routes.csv", rows, list(rows[0].keys()))
    print("bus routes:", len(rows))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)

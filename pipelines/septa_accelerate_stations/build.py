"""Place the stations and trolley routes in SEPTA's Accelerate plan in legislative and council districts.

Usage (needs geopandas):
    python build.py OUTPUT_DIR [CACHE_DIR]

Sources:
    SEPTA Accelerate plan and county fact sheets, November 2026 (https://www.septa.org/accelerate/).
        Read by hand; the service tiers and trolley proposals below are typed in from them, with
        the page each one comes from.
    SEPTA GTFS release v202611010 (https://github.com/septadev/GTFS/releases/tag/v202611010):
        station and stop locations, line order, wheelchair_boarding.
    City of Philadelphia, Council Districts 2024 (ArcGIS layer behind OpenDataPhilly):
        Council district polygons.
    Census TIGER/Line 2024 House, Senate, county and county subdivision polygons, through the
        helpers in ../regional_rail_station_districts/build.py.
Downloads go to CACHE_DIR if given (and are reused from there), otherwise to a temporary folder.

Reads, relative to the repo root:
    datasets/septa-region/regional-rail-station-districts/regional-rail-station-districts.csv
        (county, municipality, House and Senate district for every Regional Rail station it has;
        those are used as they are, not recomputed)
    datasets/pennsylvania/legislators-2025-2026/records/{house,senate}/*.toml
    datasets/pennsylvania/election-2026-results/records/{house,senate}/*.toml
    analyses/septa-capital-tip-tracker/data/septa_fy27_capital_projects.csv
        (total project cost of the named FY27 station projects)

Writes to OUTPUT_DIR:
    septa-accelerate-stations.csv                   one row per Regional Rail and Metro station
    septa-accelerate-trolley-routes.csv             one row per trolley route
    septa-accelerate-trolley-stops-by-district.csv  trolley stops counted by route, chamber and district
    fy27-named-station-projects.csv                 the named FY27 projects and the stations they are attached to
"""
import csv
import io
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "regional_rail_station_districts"))
from build import NEAR_M, PROJ, records, tiger_districts, tiger_places  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "datasets"

GTFS_TAG = "v202611010"
GTFS_URL = f"https://github.com/septadev/GTFS/releases/download/{GTFS_TAG}/gtfs_public.zip"
COUNCIL_URL = (
    "https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Council_Districts_2024/FeatureServer/0/query"
    "?where=1%3D1&outFields=district&outSR=4326&f=geojson"
)

# Page references. The full plan PDF is laid out in two-page spreads, so plan pages are given as the printed
# numbers of the spread. Fact sheet pages are 1 or 2.
PLAN = "Accelerate plan"
PHL, BUCKS, CHESTER, DELCO, MONTCO = (f"{c} fact sheet" for c in ("Philadelphia", "Bucks County", "Chester County", "Delaware County", "Montgomery County"))

# ---------------------------------------------------------------------------------------------
# Regional Rail service tiers, typed in from the county fact sheets.
# For each GTFS route: the terminals the plan names, ordered from Center City outward, with the
# frequency the plan proposes to that terminal ("15-minute", "30-minute or better", "60-minute or
# better"). A station between Center City and a named terminal is assumed to get that terminal's
# tier. A station past the last named terminal is left as not specified. Chestnut Hill West and
# Cynwyd are not named anywhere in the plan's service text.
# ---------------------------------------------------------------------------------------------
RULES = {
    # Philadelphia p. 2: "all-day, 15-minute Regional Rail service between Center City and Airport,
    # Wawa, Paoli, Norristown, Chestnut Hill East, and Fox Chase Stations". Same list in the plan, pp. 9-10.
    "AIR": [("Airport Terminals E & F", 15, f"{PHL} p. 2; {PLAN} pp. 9-10")],
    "CHE": [("Chestnut Hill East", 15, f"{PHL} p. 2; {PLAN} pp. 9-10")],
    "FOX": [("Fox Chase", 15, f"{PHL} p. 2; {PLAN} pp. 9-10")],
    "MED": [("Wawa", 15, f"{PHL} p. 2; {DELCO} p. 1; {PLAN} pp. 9-10")],
    "NOR": [("Norristown Elm Street", 15, f"{PHL} p. 2; {MONTCO} p. 1; {PLAN} pp. 9-10")],
    # Chester p. 1: 15-minute "to destinations like Paoli Station"; "60-minute or better service to Thorndale".
    "PAO": [("Paoli", 15, f"{PHL} p. 2; {CHESTER} p. 1; {DELCO} p. 1; {MONTCO} p. 1"),
            ("Thorndale", 60, f"{CHESTER} p. 1")],
    # Montgomery p. 1: 15-minute service "first to Jenkintown"; "30-minute service to Lansdale, Warminster,
    # and Neshaminy Stations". Bucks p. 1: "30-minute or better ... to Bristol, Neshaminy, Warminster, and
    # Lansdale"; "60-minute or better service to Trenton, West Trenton, and Doylestown".
    "LAN": [("Jenkintown-Wyncote", 15, f"{MONTCO} p. 1"),
            ("Lansdale", 30, f"{MONTCO} p. 1; {BUCKS} p. 1"),
            ("Doylestown", 60, f"{BUCKS} p. 1")],
    "WAR": [("Jenkintown-Wyncote", 15, f"{MONTCO} p. 1"),
            ("Warminster", 30, f"{MONTCO} p. 1; {BUCKS} p. 1")],
    "WTR": [("Jenkintown-Wyncote", 15, f"{MONTCO} p. 1"),
            ("Neshaminy Falls", 30, f"{MONTCO} p. 1; {BUCKS} p. 1"),  # the plan says "Neshaminy"
            ("West Trenton", 60, f"{BUCKS} p. 1")],
    "TRE": [("Bristol", 30, f"{BUCKS} p. 1"),
            ("Trenton Transit Center", 60, f"{BUCKS} p. 1")],
    # Delaware p. 1: "30-minute or better service to Marcus Hook with hourly service to Newark, DE".
    "WIL": [("Marcus Hook", 30, f"{DELCO} p. 1"),
            ("Newark DE", 60, f"{DELCO} p. 1")],
    "CHW": [],
    "CYN": [],
}
CENTER_CITY = "Suburban Station"  # distance along each line is counted from here

# Chester p. 1-2: "reinstated service to Coatesville". No frequency is given, and there is no GTFS stop.
# Location is the existing Amtrak station, approximate.
COATESVILLE = dict(station="Coatesville (proposed reinstated service)", latitude=39.9832, longitude=-75.8240,
                   source=f"{CHESTER} pp. 1-2")

# ---------------------------------------------------------------------------------------------
# Metro. Every Regional Rail and Metro station is proposed to be fully accessible:
# Regional Rail, "high-level platforms and fully accessible entries at every Regional Rail station"
# (plan pp. 9-10; also pp. 55-56); Metro, "a fully accessible Metro is the result of generational efforts to
# rebuild every station" (plan pp. 7-8; also pp. 57-58). The plan gives no station-level Metro frequency;
# line-level statements are in the README.
# ---------------------------------------------------------------------------------------------
METRO = {  # GTFS route_id: (line letter, line name)
    "L1": ("L", "Market-Frankford Line (L)"),
    "B1": ("B", "Broad Street Line (B)"),
    "B3": ("B", "Broad-Ridge Spur (B)"),
    "M1": ("M", "Norristown High Speed Line (M)"),
}
# 11th St (L) is listed in route_stops.txt but missing from stops.txt in this release, and has no
# scheduled stops. Location taken from the GTFS bus stop "Market St & 11th St" (stop 10258). Marked not
# accessible because the FY2027 capital budget (p. 292) describes its project as making it "fully ADA accessible".
ELEVENTH_ST = dict(stop_name="11th St", stop_lat="39.951782", stop_lon="-75.158109", wheelchair_boarding="2")

# ---------------------------------------------------------------------------------------------
# Named station projects in SEPTA's FY2027 capital budget, matched by project name to
# analyses/septa-capital-tip-tracker/data/septa_fy27_capital_projects.csv. These are related budget
# items, not a list of what Accelerate funds. A project that covers more than one station is attached
# to each, with its full cost on each row. Pages are in the FY2027 Operating and Capital Budget Proposal.
# ---------------------------------------------------------------------------------------------
CAPITAL = [  # (capital budget project name, [(mode, station)], budget page)
    ("Cornwells Heights Station Reconfiguration on the Trenton Line", [("RR", "Cornwells Heights")], 291),
    ("Jenkintown-Wyncote Station on the Regional Rail Mainline", [("RR", "Jenkintown-Wyncote")], 286),
    ("Ardmore Transportation Center on the Paoli/Thorndale Line", [("RR", "Ardmore")], 283),
    ("Villanova Station on the Paoli/Thorndale Regional Rail Line", [("RR", "Villanova")], 284),
    ("Chestnut Hill East Station on the Chestnut Hill East Line", [("RR", "Chestnut Hill East")], 285),
    ("Noble Station on the West Trenton Line", [("RR", "Noble")], 287),
    ("Swarthmore Station on the Media/Elwyn Regional Rail Line", [("RR", "Swarthmore")], 289),
    ("Bristol Station Improvements", [("RR", "Bristol")], 290),
    ("Conshohocken Station Parking", [("RR", "Conshohocken")], 282),
    ("Jefferson Station Escalators", [("RR", "Jefferson Station")], 274),
    # 30th Street Station to Suburban Station; attached to both ends.
    ("Mainline–Schuylkill Bridges and Interlockings (30th Street Station to Suburban Station)",
     [("RR", "Gray 30th St Station"), ("RR", "Suburban Station")], 199),
    # The budget page says it serves the Fern Rock Regional Rail station and the B transfer.
    ("Fern Rock Transportation Center Safety Improvements", [("RR", "Fern Rock Transit Center"), ("B", "Fern Rock Transit Center")], 262),
    ("11th Street Station", [("L", "11th St")], 292),
    ("34th Street Station", [("L", "34th St")], 297),
    ("Spring Garden Station", [("L", "Spring Garden")], 300),
    # Line/Corridor [D], [L], [M]; attached to the L and M station rows.
    ("69th Street Transportation Center Multi-Modal & ADA Improvements", [("L", "69th St Transit Center"), ("M", "69th St Transit Center")], 281),
    ("Chinatown Station on the Broad-Ridge Spur", [("B", "Chinatown")], 293),
    ("Erie Station", [("B", "Erie")], 294),
    ("Fairmount Station", [("B", "Fairmount")], 295),
    ("Snyder Station", [("B", "Snyder")], 296),
    # Line/Corridor [B]; the 15th Street (L) rehabilitation was completed in 2020.
    ("City Hall & 15th Street Stations", [("B", "15th St/City Hall")], 298),
    ("Hunting Park and Wyoming Stations (Design),", [("B", "Hunting Park"), ("B", "Wyoming")], 299),
]

# ---------------------------------------------------------------------------------------------
# Trolley routes. Plan pp. 5-6 and 39-40: "5-minute peak service on the T, 15-minute peak service on the
# D", and the entire forty-year-old fleet replaced with 130 low-floor vehicles. Philadelphia p. 1 and
# Delaware p. 2: "100% Accessible Trolley Service: every trolley, every station, every trip".
# ---------------------------------------------------------------------------------------------
T_TEXT = "5-minute peak service; new low-floor trolleys; accessible stops"
TROLLEYS = {  # route: (proposal, named_in_plan, source)
    "T1": (T_TEXT, True, f"{PLAN} pp. 5-6, 39-40; {PHL} p. 1"),
    "T2": (T_TEXT, True, f"{PLAN} pp. 5-6, 39-40; {PHL} p. 1"),
    "T3": (T_TEXT, True, f"{PLAN} pp. 5-6, 39-40; {PHL} p. 1"),
    "T4": (T_TEXT + "; rebuilt Darby Transit Center", True, f"{PLAN} pp. 5-6, 39-40; {DELCO} p. 2"),
    "T5": (T_TEXT, True, f"{PLAN} pp. 5-6, 39-40; {PHL} p. 1"),
    "D1": ("15-minute or better peak service to Media; new low-floor trolleys; accessible stops", True, f"{PLAN} pp. 5-6, 39-40; {DELCO} p. 2"),
    "D2": ("15-minute or better peak service to Sharon Hill; new low-floor trolleys; accessible stops", True, f"{PLAN} pp. 5-6, 39-40; {DELCO} p. 2"),
    # The plan never names the G1 (Route 15). Only its plan-wide trolley statements could apply.
    "G1": ("Not named in the plan; only the plan-wide statements (every trolley, every station accessible) could apply", False, f"{PLAN} pp. 39-40; {PHL} p. 1"),
}


def fetch(name, url, cache_dir):
    """Path to a downloaded file, reused from cache_dir if it is already there."""
    path = Path(cache_dir) / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def gtfs(cache_dir):
    """{'rail': {file: rows}, 'bus': {...}} for the files used here, read straight from the release zip."""
    outer = zipfile.ZipFile(fetch(f"septa_gtfs_{GTFS_TAG}.zip", GTFS_URL, cache_dir))
    feeds = {}
    for kind in ("rail", "bus"):
        inner = zipfile.ZipFile(io.BytesIO(outer.read(f"google_{kind}.zip")))
        files = ["stops", "routes", "route_stops"] + (["trips"] if kind == "bus" else [])
        feeds[kind] = {f: list(csv.DictReader(io.TextIOWrapper(inner.open(f"{f}.txt"), encoding="utf-8-sig"))) for f in files}
    return feeds


def route_order(route_stops, route):
    rows = sorted((r for r in route_stops if r["route_id"] == route and r["direction_id"] == "0"), key=lambda r: int(r["route_stop_sort_order"]))
    return [r["stop_id"] for r in rows]


def accessible(code):
    return {"1": "true", "2": "false"}.get(code, "unknown")


def regional_rail(feed):
    """One row per GTFS rail stop, with the plan's proposed frequency."""
    stops = {s["stop_id"]: s for s in feed["stops"]}
    names = {r["route_id"]: r["route_long_name"] for r in feed["routes"]}
    best = {}  # stop_id -> (minutes, basis, terminal, source)
    lines = defaultdict(list)
    for route, rules in RULES.items():
        ids = route_order(feed["route_stops"], route)
        order = [stops[i]["stop_name"] for i in ids]
        cc = order.index(CENTER_CITY)
        for i, sid in enumerate(ids):
            lines[sid].append(names[route])
            for term, minutes, source in rules:
                if abs(i - cc) <= abs(order.index(term) - cc):
                    basis = "terminal_named_in_plan" if order[i] == term else "inferred_between_terminals"
                    if sid not in best or (minutes, basis != "terminal_named_in_plan") < (best[sid][0], best[sid][1] != "terminal_named_in_plan"):
                        best[sid] = (minutes, basis, term, source)
                    break
    rows = []
    for sid in sorted(lines, key=lambda s: stops[s]["stop_name"]):
        s = stops[sid]
        minutes, basis, term, source = best.get(sid, ("", "not_specified", "", ""))
        rows.append(dict(mode="Regional Rail", line="; ".join(dict.fromkeys(lines[sid])), station=s["stop_name"], stop_id=sid,
                         latitude=s["stop_lat"], longitude=s["stop_lon"], proposed_frequency_minutes=minutes,
                         frequency_basis=basis, frequency_terminal=term, frequency_source=source,
                         accessible_today=accessible(s["wheelchair_boarding"])))
    c = COATESVILLE
    rows.append(dict(mode="Regional Rail", line=names["PAO"], station=c["station"], stop_id="", latitude=c["latitude"], longitude=c["longitude"],
                     proposed_frequency_minutes="", frequency_basis="not_specified", frequency_terminal="",
                     frequency_source=c["source"], accessible_today="unknown"))
    return rows


def metro(feed):
    stops = {s["stop_id"]: s for s in feed["stops"]}
    seen = {}
    for route, (letter, line) in METRO.items():
        for sid in route_order(feed["route_stops"], route):
            s = stops.get(sid) or (ELEVENTH_ST if sid == "2456" else None)
            if s is None:
                raise SystemExit(f"stop {sid} on {route} is not in stops.txt")
            if "Employee" in s["stop_name"]:
                continue
            name = s["stop_name"].split(" - B")[0].strip()  # "Olney Transit Center - B1" -> "Olney Transit Center"
            key = (letter, name)
            if key in seen:
                if line not in seen[key]["line"]:
                    seen[key]["line"] += f"; {line}"
                continue
            seen[key] = dict(mode="Metro", line=line, station=name, stop_id=sid, latitude=s["stop_lat"], longitude=s["stop_lon"],
                             proposed_frequency_minutes="", frequency_basis="not_specified", frequency_terminal="", frequency_source="",
                             accessible_today=accessible(s["wheelchair_boarding"]))
    return list(seen.values())


class Places:
    """Point-in-polygon for House, Senate, county, municipality and Philadelphia Council districts."""

    def __init__(self, cache_dir):
        self.layers = {ch: tiger_districts(ch, cache_dir) for ch in ("house", "senate")}
        council = gpd.read_file(fetch("philadelphia_council_districts_2024.geojson", COUNCIL_URL, cache_dir))
        council["district"] = council["district"].astype(str)
        self.layers["council"] = council[["district", "geometry"]].to_crs(PROJ)
        self.edges = {k: g.boundary.union_all() for k, g in self.layers.items()}
        self.places = {k: tiger_places(k, cache_dir) for k in ("county", "municipality")}

    def locate(self, lons, lats):
        pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(lons, lats), crs="EPSG:4326").to_crs(PROJ)
        out = [dict() for _ in range(len(pts))]
        for k, g in self.layers.items():
            j = gpd.sjoin(pts, g, how="left", predicate="within").sort_values("district").groupby(level=0).first()
            for i, d in j["district"].items():
                d = d if isinstance(d, str) else ""
                out[i][f"{k}_district"] = d
                out[i][f"{k}_near_boundary"] = "" if not d else str(pts.geometry.loc[i].distance(self.edges[k]) * 0.3048 <= NEAR_M).lower()
        for k, g in self.places.items():
            j = gpd.sjoin(pts, g, how="left", predicate="within")
            j = j[~j.index.duplicated(keep="first")]
            for i, p in j["place"].items():
                out[i][k] = p if isinstance(p, str) else ""
        return out


def capital_projects():
    budget = {r["project"]: r for r in csv.DictReader(open(ROOT / "analyses/septa-capital-tip-tracker/data/septa_fy27_capital_projects.csv"))}
    return [(budget[name], targets, page) for name, targets, page in CAPITAL]


def main(out_dir, cache_dir=None):
    cache_dir = cache_dir or tempfile.mkdtemp()
    out = Path(out_dir)
    feeds = gtfs(cache_dir)
    places = Places(cache_dir)
    rr_csv = {r["stop_id"]: r for r in csv.DictReader(open(D / "septa-region/regional-rail-station-districts/regional-rail-station-districts.csv"))}
    legs = {ch: records(D / f"pennsylvania/legislators-2025-2026/records/{ch}") for ch in ("house", "senate")}
    results = {ch: records(D / f"pennsylvania/election-2026-results/records/{ch}") for ch in ("house", "senate")}

    # --- stations ---
    stations = regional_rail(feeds["rail"]) + metro(feeds["bus"])
    located = places.locate([float(s["longitude"]) for s in stations], [float(s["latitude"]) for s in stations])
    for s, loc in zip(stations, located):
        c = rr_csv.get(s["stop_id"]) if s["mode"] == "Regional Rail" else None
        if c:  # the repo's Regional Rail districts are the single source of truth
            loc.update(county=c["county"], municipality=c["municipality"], house_district=c["house_district"], senate_district=c["senate_district"],
                       house_near_boundary=c["house_near_boundary"], senate_near_boundary=c["senate_near_boundary"])
        s["district_source"] = "regional_rail_station_districts" if c else "point_in_polygon"
        if loc["county"] != "Philadelphia":
            loc["council_district"] = loc["council_near_boundary"] = ""
        s.update({k: loc[k] for k in ("county", "municipality", "house_district", "house_near_boundary", "senate_district",
                                       "senate_near_boundary", "council_district", "council_near_boundary")})
        s["accessibility_rebuild_proposed"] = {"false": "true", "true": "false"}.get(s["accessible_today"], "")
        s["fy27_named_projects"], s["fy27_named_projects_millions"] = [], 0.0

    key = {("RR" if s["mode"] == "Regional Rail" else s["line"][-2], s["station"]): s for s in stations}
    project_rows = []
    for p, targets, page in capital_projects():
        for t in targets:
            if t not in key:
                raise SystemExit(f"capital project station not found: {t}")
            key[t]["fy27_named_projects"].append(p["project"].rstrip(","))
            key[t]["fy27_named_projects_millions"] += float(p["budget_musd"])
        project_rows.append(dict(project=p["project"].rstrip(","), cpms=p["cpms"], program=p["program"], total_cost_millions=p["budget_musd"],
                                 twelve_year_millions=p["twelve_year_total_musd"],
                                 stations="; ".join(f"{key[t]['station']} ({'Regional Rail' if t[0] == 'RR' else t[0]})" for t in targets),
                                 budget_page=page))

    for s in stations:
        s["fy27_named_projects"] = "; ".join(s["fy27_named_projects"])
        s["fy27_named_projects_millions"] = f"{s['fy27_named_projects_millions']:.2f}" if s["fy27_named_projects"] else ""
        for ch in ("house", "senate"):
            d = s[f"{ch}_district"]
            m, f = legs[ch].get(d), results[ch].get(d)
            s[f"{ch}_member_2025_26"] = m["full_name"] if m else ""
            s[f"{ch}_party_2025_26"] = m["party"] if m else ""
            s[f"{ch}_seat_2026_status"] = f["outcome"] if f else ("" if not d else "not_up")
            s[f"{ch}_winner_2026"] = f.get("winner", "") if f else ""
            s[f"{ch}_winner_party_2026"] = f.get("winner_party", "") if f else ""

    cols = ["mode", "line", "station", "stop_id", "latitude", "longitude", "county", "municipality",
            "house_district", "senate_district", "council_district", "house_near_boundary", "senate_near_boundary",
            "council_near_boundary", "district_source", "proposed_frequency_minutes", "frequency_basis", "frequency_terminal",
            "frequency_source", "accessible_today", "accessibility_rebuild_proposed", "fy27_named_projects", "fy27_named_projects_millions"]
    cols += [f"{ch}_{c}" for ch in ("house", "senate") for c in ("member_2025_26", "party_2025_26", "seat_2026_status", "winner_2026", "winner_party_2026")]
    write(out / "septa-accelerate-stations.csv", stations, cols)
    write(out / "fy27-named-station-projects.csv", project_rows)

    # --- trolleys ---
    bus = feeds["bus"]
    bus_stops = {s["stop_id"]: s for s in bus["stops"]}
    route_names = {r["route_id"]: r["route_long_name"] for r in bus["routes"]}
    routes, counts = [], []
    for route, (proposal, named, source) in TROLLEYS.items():
        ids = sorted({r["stop_id"] for r in bus["route_stops"] if r["route_id"] == route and r["stop_id"] in bus_stops})
        loc = places.locate([float(bus_stops[i]["stop_lon"]) for i in ids], [float(bus_stops[i]["stop_lat"]) for i in ids])
        routes.append(dict(route=route, name=route_names[route], proposal=proposal, named_in_plan=str(named).lower(), source=source, stop_count=len(ids),
                           accessible_stops_today=sum(bus_stops[i]["wheelchair_boarding"] == "1" for i in ids)))
        for ch in ("house", "senate", "council"):
            for d, n in sorted(Counter(l[f"{ch}_district"] for l in loc if l[f"{ch}_district"]).items(), key=lambda x: int(x[0])):
                counts.append(dict(route=route, chamber=ch, district=d, stop_count=n))
    write(out / "septa-accelerate-trolley-routes.csv", routes)
    write(out / "septa-accelerate-trolley-stops-by-district.csv", counts)

    rr = [s for s in stations if s["mode"] == "Regional Rail"]
    print(f"wrote {len(rr)} Regional Rail and {len(stations) - len(rr)} Metro stations, {len(routes)} trolley routes to {out}")
    print("Regional Rail by proposed frequency:", dict(Counter(s["proposed_frequency_minutes"] or "not specified" for s in rr)))


def write(path, rows, cols=None):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)

# SEPTA Accelerate stations to districts

Lists every Regional Rail and Metro station with the service SEPTA's Accelerate plan proposes for it, places each in a Pennsylvania House and Senate district, county, municipality and Philadelphia Council district, and counts each trolley route's stops by district.

- **Run:** `python build.py ../../datasets/septa-region/septa-accelerate-station-service [CACHE_DIR]`, then `python check_with_census_geocoder.py ../../datasets/septa-region/septa-accelerate-station-service/census-geocoder-check.csv`
- **Needs:** `geopandas`. Downloads SEPTA GTFS release `v202611010` from GitHub, Philadelphia's 2024 Council districts from the City's ArcGIS layer, and Census TIGER/Line 2024 polygons (through the helpers in `regional_rail_station_districts`). Files are reused from `CACHE_DIR` if present, otherwise downloaded into it (or into a temporary folder). Nothing large is committed.
- **Also reads:** the Regional Rail station districts, 2025–26 legislators, 2026 election results and the FY27 capital projects table in `analyses/septa-capital-tip-tracker/data/`.
- **Hand-entered rules:** the service tiers per line, the trolley proposals and the station-to-project matches are constants at the top of `build.py`, each with the plan, Master Plan or budget page it comes from. Check those first when the plan or budget is revised.
- **District summary:** `python build_district_summary.py ../../datasets/septa-region/septa-accelerate-station-service/septa-accelerate-district-summary.csv` (Python 3.11+, no extra packages). Run after `build.py`; it reads that output plus the boardings, legislators, election and vote datasets, and downloads nothing.

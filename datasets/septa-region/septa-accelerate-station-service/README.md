# SEPTA Accelerate: proposed service by station and district

**One-line summary:** Every Regional Rail and Metro station with the service frequency and accessibility SEPTA's Accelerate plan proposes for it, placed in its Pennsylvania House, Senate and Philadelphia Council district, plus the eight trolley routes with their stops counted by district.

## Source

- **Original source:** SEPTA, [Accelerate](https://www.septa.org/accelerate/), November 2026: the [full plan](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_Web_Nov26.pdf), the [executive summary](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_ExecSummary_Web_Nov26.pdf) and five two-page county fact sheets dated September 2026 ([Philadelphia](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_Philadelphia_Web_Nov26.pdf), [Bucks](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_BucksCounty_Web_Nov26.pdf), [Chester](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_ChesterCounty_Web_Nov26.pdf), [Delaware](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_DelawareCounty_Web_Nov26.pdf), [Montgomery](https://www.septa.org/wp-content/uploads/page/communication/SEPTA_Accelerate_MontgomeryCounty_Web_Nov26.pdf)). Pulled 2026-11-16.
- **Station-level service:** SEPTA, [Reimagining Regional Rail: Regional Rail Master Plan](https://wwww.septa.org/initiatives/regional-rail/reimagining-regional-rail/), [Section 05, Network Vision](https://wwww.septa.org/wp-content/uploads/page/planning/RRMP_FINAL_05_Vision_SEPTA.pdf) (September 2026; pages marked DRAFT). Pulled 2026-11-19.
- **Stations, stops and line order:** SEPTA GTFS release [`v202611010`](https://github.com/septadev/GTFS/releases/tag/v202611010) (schedule starting 2026-11-01). Pulled 2026-11-17.
- **Districts:** [Regional Rail stations by district](../regional-rail-station-districts/) for the Regional Rail stations it covers; Census TIGER/Line 2024 for everything else; City of Philadelphia [Council Districts 2024](https://services.arcgis.com/fLeGjb7u4uXqeF9q/arcgis/rest/services/Council_Districts_2024/FeatureServer/0) (the ArcGIS layer behind OpenDataPhilly) (pulled 2026-11-17); [PA legislators 2025–26](../../pennsylvania/legislators-2025-2026/) and [2026 election results](../../pennsylvania/election-2026-results/).
- **Named FY27 projects:** SEPTA [FY2027 Operating and Capital Budget Proposal](https://www.septa.org/wp-content/uploads/page/planning/SEPTA-FY-2027-Operating-Capital-Budget-Proposal.pdf), through the parsed project table in [`analyses/septa-capital-tip-tracker`](../../../analyses/septa-capital-tip-tracker/).
- **Named plan projects:** Jeff Maki's catalog of the 39 named projects in the Accelerate plan, made with AI help and shared in TFP Slack on 2026-11-11, kept as [`sources/jeff-maki-septa-accelerate-projects-2026-11-11.geojson`](../../../pipelines/septa_accelerate_stations/sources/). Every name was checked against the plan text, and every page number against the plan PDF, on 2026-11-24.
- **Bus routes and frequent network:** the same GTFS release. SEPTA marks its weekday frequent routes in red (`route_color` EF3340), which its [maps and signs page](https://wwww.septa.org/initiatives/bus/maps-signs/) defines as "every 15 minutes or better from 6 am to 9 pm weekdays."
- **Costs:** the Regional Rail Master Plan's [Section 07 Implementation](https://wwww.septa.org/wp-content/uploads/page/planning/RRMP_FINAL_07_Implementation_SEPTA.pdf); the Accelerate plan and county fact sheets above; [DVRPC long-range plan SEPTA projects](../dvrpc-lrp-septa-projects/); DVRPC's [FY2025 TIP, MPMS 115472](https://www.dvrpc.org/tip/pa/map/115472); and the FY27 capital budget and FFY2027 TIP tables in [`analyses/septa-capital-tip-tracker`](../../../analyses/septa-capital-tip-tracker/).
- **Built on:** 2026-11-17 (plan projects, bus routes and costs added 2026-11-24)
- **Geography:** SEPTA Regional Rail and Metro (L, B, M) stations and trolley routes; stations in Delaware and New Jersey have no district

## Processing

Script: [`pipelines/septa_accelerate_stations/build.py`](../../../pipelines/septa_accelerate_stations/build.py).

- **Proposed frequency.** Neither document lists stations, but the Master Plan says how far each service runs. Its 15-minute S Lines run "every 15 minutes or better all day ... stopping at every station" (pp. 166–167): S1 Airport to Norristown, S2 Chestnut Hill East to Wawa, S3 Paoli to Fox Chase (pp. 170–175), plus "15-minute MAX from Glenside to Center City" where three lines overlap (pp. 176–177). Its SEPTA Regional lines run 30-minute service "as far as" a named station and 60-minute service beyond (pp. 176–179). The county fact sheets name the same stations. For each line, the stations between Suburban Station and a named station, in GTFS line order, get that station's tier. A station on more than one line gets the best tier. The rules and the page each comes from are typed in at the top of the script.
- **Districts.** Regional Rail districts, county and municipality are copied from `regional-rail-station-districts.csv` (matched on `stop_id`), not recomputed. Metro stations, the three Regional Rail rows that file does not have (Wawa, North Philadelphia Amtrak, Coatesville) and trolley stops are placed by point-in-polygon against the same Census TIGER/Line 2024 polygons and the same 100 m edge test that pipeline uses. Council districts are point-in-polygon against the City's 2024 layer, for Philadelphia stations only.
- **Metro stations** are the stops on GTFS routes L1, B1, B3 and M1, one row per station per line letter (a station on both the B1 and B3 is one row). The employee-only platform on the M is dropped.
- **District summary.** [`build_district_summary.py`](../../../pipelines/septa_accelerate_stations/build_district_summary.py) counts the station and trolley files by district and adds the member and 2026 result (from the datasets above), the member's vote on final passage of the 2025–26 transit funding bill in that chamber (HB 1788 in the House, HB 257 in the Senate, from [transportation votes](../../pennsylvania/transportation-votes/)), and weekday Regional Rail boardings from [SEPTA's station layer](../septa-regional-rail-stations/), matched on `stop_id`. It reads only files in this repo. It counts; it does not score or rank districts.
- **Named plan projects.** [`build_plan_projects.py`](../../../pipelines/septa_accelerate_stations/build_plan_projects.py) places each of Jeff's 39 projects, best source first: at a station in the station file (districts copied); along the GTFS shapes of Routes 47, 72 and 76 (districts the route crosses); at Jeff's hand-placed point for the two transit centers and Crum Creek Viaduct; along Jeff's hand-drawn line for the Olney Avenue and Roosevelt Boulevard corridors, whose extent the plan does not give. Projects the other files already place (trolleys, L/B/M cars, Regional Rail frequencies and accessibility, the Schuylkill bridges) are listed but not placed again. Pit-crew cleaning is placed at the four B and L line ends, since the plan puts it "when they reach the end of the line". Systemwide items have no location. `location_basis` says which applies.
- **Bus routes.** [`build_bus_routes.py`](../../../pipelines/septa_accelerate_stations/build_bus_routes.py) places every GTFS bus and trackless trolley route in the districts its shapes cross, and measures how often it runs: trips starting 7:00 to 19:00 on Wednesday Nov 18, Saturday Nov 21 and Sunday Nov 22, 2026, taking the less frequent direction. `septa_frequent_weekday` is SEPTA's own red marking, not the measurement; all 25 red routes measure every 15 minutes or better on the Wednesday.
- **Costs.** [`build_cost_sources.py`](../../../pipelines/septa_accelerate_stations/build_cost_sources.py) collects every public dollar figure found for Accelerate, one row per figure, with its source, page and wording, and ties each to the plan projects it covers. Figures typed from documents were each checked against the source; DVRPC and budget figures are read from the repo's own tables. Nothing is summed or split by district.
- **Named FY27 projects** are matched to stations by hand, by project name, and their total project cost is read from the capital budget table.

## Files

| File | Format | Description |
|---|---|---|
| `septa-accelerate-stations.csv` | CSV | One row per Regional Rail and Metro station, 231 rows |
| `septa-accelerate-trolley-routes.csv` | CSV | One row per trolley route, 8 rows |
| `septa-accelerate-trolley-stops-by-district.csv` | CSV | Trolley stops counted by route, chamber (`house`, `senate`, `council`) and district |
| `fy27-named-station-projects.csv` | CSV | The 22 named FY27 capital projects and the station rows each is attached to |
| `septa-accelerate-district-summary.csv` | CSV | One row per House and Senate district with at least half its population in the five Pennsylvania SEPTA counties or with a station or trolley stop, and per Council district: counts from the files above plus the member, 2026 result, transit funding vote and Regional Rail boardings |
| `septa-accelerate-plan-projects.csv` | CSV | The 39 named projects in the Accelerate plan, with status, plan pages and the districts each reaches |
| `septa-accelerate-plan-projects.geojson` | GeoJSON | The 20 of those placed here, for mapping |
| `septa-accelerate-cost-sources.csv` | CSV | 75 public dollar figures for Accelerate components, each with source, page and wording |
| `septa-bus-routes.csv` | CSV | Every SEPTA bus and trackless trolley route, 155 rows: measured frequency by day, SEPTA's frequent marking, and the districts it runs through |
| `census-geocoder-check.csv` | CSV | Independent check of the 77 point-in-polygon station rows against the Census geocoder |

## Columns

`septa-accelerate-stations.csv`

| Column | Type | Description |
|---|---|---|
| `mode` | text | `Regional Rail` or `Metro` |
| `line` | text | GTFS line names serving the station, separated by `;` |
| `station`, `stop_id`, `latitude`, `longitude` | text, text, number, number | From GTFS. Coatesville has no stop yet (see caveats) |
| `county`, `municipality` | text | Blank outside Pennsylvania |
| `house_district`, `senate_district` | text | Blank outside Pennsylvania |
| `council_district` | text | Philadelphia Council district (2024 map); blank outside Philadelphia |
| `house_near_boundary`, `senate_near_boundary`, `council_near_boundary` | true/false | `true` if the station is within 100 m of that district's edge |
| `district_source` | text | `regional_rail_station_districts` (copied from that dataset) or `point_in_polygon` (computed here) |
| `proposed_frequency_minutes` | number | 15, 30 or 60: the "15-minute", "30-minute or better" or "60-minute or better" tier (the Master Plan's "15-minute MAX", "30-minute MAX", "60-minute MAX"). Blank where neither document specifies one. Metro rows are always blank |
| `frequency_basis` | text | `terminal_named_in_plan` (the plan names this station as where a tier reaches), `between_named_stations` (between Center City and such a station), or `not_specified` |
| `frequency_terminal` | text | The named station whose tier applies |
| `frequency_source` | text | Fact sheet or plan page for that tier. Plan pages are the printed numbers of the two-page spread |
| `accessible_today` | text | From GTFS `wheelchair_boarding`: `true`, `false` or `unknown` |
| `accessibility_rebuild_proposed` | true/false | `true` where the station is not accessible today. The plan proposes full accessibility at every Regional Rail station (pp. 9–10, 55–56) and every Metro station (pp. 7–8, 57–58), so these are the stations that need work. Blank where accessibility today is unknown |
| `fy27_named_projects` | text | Named FY27 capital budget projects at this station, separated by `;` |
| `fy27_named_projects_millions` | number | Total project cost of those projects, $ millions. A project at two stations counts in full at both, so do not sum this column |
| `house_member_2025_26`, `house_party_2025_26` (and Senate) | text | Member for the district |
| `house_seat_2026_status`, `senate_seat_2026_status` | text | `hold`, `flip_r_to_d`, `flip_d_to_r`, `uncounted`, or `not_up`. Unofficial, as of 2026-11-10 |
| `*_winner_2026`, `*_winner_party_2026` | text | Unofficial winner of that seat; blank where the seat was not up |

`septa-accelerate-trolley-routes.csv`: `route`, `name` (GTFS), `proposal` (the plan's wording, condensed), `named_in_plan`, `source` (pages), `stop_count` (GTFS stops on the route, both directions), `accessible_stops_today` (stops with GTFS `wheelchair_boarding = 1`).

`septa-accelerate-trolley-stops-by-district.csv`: `route`, `chamber`, `district`, `stop_count`.

`septa-accelerate-district-summary.csv`

| Column | Type | Description |
|---|---|---|
| `chamber`, `district` | text | `house`, `senate` or `council`, and the district number |
| `member_2025_26`, `party_2025_26` | text | House and Senate only |
| `seat_2026_status`, `winner_2026`, `winner_party_2026` | text | As in the station file. Unofficial |
| `transit_funding_vote_bill`, `transit_funding_vote_2025_26` | text | `HB 1788` (House final passage, Aug 11, 2025) or `HB 257` (Senate final passage, Aug 12, 2025), and the 2025–26 member's vote: `Y`, `N`, `NV` (not voting) or `NA` |
| `transit_funding_vote_pro_transit` | true/false | Whether that vote was the pro-transit position, from the roll call's `pro_position`. On HB 1788 that is Yes; on HB 257, the Senate's version without the House transit funding, it is No. Blank for `NV` and `NA` |
| `regional_rail_stations` | number | Regional Rail stops in the district |
| `rr_15_min`, `rr_30_min`, `rr_60_min`, `rr_frequency_not_specified` | number | Those stops by proposed tier |
| `metro_stations` | number | Metro stations in the district |
| `accessibility_rebuilds` | number | Regional Rail and Metro stations not accessible today |
| `accessible_today_unknown` | number | Stations with no GTFS accessibility value |
| `trolley_routes`, `trolley_stops` | text, number | Trolley routes with a stop in the district, and their stops (counted as in the trolley file) |
| `fy27_named_projects` | number | Distinct named FY27 station projects at stations in the district |
| `fy27_named_projects_millions` | number | Total project cost of those projects, $ millions, each counted once per district. A project with stations in two districts counts in full in both, so do not sum this column across districts. Program-wide budget lines are not included |
| `plan_projects`, `plan_project_names` | number, text | Named Accelerate plan projects placed in the district (stations, bus routes, transit centers, corridors, TOD sites), and their names separated by `;`. Projects counted elsewhere in this file, and systemwide ones, are not included |
| `bus_routes`, `frequent_bus_routes`, `frequent_bus_route_names` | number, number, text | Bus routes that run through the district, how many of them are on SEPTA's weekday frequent network, and those route numbers |
| `rr_weekday_boardings` | number | SEPTA's weekday total boardings at the district's Regional Rail stops |
| `rr_weekday_boardings_at_15_min_stations` | number | The same, for 15-minute stops only |
| `rr_stations_without_boardings` | number | Stops with no SEPTA boardings figure (Wawa, North Philadelphia Amtrak, Coatesville) |
| `near_boundary_stations` | number | Stations within 100 m of this district's edge |

`fy27-named-station-projects.csv`: `project`, `cpms`, `program` (as in the budget), `total_cost_millions`, `twelve_year_millions` (FY2027–2038), `stations`, `budget_page` (PDF page of the project sheet).

`septa-accelerate-plan-projects.csv`: `id` (Jeff's), `name`, `program` (the plan's section), `project_type`, `status` (as the plan states it: `proposed`, `underway`, `underway (procurement)`, `completed`, `status not stated`), `quantities`, `description`, `plan_pages` (printed page numbers), `location_basis` (`gtfs_station`, `gtfs_route_shape`, `approximate_point`, `schematic_line`, `covered_elsewhere` or `none`), `location_note`, `stations`, `house_districts`, `senate_districts`, `council_districts` (each separated by `;`), `covered_in` (the file that already places it), `related_fy27_project`, `dvrpc_tip_mpms`, `notes`.

`septa-bus-routes.csv`: `route`, `name` (GTFS), `wed_avg_headway_min`, `wed_max_gap_min`, `sat_avg_headway_min`, `sat_max_gap_min`, `sun_avg_headway_min`, `sun_max_gap_min` (minutes; blank where the route has fewer than two trips each way from 7:00 to 19:00 that day), `septa_frequent_weekday` (true/false), `house_districts`, `senate_districts`, `council_districts` (separated by `;`).

`septa-accelerate-cost-sources.csv`: `plan_project_ids` (the plan projects it covers, by `id` in the plan projects file; blank for items the plan does not name, like Cornwells Heights), `component`, `figure_millions`, `qualifier` (`more than` where the source says so), `dollar_basis`, `status` (estimate, funded, unfunded, programmed, completed), `source`, `source_url`, `page_or_id`, `wording` (the source's words, or the project scope), `match` (`named`: the source names the project; `inferred`: same scope, but the source does not tie it to Accelerate or the Master Plan; `related`: an overlapping budget line).

## Key findings

- **74 of 156 Regional Rail stops are in the 15-minute tier** (47%), consistent with the plan's "nearly half of our 155 stations" (pp. 9–10). 46 are in the 30-minute or better tier and 36 in the 60-minute or better tier. Coatesville is a 157th row with no tier.
- **By county**, the 15-minute stations are 35 in Philadelphia, 17 in Delaware, 17 in Montgomery and 5 in Chester. None are in Bucks, where the best named tier is 30 minutes.
- **79 of 156 Regional Rail stops are not accessible today** by SEPTA's GTFS, including 38 in the 15-minute tier. Six of the 79 have a named FY27 station project. On Metro, 28 of 74 stations are not accessible today: 3 on the L, 10 on the B and 15 on the M. Ten of those 28 have a named FY27 project; none of the 15 M stations do.
- **Seats that flipped.** Seven stations with a proposed tier are in House seats that flipped R to D in the unofficial 2026 results: Cornwells Heights, Eddington, Neshaminy Falls and Trevose (HD-18, 30-minute tier), Langhorne and Woodbourne (HD-142, 60-minute tier), and Wawa (HD-160, 15-minute tier). Eight are in Senate seats that flipped (seven in SD-6, one in SD-24).
- **Trolleys.** The plan proposes 5-minute peak service on the five T routes and 15-minute peak service on the D1 and D2, with new low-floor vehicles and accessible stops. The eight routes have 706 GTFS stops between them (shared stops counted once per route).
- **The named FY27 station projects total $1,388.28M** across 22 projects and 26 station rows. The largest is the $400M Schuylkill bridges and interlockings between 30th Street and Suburban Station.

- **The plan names 39 projects; 20 are placed here.** 12 are at stations, 3 are bus routes, 2 are transit centers, 2 are street corridors and 1 is a viaduct. 9 more (trolleys, L/B/M cars, Regional Rail frequencies and accessibility, the Schuylkill bridges) are already placed by the station, trolley and FY27 files. 10 are systemwide or name no site. 47 of the 92 districts in the summary have at least one placed plan project.
- **25 bus routes are on SEPTA's weekday frequent network today.** Only 3 bus routes (33, 52 and Boulevard Direct) average every 15 minutes or better on the Wednesday, Saturday and Sunday measured. The plan's 29 routes "every 15 minutes or better, 7 days a week" come with the full New Bus Network, phased through 2027. 58 of the 92 districts have at least one frequent route, including all 10 Council districts; 30 House districts have none.
- **No source prices Accelerate as a whole.** The closest is the Regional Rail Master Plan: the full rail vision "will require a renewed investment totaling more than $12 billion over the course of the next 30 years," of which SEPTA "is already planning to invest more than $9 billion," leaving "the additional $3 billion" (Section 07, PDF pp. 4–5). DVRPC's long-range plan lists 29 unfunded Regional Rail rebuild items that total about $7.2 billion in 2025 dollars; the two figures cover different scopes and are not reconciled here.
- **The bus pieces are priced in the FY2025 TIP:** $184.82M of Bus Revolution capital, including $92.32M for end-of-line facilities such as the Wissahickon and South Philadelphia transit centers and $59.7M for transit priority corridors including Olney Avenue (MPMS 115472).

Program-wide FY27 budget lines related to the plan's vehicles and lines, total project cost from the capital budget. These are **not** divided among districts (see caveats).

| Capital budget project | $M |
|---|---|
| Trolley Modernization Vehicles and Infrastructure | 3,685.14 |
| Regional Rail Cars Silverliner IV Vehicle Replacement | 2,117.34 |
| Regional Rail Cars Silverliner IV Infrastructure | 132.59 |
| Market-Frankford Line (L) Vehicle Replacement and Infrastructure | 1,805.09 |
| Broad Street Line (B) Vehicle Replacement and Infrastructure | 727.31 |
| Broad Street Subway Line Signals | 194.92 |
| Norristown High Speed Line (M) Signal System Renewal | 352.07 |
| NHSL (M) Viaduct over Schuylkill River | 54.99 |

## Independent check

The 77 rows placed here by point-in-polygon (74 Metro stations and 3 Regional Rail rows) were sent by coordinates to the Census Bureau geocoder (script: [`check_with_census_geocoder.py`](../../../pipelines/septa_accelerate_stations/check_with_census_geocoder.py)). 76 agree on both House and Senate district. The one difference is Logan on the B: HD-201 here, HD-198 from the geocoder. It sits within 100 m of the edge and is flagged `house_near_boundary`.

## Known gaps and caveats

- **Accelerate is a vision plan.** It is not a funded program or an itemized project list. SEPTA says the full vision "is only achievable with stable, adequate investment." Nothing here says when, or whether, a station will see the proposed service.
- **These are end-state frequencies, decades out.** The Master Plan's Network Vision is the full build-out, phased from today through 2055 (Section 06, Phasing; the pages are marked DRAFT). Early Action (to 2030) restores and adds 30- and 60-minute all-day service; the first S Line, Airport to Norristown, is planned for 2030–2035, and the others follow in later phases. Accelerate describes the same end state (Regional Rail ridership doubling "over the next 30 years", plan pp. 53–54). Read a station's tier as what the plan proposes eventually, not what it gets this decade.
- **Frequencies come from line-level statements.** SEPTA has not published a station-by-station table. The tiers follow the Master Plan's statements of how far each service runs, and S Lines stop at every station, so the between-stations rule matches what the plan says. Peak-hour express trains (for example the Paoli/Thorndale express, pp. 178–179) and any later changes to the plan could still differ for individual stations. Montgomery's sheet says 15-minute service comes "first to Jenkintown, then to Paoli and Norristown", so the tiers do not all arrive at once. The 30 and 60 tiers are ceilings ("MAX", "or better").
- **Chestnut Hill West and Cynwyd come from the Master Plan only.** The Accelerate documents do not name a frequency for them; the Master Plan gives both hourly all-day service (pp. 178–179). Coatesville has no frequency in either.
- **Coatesville.** The Chester County sheet proposes "reinstated service to Coatesville" with no frequency. There is no GTFS stop; the row uses the location of the existing Amtrak station, which is approximate.
- **Metro frequency is line-level.** The plan proposes "15-minute or better M service" (Montgomery sheet p. 2) and "25% shorter headway capabilities" on the L (plan pp. 7–8; Philadelphia sheet p. 2). Neither is a station-level frequency, so Metro rows are blank.
- **G1 (Route 15) is not named in the plan.** Its row says so. Only the plan-wide statements (the whole trolley fleet replaced, every trolley station accessible) could apply to it.
- **FY27 program dollars are not divided by district.** Vehicle, signal and trolley programs run across many districts and cannot be split among them honestly, so they are listed above as totals only.
- **Named FY27 projects are related budget items, not proof they fund Accelerate.** They are station projects in SEPTA's capital budget at stations the plan covers. Some are mostly in the past (Ardmore reopened in March 2026), and some are mostly deferred (Noble construction is deferred beyond FY2038; the 69th Street project is scheduled for 2038 and beyond). `total_cost_millions` is the whole project cost, including prior years; `twelve_year_millions` is what the budget plans for FY2027–2038.
- **Projects attached to more than one station** (30th Street and Suburban, Fern Rock on Regional Rail and the B, 69th Street on the L and M, Hunting Park and Wyoming) carry their full cost on each row.
- **Accessibility today is GTFS's.** It may lag recent work: Ardmore reopened in March 2026 but is still `false` in this feed. 11th St (L) is missing from the feed's stop list and has no scheduled stops; its location is the Market St & 11th St bus stop, and it is marked not accessible because its FY27 project is described as making it "fully ADA accessible."
- **Two North Philadelphia stops.** GTFS has North Philadelphia SEPTA (Chestnut Hill West) and North Philadelphia Amtrak (Trenton Line) as separate stops, so there are 156 Regional Rail stops rather than SEPTA's 155 stations.
- **Results are unofficial.** They come from MultiState's election page, not certified returns. **Member names are for 2025–26** and will change in January 2027 where seats flipped or incumbents left.
- **Edge cases.** Rows flagged `near_boundary` could land in a neighboring district with small coordinate differences.
- **Trolley stops** are GTFS stops, so a stop served in both directions usually counts twice, and stops shared by several T routes count once for each route.

- **The district summary counts bus routes, not riders reached.** Accelerate's largest change in Philadelphia is the bus network: the Philadelphia fact sheet's 620,000 to 1.4 million residents near frequent transit comes mostly from buses. The summary counts the routes through each district and today's frequent ones, not how many residents live near frequent service or how the full network will change that.
- **Boardings are SEPTA's and undated.** SEPTA's station layer does not say what period its counts cover (see [that dataset](../septa-regional-rail-stations/)). They are Regional Rail only; Metro and trolley ridership is not included.
- **Plan projects have no dollars in the plan itself.** `septa-accelerate-cost-sources.csv` collects what other public documents give. Figures overlap (the same trolley program appears in the FY27 budget, both TIPs and the long-range plan, at different amounts and dollar bases), so never add the column up.
- **Program-level costs are not split by district.** Most figures cover whole lines, fleets or programs.
- **Corridor and route districts are generous.** A route or corridor counts in every district it touches, including one it only runs along the edge of. The Olney Avenue and Roosevelt Boulevard lines are hand-drawn and their extent is assumed (see `location_note`).
- **The Accelerate 29 frequent routes are not listed anywhere public.** SEPTA gives the count, not the routes. `septa_frequent_weekday` is the network running now, so it can change as later phases roll out (February and June 2027).
- **Bus districts are generous.** A route counts in every district its shapes touch, including ones it only runs along the edge of or briefly crosses.
- **Council rows have no member names.** The repo does not have a City Council roster yet.
- **Votes belong to the 2025–26 member.** Where a seat flipped or turned over, the new member did not cast that vote.

## License

CC BY 4.0. Please credit Transit Forward Philly, SEPTA, the City of Philadelphia and the US Census Bureau.

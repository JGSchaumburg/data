# DVRPC long-range plan: SEPTA projects and costs

**One-line summary:** The 84 Pennsylvania transit projects (SEPTA) in DVRPC's long-range plan, 39 funded and 45 unfunded, each with its scope and cost.

## Source

- **Original source:** DVRPC, [Update: Connections 2050 Long-Range Plan, Appendices](https://www.dvrpc.org/Reports/25140.pdf) (May 2026), Appendix F Financial Plan: Table F-25 "Pennsylvania Transit MRPs, Funded" (PDF pp. 251–256) and the transit rows of Table F-30 "Pennsylvania MRPs, Unfunded" (PDF pp. 271–277). Funded costs are revised where DVRPC's [Amendment 1](https://www.dvrpc.org/Reports/26140.pdf) (adopted September 2026), Table 5, changed them.
- **Pulled on:** 2026-11-24
- **Geography:** SEPTA's five Pennsylvania counties
- **Time period covered:** plan periods 2026–2050

## Processing

Script: [`pipelines/dvrpc_lrp_septa_projects/build.py`](../../../pipelines/dvrpc_lrp_septa_projects/build.py). It downloads both PDFs, reads the tables from `pdftotext -layout` output, and stops if the row counts (39 funded, 45 unfunded, 6 amended) change. Text that wraps across lines is joined. Nothing is retyped by hand.

## Files

| File | Format | Description |
|---|---|---|
| `dvrpc-lrp-septa-projects.csv` | CSV | One row per Major Regional Project (MRP) with an ID beginning PAT |

## Columns

| Column | Type | Units | Description |
|---|---|---|---|
| `table` | text | | `F-25 funded` or `F-30 unfunded` |
| `mrp_id` | text | | DVRPC's MRP ID |
| `facility`, `scope`, `location` | text | | As printed |
| `cost_millions` | number | $ millions | As printed in the May 2026 appendix |
| `amendment1_cost_millions`, `amendment1_note` | number, text | $ millions | Amendment 1's revised cost and its explanation; blank if unchanged |
| `current_cost_millions` | number | $ millions | Amendment 1 cost where there is one, otherwise the appendix cost |
| `dollar_basis` | text | | `year of expenditure` (funded) or `2025 dollars` (unfunded) |

## Known gaps and caveats

- **Funded and unfunded costs are in different dollars** (year of expenditure versus 2025 dollars). Do not add them together.
- **The plan period column is not kept.** It sits next to the location in the PDF layout; see the PDF for each project's period.
- **Unfunded items are not commitments.** They are projects DVRPC lists as needs without identified funding.
- **Amendment 1's PAT001 note says the cost rose "from $98.53 million"**, while the May appendix prints $96.5M. Both are kept as printed.

## License

CC BY 4.0. Please credit Transit Forward Philly and DVRPC.

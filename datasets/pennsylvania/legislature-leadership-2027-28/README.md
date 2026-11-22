# PA legislature leadership, 2027–28 session (posts not on a 2026 winner record)

**One-line summary:** Caucus leadership posts for the 2027–28 Pennsylvania General Assembly that can't be attached to a seat in [`election-2026-results`](../election-2026-results/), either because the holder's seat was not on the 2026 ballot or because the post has no holder yet.

> Leaders who won in 2026 are **not** here. Their posts are fields on their seat records in `election-2026-results`. Together the two datasets cover every post we track.

## Source

- **Original sources:** Spotlight PA, or the compiled leadership brief where it names no outlet. The source is named on every record. (Leaders who won in 2026 also draw on PoliticsPA and Stephen Caruso's reporting; those posts are on the winner records.)
- **Compiled:** as of 2026-11-19
- **Geography:** Pennsylvania House and Senate
- **Time period covered:** 2027–28 session, ahead of the January 2027 organizing votes

## Processing

Each leader's district comes from [`legislators-2025-2026`](../legislators-2025-2026/), matched on surname and first initial. A post goes on a winner record only when that district's 2026 winner has the same name. Everything else lands here with a `match_status` explaining why. This is a [gitsheet](../../../docs/gitsheets.md): one record per post in `records/<chamber>/<post_id>.toml`, validated by `.gitsheets/pa-legislature-leadership-2027-28.toml`.

## Fields

| Field | Description |
|---|---|
| `chamber`, `caucus`, `role`, `post_id` | The post |
| `holder`, `district` | Who holds it and their seat. Blank where the post is unresolved |
| `status` | `Announced` (the caucus decided), `Expected` (reported but awaiting a vote or a second source), `Contested`, or `Not announced` |
| `source`, `source_date` | Where the entry comes from, and when |
| `match_status`, `match_note` | Why the post is not on a 2026 winner record: `not_on_2026_ballot` or `no_holder` |
| `note`, `as_of` | Context, and the date of the compilation |

## Known gaps and caveats

- **Senate Democratic Caucus Chair** is `Contested` with no holder (Pisciottano, Street and Boscola were contesting).
- **Not announced:** Senate Democratic Secretary, Administrator and Policy Chair, and Senate Republican Caucus Chair, Secretary, Administrator and Policy Chair.
- **President Pro Tempore** (Costa) is `Expected` until the January floor vote.
- **Spotlight PA entries** carry 2026-11-19, the date of the briefing they were compiled from, not the articles' publication dates.

## License

CC BY 4.0. Please credit Transit Forward Philly and the sources named on each record.

# CFB Sundays — cfbsundays.com

See which former players from your college teams are in each NFL game this week, with transfer badges, depth chart slots, per-game and season stats, and school rankings.

## How it works
- `site/` is the whole website: one static HTML page plus small JSON data files. No server, no framework.
- `scripts/build.py` downloads free, open NFL data (nflverse rosters, weekly stats, snap counts, team depth charts, schedule) and rebuilds the JSON.
- `.github/workflows/deploy.yml` rebuilds the data on a schedule (daily, plus extra refreshes after game days) and deploys to GitHub Pages.

## Run locally
    python3 scripts/build.py
    cd site && python3 -m http.server

## Definitions
- A **start** comes from ESPN's starting lineup for each game, which matches who was on the field for the first snap. A **starter** for the season is one of the players with the most starts at his position group on his team, as many as that team usually starts there (regular season only). Kickers and punters count after two games played. If ESPN can't be reached, the build falls back to 50%+ of snaps.
- Each build reuses the previous deploy's `data/starts.json`, so it only asks ESPN for games it hasn't seen.
- Rebuild past seasons by pushing to the `archive-build` branch; the workflow uploads `site/archive` as an artifact to commit.
- Rankings credit the school a player **finished** at. A "finished at X" badge marks a player who also played at the selected school.

Data: [nflverse](https://github.com/nflverse/nflverse-data) (rosters, stats, snap counts, depth charts) and [nfldata](https://github.com/nflverse/nfldata) (schedule).

## Past seasons

Seasons 2013 through 2025 are prebuilt in `site/archive/YYYY/` and committed, since
they no longer change. The page loads one only when someone picks it from the
Season dropdown (`?season=YYYY`). 2013 is the floor because snap counts, which
decide who counts as a starter, begin that year.

Each summer before week 1:

1. Archive the season that just ended: `python3 scripts/build.py --archive 2026`
2. Change `SEASON` at the top of `scripts/build.py` to the new year.
3. Commit both.

Rebuild every archived season (after a conference or nickname fix, say) with
`python3 scripts/build.py --archive all` (2013 through last season).

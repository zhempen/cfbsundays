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
- A **starter** is anyone averaging 50%+ of his team's offensive or defensive snaps over his last three games (current season) or the whole season (archived seasons), with a two-game minimum; kickers and punters count after two games played.
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
`python3 scripts/build.py --archive 2013-2025`.

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
- A **starter** is anyone averaging 50%+ of his team's offensive or defensive snaps over at least two games; kickers and punters count after two games played.
- Rankings credit the school a player **finished** at. A "finished at X" badge marks a player who also played at the selected school.

Data: [nflverse](https://github.com/nflverse/nflverse-data) (rosters, stats, snap counts, depth charts) and [nfldata](https://github.com/nflverse/nfldata) (schedule).

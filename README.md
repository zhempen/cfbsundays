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
- A **start** comes from ESPN's starting lineup for each game, which matches who was on the field for the first snap. A **starter** for the season: at each position group on each team, the usual number of most-started players, plus anyone else who started at least a quarter of the team's games (regular season only). QB splits, benchings and long injury fill-ins all count; one-off spot starts don't. Kickers and punters count after two games played. If ESPN can't be reached, the build falls back to 50%+ of snaps.
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

## Tuesday email

- **Signup:** the form at the bottom of the page posts to a Cloudflare Worker (`worker/`) with a D1
  database. It checks a Turnstile captcha, rate-limits by IP, normalizes addresses (case, `+tags`,
  Gmail dots) so each person gets one subscription, caps schools at 4, and sends a confirmation link
  through Resend. Signing up again with the same address changes the schools after a new confirmation.
- **Deploy:** `.github/workflows/worker.yml` on any change under `worker/`. Needs repo secrets
  `CLOUDFLARE_API_TOKEN`, `RESEND_API_KEY`, `TURNSTILE_SECRET`, plus `account_id` in
  `worker/wrangler.toml` and the Worker's address in `worker/URL` and `SIGNUP_URL` in `site/index.html`.
- **Send:** `.github/workflows/tuesday.yml`, 7 AM New York time on Tuesdays, runs
  `scripts/send_tuesday.py`. It sends the latest week whose games are all final with stats in, once per
  week. Push to the `email-sample` branch to send the latest week to 3 or fewer test subscribers.
- **Limits:** Resend's free plan sends 100 emails a day; the job warns past 95 subscribers.
- **Preview:** `MODE=preview DATA=site PREVIEW_SCHOOLS="Georgia,Alabama" python3 scripts/send_tuesday.py`

# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

College football fans who follow their schools' former players into the NFL. Built for die-hards (the r/cfb crowd who argue about which programs produce NFL talent) and shared directly with friends and family. Used about equally on phones during Sunday games, at watch parties or on the couch, and on desktop during the week to dig into rankings, leaderboards and past seasons.

## Product Purpose

Pick one or more colleges and see which former players are in each NFL game that week, with game and season stats, starters, transfers marked, and how the school ranks against every other program's NFL alumni. Success is a fan opening it on Sunday and immediately seeing where their guys are playing and how they did.

## Positioning

Organized by college, not by NFL team: every view answers "how are my school's players doing on Sundays," across multiple schools at once, with transfers credited and school-vs-school rankings no NFL site offers.

## Operating Context

Static site at cfbsundays.com (GitHub Pages), data rebuilt daily and after game days from free open NFL data (nflverse) plus ESPN starting lineups. A Tuesday-morning email covers the past week for subscribers' schools. Past seasons back to 2013 load on request.

## Capabilities and Constraints

- Tabs: NFL Week (game cards, weekly recap), Leaderboards, School rankings, Conferences, Draft, Fantasy, Playoffs (in season), plus a season dropdown, counting toggle (finished at vs everyone who played there), school search with nicknames, email signup, contact form, and a Konami-code easter egg. All of these stay.
- Must stay fast, light and ad-free; nothing obtrusive.
- Must follow the device's light or dark setting.
- Team identity is shown with colors only. No school, NFL or video game logos, wordmarks or trademarks (legal risk; decided Oct 2026).
- Single static page with inline CSS/JS and JSON data files; no build framework.

## Brand Commitments

- Name: CFB Sundays. Tagline in use: "Pick your schools. See where your guys are playing on Sundays." Email line: "This website could have been an email."
- Copy voice: plain declarative sentences, business-plain, wry at most; no em dashes, no hype, no rhetorical questions.
- The owner is a Georgia fan; the easter egg crowns Georgia.

## Evidence on Hand

Real live data only (rosters, stats, lineups). No testimonials, user counts or press exist; none may be invented.

## Product Principles

1. College first: every screen answers a question about a school's players.
2. Sunday-speed: the answer to "who's playing and how did they do" is one tap away on a phone.
3. Honest numbers: every number traces to the data; gaps are labeled, not smoothed.
4. Fun without friction: personality lives in the presentation, never in extra steps or clutter.

## Accessibility & Inclusion

Readable on phones in bright and dim light; keyboard usable; respects reduced motion.

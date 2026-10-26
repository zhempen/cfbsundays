---
name: CFB Sundays
description: An early-2000s console college football menu. The site is your team-select screen.
colors:
  steel-ground: "#cdd5df"
  steel-panel: "#edf1f6"
  ink: "#0c1526"
  muted: "#3d4a5f"
  line: "#aeb9c8"
  accent: "#1546b8"
  accent-ink: "#ffffff"
  chip: "#dde3eb"
  gold: "#ffc629"
  gold-ink: "#1b1400"
  rail: "#0e1830"
  rail-ink: "#c7d2e8"
  badge: "#5c4300"
  badge-bg: "#ffe9a8"
  stadium-ground: "#090f1d"
  stadium-panel: "#111a2e"
  stadium-ink: "#e7edf8"
  stadium-muted: "#97a6c0"
  stadium-line: "#24314b"
  stadium-accent: "#6f9bff"
  stadium-accent-ink: "#06102a"
  stadium-chip: "#1a2540"
  stadium-rail: "#050a16"
  stadium-rail-ink: "#b9c6df"
  stadium-badge: "#ffd65c"
  stadium-badge-bg: "#3a2e08"
  team1-default: "#1546b8"
  team2-default: "#ffc629"
  team-fallback-1: "#33405a"
  team-fallback-2: "#8a96ad"
  bug-top: "#22325a"
  bug-upper: "#18264a"
  bug-lower: "#121d3a"
  bug-bottom: "#0f1832"
  bug-edge: "#0a1226"
  bug-count-cell: "#070d1c"
  bug-meta: "#a9b6d0"
  bug-final: "#c9d4ea"
  bug-score-loser: "#9fb0cf"
  bug-count-zero: "#7d8bab"
typography:
  display:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "clamp(40px, 8vw, 58px)"
    fontWeight: 800
    lineHeight: 0.92
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 70"
  headline:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 70"
  headline-panel:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "clamp(26px, 4.6vw, 36px)"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 70"
  title:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 70"
  menu:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    letterSpacing: "0.03em"
    fontVariation: "'wdth' 72"
  action:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 800
    letterSpacing: "0.03em"
    fontVariation: "'wdth' 72"
  score:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    lineHeight: 1
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 70"
  count:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 800
    lineHeight: 1
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 70"
  body:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 96"
  body-strong:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 650
    lineHeight: 1.5
    fontFeature: "'tnum' 1"
    fontVariation: "'wdth' 96"
  label:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    letterSpacing: "0.04em"
    fontVariation: "'wdth' 72"
  small:
    fontFamily: "Saira, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
    fontVariation: "'wdth' 96"
rounded:
  hairline: "2px"
  sm: "3px"
  md: "4px"
  dot: "50%"
spacing:
  xxs: "2px"
  xs: "4px"
  sm: "8px"
  md: "12px"
  rhythm: "14px"
  gutter: "16px"
  lg: "24px"
  container: "760px"
components:
  band:
    backgroundColor: "{colors.team1-default}"
    textColor: "{colors.accent-ink}"
    typography: "{typography.display}"
    padding: "18px 16px 14px"
  nav-rail:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.rail-ink}"
    typography: "{typography.menu}"
    padding: "6px 16px"
  nav-tab:
    textColor: "{colors.rail-ink}"
    typography: "{typography.menu}"
    padding: "7px 14px"
  nav-tab-active:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.gold-ink}"
    rounded: "{rounded.hairline}"
    typography: "{typography.menu}"
    padding: "7px 14px"
  button-primary:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.gold-ink}"
    rounded: "{rounded.sm}"
    typography: "{typography.action}"
    padding: "9px 26px"
  button-primary-wide:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.gold-ink}"
    rounded: "{rounded.sm}"
    typography: "{typography.action}"
    padding: "12px 16px"
    width: "100%"
  button-text:
    textColor: "{colors.accent}"
    typography: "{typography.body-strong}"
    padding: "0"
  chip:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.ink}"
    rounded: "{rounded.hairline}"
    padding: "4px 12px"
  chip-selected:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.hairline}"
    typography: "{typography.menu}"
    padding: "5px 14px 5px 18px"
  week-button:
    backgroundColor: "{colors.steel-panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.hairline}"
    padding: "5px 0"
  week-button-active:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.gold-ink}"
    rounded: "{rounded.hairline}"
    padding: "5px 0"
  input-search:
    backgroundColor: "{colors.steel-panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    typography: "{typography.body}"
    padding: "12px 14px"
    width: "100%"
  select-mini:
    backgroundColor: "{colors.steel-panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    typography: "{typography.small}"
    padding: "4px 28px 4px 9px"
  dropdown-option-active:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.gold-ink}"
    padding: "12px 14px"
  card:
    backgroundColor: "{colors.steel-panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "14px 16px"
  card-dark:
    backgroundColor: "{colors.stadium-panel}"
    textColor: "{colors.stadium-ink}"
    rounded: "{rounded.md}"
    padding: "14px 16px"
  score-bug:
    backgroundColor: "{colors.bug-upper}"
    textColor: "{colors.stadium-ink}"
    rounded: "{rounded.sm}"
    padding: "9px 12px"
  score-bug-count:
    backgroundColor: "{colors.bug-count-cell}"
    textColor: "{colors.gold}"
    typography: "{typography.count}"
    padding: "8px 10px"
    width: "86px"
  team-tag:
    backgroundColor: "{colors.team-fallback-1}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.hairline}"
    padding: "2px 8px 2px 10px"
    width: "52px"
  badge:
    backgroundColor: "{colors.badge-bg}"
    textColor: "{colors.badge}"
    rounded: "{rounded.hairline}"
    padding: "1px 7px"
  badge-started:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.accent-ink}"
    rounded: "{rounded.hairline}"
    padding: "1px 7px"
  badge-status:
    backgroundColor: "{colors.chip}"
    textColor: "{colors.muted}"
    rounded: "{rounded.hairline}"
    padding: "1px 7px"
  swatch-dot:
    rounded: "{rounded.dot}"
    size: "0.62em"
---

# Design System: CFB Sundays

## Overview

**Creative North Star: "The Team-Select Screen"**

CFB Sundays is dressed as an early-2000s console college football menu. Picking a school is picking your team on the select screen: the header band, its slanted second-color stripe and the email panel header take on the lead school's colors with a slanted wipe, and a single gold selection bar marks where you are. The ground under it is cool steel in light mode and deep stadium navy in dark mode; the menu rail is always near-black navy. Game rows are broadcast score bugs that stay dark in both themes.

The world is glossy and beveled, never glowing. Depth comes from chrome hairline highlights along top edges, darker bevels along bottom edges, and a split gloss gradient on the band. Everything that is a choice (tabs, chips, week buttons, team tags) is a slanted parallelogram. Type is one variable family, Saira, pushed narrow, heavy and italic for anything that is a label on the menu, and set at near-normal width for reading. Numbers are tabular everywhere.

Team identity is carried by color alone: two-tone swatches, two-tone team tags and the reskinned band. There are no school, NFL or video game logos or wordmarks anywhere in the system. Density is a working tool's density: compact rows, 14px rhythm, one 760px column, built for a phone during a Sunday game.

**Key Characteristics:**
- Team-color band with a glossy split gradient and a slanted second-color stripe at right, recolored at runtime from the lead school.
- Near-black menu rail with slanted italic tab labels and one gold selection bar that slides between tabs.
- Steel (light) or stadium-navy (dark) ground; the menu rail and score bugs stay dark in both.
- Slanted parallelogram shapes for every selectable control, counter-skewed so the text stays upright.
- Saira variable at narrow width (70 to 74) for display and menu labels, near-normal width (96) for body; tabular numerals throughout.
- Colors only, never logos.

## Colors

A cool steel-and-navy neutral field, one gold highlight, one blue link accent, and a runtime team pair that owns the band.

### Primary
- **Team One** (`--team1`, defaults to Varsity Blue, see `team1-default`): the lead school's first color, set at runtime from `site/colors.json`. Fills the header band, the email signup header and the easter egg screen. It is the largest color field on the page and the only one the visitor controls.
- **Team Two** (`--team2`, defaults to Selection Gold, see `team2-default`): the lead school's second color. Fills only the slanted stripe at the right of the band, which bleeds to the viewport edge.
- **Team Ink** (`--team-ink`, `--team2-ink`): text color on Team One and Team Two, computed at runtime: dark ink (`ink`) when the color's relative luminance is above 0.36, otherwise white. The same function sets `--ci` on every team tag and selected chip.

### Secondary
- **Selection Gold** (`gold`, with `gold-ink` text): the one bright highlight. The active tab bar, the active week button, the active or hovered search option, primary buttons, the score-bug hover ring, the gold rule under the rail, text selection and the keyboard focus outline. On dark score bugs it also marks your number: the per-game player count and the "add a school" prompt. Small pointer marks (disclosure triangles, the select caret) are gold too. Gold is identical in light and dark.

### Tertiary
- **Varsity Blue** (`accent`; dark `stadium-accent`): links, text buttons, the table header underline (2px), the "started" badge, form checkbox accent, caret color, scrollbar thumb, and the default selected-chip fill when a school has no colors on file.

### Neutral
- **Steel Ground / Stadium Ground** (`steel-ground` / `stadium-ground`): page background.
- **Steel Panel / Stadium Panel** (`steel-panel` / `stadium-panel`): cards, inputs, dropdowns, inactive week buttons.
- **Chip Steel** (`chip` / `stadium-chip`): unselected chips, table row hover, status badges, scrollbar track.
- **Ink and Muted** (`ink`, `muted` / `stadium-ink`, `stadium-muted`): body text and secondary text (hints, positions, table headers, nicknames).
- **Hairline** (`line` / `stadium-line`): 1px borders on cards, inputs, chips and table rows; the swatch dot's ring.
- **Menu Rail** (`rail`, `rail-ink` / `stadium-rail`, `stadium-rail-ink`): the tab strip and the dark cap of the select caret.
- **Pennant Badge** (`badge` on `badge-bg` / dark pair): transfer and context badges ("finished at", "also", "yours", "Super Bowl", round names).
- **Score Bug Navy** (`bug-*`): a fixed four-stop gloss gradient (`bug-top` to `bug-bottom`) with a `bug-edge` border, a darker `bug-count-cell` on the right, and its own text greys. These do not change with the theme.

### Named Rules
**The One Gold Rule.** Gold means "selected, focused, press this, or this is your number." Only one gold selection bar exists in the rail, one gold week button in the week bar, one gold option in the dropdown. Gold is never a decorative fill or a section color.

**The Colors-Only Rule.** Team identity is expressed only through color: `--team1`/`--team2`/`--team-ink` on the band, `--c1`/`--c2`/`--ci` on team tags, selected chips and swatch dots. No school, NFL or video game logos or wordmarks, ever.

**The Computed Ink Rule.** Text on any team color takes its ink from the luminance function, never a hand-picked value, so every school in `colors.json` stays legible.

## Typography

**Display Font:** Saira (self-hosted variable, `/fonts/saira-latin-var.woff2` and `-italic.woff2`, weight 100 to 900, width 50% to 125%), with system-ui fallback
**Body Font:** Saira, same files
**Label/Mono Font:** none; labels are Saira at narrow width

**Character:** One family doing two jobs. Narrow, heavy, italic and uppercase, it is the menu screen talking; at near-normal width and regular weight, it is the stat sheet. Both are preloaded.

### Hierarchy
- **Display** (800 italic, uppercase, width 70, clamp(40px, 8vw, 58px), line-height 0.92): the "CFB SUNDAYS" wordmark in the band only.
- **Headline** (800 italic, uppercase, width 70, 24px, line-height 1.05, balanced wrap): card titles (h2). The signup panel uses the larger `headline-panel` size, clamp(26px, 4.6vw, 36px).
- **Title** (800 italic, uppercase, width 70, 19px): team-side headings in an open game (h3); the recap summary at 20px.
- **Menu** (700 italic, uppercase, width 72, 17px, 0.03em; 18px on phones): rail tabs. Band meta (week and season) uses the same voice at 15px, 800, 0.05em.
- **Action** (800 italic, uppercase, width 72, 19px to 20px, 0.03em): gold buttons.
- **Score / Count** (800, width 70, 22px / 26px, line-height 1; 24px / 28px on phones): score-bug points and the per-game player count. Team tags use 800 italic width 70 at 18px (20px on phones).
- **Body** (400, width 96, 15px/1.5, tabular numerals; 16px on phones): all reading text. Player names at 650.
- **Label** (700, width 72, uppercase, 12px to 13px, 0.04em to 0.06em): table headers, "FINAL", count labels (10.5px), position codes (12.5px, not uppercase).
- **Small** (400, 13px): hints, nicknames, stat lines, muted meta.

### Named Rules
**The Two Widths Rule.** Narrow (width 70 to 74) is for things the menu says: display, headings, tabs, chips, buttons, scores. Reading text stays at width 96. Never set a paragraph narrow.

**The Tabular Rule.** `font-variant-numeric: tabular-nums` is set on the body, so every score, count and stat column lines up. Don't turn it off.

**The Italic Is Motion Rule.** Italic belongs to display and control labels, where it matches the slanted shapes. Body text is upright.

## Layout

A single centered column, max 760px, with a 16px side gutter that respects safe-area insets. The band and the menu rail run full-bleed; their content sits in the same 760px column, and the band's Team Two stripe extends from inside the column to the right viewport edge.

Order from the top: band (wordmark, tagline, week and season at top right), school chips, search, counting select, menu rail, then the view: week bar, recap, score bugs, and finally the signup panel, contact disclosure, season select and data footer.

Spacing rhythm is small and steady: 14px between cards and below chips, 8px between score bugs and chips, 4px to 5px inside dense grids, 16px to 20px of panel padding. The week bar is an equal-column grid (9 columns on desktop) with 5px gaps.

Breakpoints: at 640px and below, the rail becomes a single horizontally scrolling row with snap points and a fade mask at the right edge, and touch targets grow (tabs 9px by 12px padding, chips 9px by 16px, week buttons 10px vertical). Above 641px the score bug becomes a two-column grid (200px team block, meta beside it). At 600px and below, the recap's two-column stat grid collapses to one.

## Elevation & Depth

Depth is bevel, not float. Surfaces read as pressed plastic and glass: a light hairline highlight on the top inner edge, a darker inner line on the bottom edge, and short tight drop shadows. The band adds a split gloss gradient (lighter top half, darker bottom half, with a hard change at the midline). Nothing glows.

### Shadow Vocabulary
- **Lift** (`--lift`; light `inset 0 1px 0 rgba(255,255,255,.75), 0 1px 2px rgba(12,21,38,.08), 0 8px 18px -10px rgba(12,21,38,.35)`; dark `inset 0 1px 0 rgba(255,255,255,.05), 0 1px 2px rgba(0,0,0,.4), 0 10px 22px -12px rgba(0,0,0,.8)`): every card.
- **Band bevel** (`inset 0 1px 0 rgba(255,255,255,.7), inset 0 2px 0 rgba(255,255,255,.18), inset 0 -1px 0 rgba(255,255,255,.35), inset 0 -3px 0 rgba(0,0,0,.4)`): the chrome hairlines on the band's top and bottom edges. The signup header uses a lighter version.
- **Gold bevel** (`inset 0 1px 0 rgba(255,255,255,.6), inset 0 -3px 0 rgba(0,0,0,.18), 0 3px 8px -4px rgba(0,0,0,.45)`): gold buttons. The tab selection bar uses the inset part only.
- **Gold rule** (`0 3px 0 var(--gold)`): a 3px gold line under the menu rail.
- **Score bug** (`inset 0 1px 0 rgba(255,255,255,.22), 0 2px 4px rgba(0,0,0,.25)`), and on hover or focus adds a 2px gold ring and `0 6px 14px -6px rgba(0,0,0,.5)`.
- **Dropdown** (`0 14px 30px -8px rgba(0,0,0,.45)`): the school search results, the only floating layer besides the easter egg.
- **Inset well** (`inset 0 2px 3px rgba(12,21,38,.08)`): the search input.

### Named Rules
**The Chrome Edge Rule.** Raised menu surfaces carry a 1px white inner highlight on top and a darker inner line at the bottom. That pair, not a large blurred shadow, is what makes something look like a menu button.

**The No Glow Rule.** No colored outer glows, no neon, no blur halos. Gold appears as a solid ring or bar.

## Shapes

Corners are nearly square: 2px on slanted controls, tags and badges, 3px on inputs, buttons, score bugs and dropdowns, 4px on cards. The only round shape is the two-tone team swatch dot.

The signature form is the parallelogram. Tabs' selection bars skew -14deg; chips, week buttons and team tags skew -12deg, with their inner span counter-skewed +12deg so text stays upright. Team tags and selected chips carry a hard color split: a 5px (tags) or 7px (chips) leading stripe in the second color, then the first color. The band's right stripe is a clip-path polygon slanted 84px across its height. Disclosure markers are solid gold CSS triangles that rotate 90deg when open.

## Components

### Buttons
Heavy, gold and pressed-in, like a console menu confirm button.
- **Shape:** gently squared (3px).
- **Primary:** Selection Gold with gold ink, Saira 800 italic uppercase at width 72, 19px, padding 9px 26px. The full-width "add a school" variant is 20px with 12px by 16px padding. Disabled at 0.6 opacity.
- **Hover / Focus:** brightness lifts by 5 to 6 percent; focus shows the global 2px gold outline at 2px offset.
- **Text button:** "Back" and the contact summary are blue link text at weight 600 with no chrome.

### Chips
Slanted tags. Unselected chips are filters; selected chips are your schools.
- **Style:** Chip Steel fill, 1px hairline border, 13px weight 600, skewed -12deg, 2px radius (15px with 9px by 16px padding on phones).
- **Selected:** the school's two colors as `--c1`/`--c2` with computed `--ci` ink, a 7px leading second-color stripe, Saira 800 uppercase at width 74, 15px (17px on phones), inner highlight plus a short drop. Schools without colors fall back to Varsity Blue with a gold stripe. School chips end in a 0.7em SVG cross; filter chips (positions, teams, PPR/Standard, draft rounds) use the same selected look.

### Cards / Containers
- **Corner Style:** 4px.
- **Background:** Steel Panel / Stadium Panel.
- **Shadow Strategy:** Lift (see Elevation & Depth).
- **Border:** 1px hairline.
- **Internal Padding:** 14px 16px; 14px gap below each card.
- **Signup panel:** a card with no padding whose header is a mini band in Team One with the gloss gradient and bevel, the headline in Team Ink.

### Inputs / Fields
- **Style:** Steel Panel fill, 1px hairline, 3px radius, 16px text (prevents phone zoom), 12px by 14px padding, a faint inset well. Placeholders use Muted at full opacity. The signup email field sits on the page ground color instead.
- **Focus:** the global gold outline.
- **Search results:** a floating panel, 1px hairline, 3px radius, max height min(60vh, 380px). Each option is 12px by 14px with a hairline divider; the active or hovered option fills gold with gold ink. Already-picked schools dim to 0.55.
- **Selects:** custom-drawn: 13px weight 600 on Steel Panel, with a 22px Menu Rail cap at the right holding a gold caret drawn from two gradients.
- **Checkboxes:** native, 16px, `accent-color` Varsity Blue.

### Navigation
- **Rail:** full-bleed Menu Rail strip with a top hairline and the 3px gold rule beneath.
- **Tabs:** Saira 700 italic uppercase at width 72, 17px, Rail Ink. Hover turns the label white.
- **Active:** the gold selection bar sits behind the label (skewed -14deg, inset 2px top and bottom, inner bevel) and the label turns gold ink. The bar is one element per tab, and only the active one is visible and carries the `tabhl` view-transition name, so switching tabs morphs the bar from old tab to new (0.28s, cubic-bezier(.16,1,.3,1)).
- **Mobile:** one scrolling row with snap and a right-edge fade; no scrollbar.

### Week Bar
A grid of slanted buttons, one per week. Steel Panel, 1px hairline, Saira 700 at width 72, 15px. Hover shifts the border to Varsity Blue. The current week is solid gold with gold ink and the gold bevel.

### Score Bug (signature)
Each game is a broadcast score bug and stays dark in both themes.
- **Body:** the four-stop Score Bug Navy gloss gradient, `bug-edge` border, 3px radius, chrome top highlight.
- **Teams:** each NFL team is a slanted two-tone team tag (5px second-color stripe, first-color body, computed ink) with the score beside it. The winning score is white, the losing score `bug-score-loser`.
- **Meta:** "FINAL" in the label voice plus kickoff time in `bug-meta`.
- **Count cell:** the right edge is a `bug-count-cell` column, at least 86px, with the number of your players in gold (`bug-count-zero` grey when none) over a small uppercase per-school breakdown in Rail Ink.
- **Hover / Focus:** a 2px gold ring and a deeper drop, and the bug nudges 3px right.

### Badges and Swatches
- **Badge:** 11px weight 600, 2px radius, 1px by 7px padding, Pennant Badge colors. Variants: "started" in Varsity Blue with accent ink, "starter" on Chip Steel, status on Chip Steel with Muted text.
- **Swatch dot:** a 0.62em circle split vertically into the school's two colors with a 1px hairline ring (1.5px white ring inside a selected chip). Used before school names in card titles, recaps and signup checkboxes.

### Tables
14px body text, headers in the label voice with a 2px Varsity Blue underline, 1px hairline row dividers, right-aligned number columns. Expandable ranking rows hover to Chip Steel and rotate a small SVG chevron 90deg when open.

### Motion
- **Team-select reskin:** when the lead school changes, `--team1`, `--team2`, `--team-ink` and `--team2-ink` are set inside `document.startViewTransition`, and the band (view-transition name `band`) wipes in on a slanted clip-path polygon, left to right, over 0.5s with cubic-bezier(.16,1,.3,1). The root cross-fade is disabled.
- **Selection bar slide:** the `tabhl` group morphs between tabs in 0.28s on the same curve.
- **Small state changes:** score bug hover 0.15s, disclosure triangles 0.15s, ranking chevrons 0.12s.
- **Easter egg:** the championship screen scales in from 0.92 over 0.35s, the answer over 0.5s, only under `prefers-reduced-motion: no-preference`.
- **Reduced motion:** view transitions are not started at all when `prefers-reduced-motion: reduce` matches, and a CSS rule removes any view-transition animation as a backstop.

### Global Theming
- Light and dark follow `prefers-color-scheme`, overridable with `data-theme="light"` or `data-theme="dark"` on the root, and set `color-scheme` to match.
- Text selection is gold with gold ink. Keyboard focus is a 2px gold outline at 2px offset. The scrollbar is a Varsity Blue thumb on a Chip Steel track. The text caret is Varsity Blue.

## Do's and Don'ts

### Do:
- **Do** take team colors only from `site/colors.json` at runtime and route them through `--team1`/`--team2`/`--team-ink` (band) or `--c1`/`--c2`/`--ci` (tags, chips, dots).
- **Do** compute text ink on any team color with the luminance function (dark `#0c1526` above 0.36 luminance, otherwise white).
- **Do** skew selectable controls (-12deg, or -14deg for the tab bar) and counter-skew their text so it stays upright.
- **Do** keep one gold selection per group: one tab, one week, one dropdown option.
- **Do** give raised menu surfaces the chrome edge pair: a 1px white inner highlight on top, a darker inner line at the bottom.
- **Do** keep score bugs dark navy in both themes.
- **Do** use Saira at width 70 to 74 for labels and headings and width 96 for reading text, with tabular numerals.
- **Do** gate every animation and view transition behind a reduced-motion check.

### Don't:
- **Don't** use school, NFL or video game logos, wordmarks or helmet art. Colors only.
- **Don't** add colored outer glows or neon effects. Gold is a solid bar, fill or ring.
- **Don't** use gold for decoration, section headers or large fills that are not a selection, focus, primary action or your player count.
- **Don't** round slanted controls beyond 2px or cards beyond 4px.
- **Don't** set paragraphs in the narrow italic display voice.
- **Don't** introduce a second display family or system display faces; everything is Saira.
- **Don't** hand-pick a text color for a team color.

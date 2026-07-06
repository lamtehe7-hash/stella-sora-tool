# Changelog — Stella Sora Tool

## v0.3.0 (2026-07-07) — pre-release — Event group + Event First Clear task

### New task: Event First Clear
- **`EventFirstClear`** — actually **plays** (Go → Deploy → Auto-Battle) the event Battle Stage stages
  that still have **gray stars** (not first-cleared) to grab First Clear rewards (gems, materials).
  Different from `EventDaily` (Quick Battle *sweep* of already-mastered stages to spend Vigor).
- **3 difficulty checkboxes** Normal / Hard / Challenge (3rd tab) — each run, for every enabled
  difficulty, it scans for gray-star stages and clears them in order. **Locked difficulties are
  skipped** (detected via the selected-pill brightness). Clearing a stage usually unlocks the next →
  auto re-scan.
- **Detection (live survey 2026-07-07, GUNFIRE chapter 2)**: **gold** stars = first-cleared (skip),
  **gray/silver** = not yet (play), **padlock** = locked (skip) — classified by color on the "N-N"
  ribbon. **Auto-Battle** is turned on only when detected OFF (via the **blue ring** around the button,
  tapped **once per battle**) — it never accidentally turns off a running battle.
- **OFF by default** (events are temporary + costs 30 Vigor/battle). Switching events needs re-cropping
  `EVENT_BANNER` like Event Daily. Tuning: `max_stages` (per-run cap), `run_timeout` (seconds/battle).

### UI
- **Collapsible "Event" group** in the app sidebar (Alas-style) grouping **Event Daily** + **Event
  First Clear**. Click the group header to collapse/expand (state remembered).
- Added an **Event First Clear settings page** (3 difficulty checkboxes + tuning).

## v0.2.0 (2026-07-05) — pre-release — Ascension optimization

Based on verified multi-source research (EN/JP/CN) of the Monolith/Ascension mechanics — see
`docs/ascension-strategy.md`.

### Ascension
- **Auto-select the highest already-cleared Difficulty** (`ascension.difficulty`, default `0` = auto).
  Rewards (stubs/coins/Record score) rise monotonically with difficulty, so keeping the game-remembered
  tier can leave rewards behind. Auto only moves UP to a tier whose Quick Battle is lit (cleared); never
  down or to an uncleared tier. Set `2..8` to force a specific tier.
- **Smart Event / Choice Domain** (`smart_event_choice`, default ON): prefers the option granting a
  **free item (Potential/Note)** over blindly tapping the bottom option — found via live-test: the old
  logic took 🪙×30 instead of a Rare Potential. Detected via the coin icon on the reward tag (no coin =
  free item). All-coin/gamble/Spend events still fall back to the safe bottom option (no regression).
- **Skip when Weekly Limit is capped** (`skip_when_capped`, default ON): reads the N/3000 meter on the
  Monolith page; when full (3000/3000) a run yields 0 stubs, so it skips to save a ticket. **Uncheck** to
  still run for Record power (POWER).
- **Last-room shop fix**: the final Portia room only used 1 of 2 shelf-refresh charges (the 360-coin
  enhance reserve blocked the 2nd). Added `enhance_reserve_last_room` (=180) so both refresh charges get
  used to surface SALE items (a 45–72 SALE potential is cheaper per level than a 180 enhance).
- New objective switch `objective=power|score` (POWER default = validated behavior; SCORE experimental).
- **GUI**: added Difficulty, POWER/SCORE objective, last-room enhance reserve, and the skip-when-capped /
  smart-event checkboxes to the Ascension settings page.

### Docs
- README: added a note that the **emulator resolution must be 720×1280** (the tool does not auto-scale;
  changing the resolution makes it error out). Resizing/zooming the MuMu **window** is harmless.

## v0.1.1 (2026-07-05) — pre-release

### Fixed
- **Cleanup crash** (`matchTemplate` assertion). OpenCV threw `(-215) _img <= _templ` whenever a
  template was larger than its search area — this happened during `ui_current_page` and aborted the
  Cleanup task. Fix: widened the `GRANT_CHECK` search area to fit its template, and hardened
  `Button.match` to skip (with a one-time warning) instead of crashing when a template exceeds its
  search region, so a single mis-cropped asset can no longer break page detection.

## v0.1.0 (2026-07-05) — pre-release

First release. A tool that **automates the daily routine** for **Stella Sora (EN server)** running on an Android emulator. Portable Windows 64-bit build — **no Python installation required**.

> ⚠️ This is the **first pre-release** — the tool is still under active development and things may change in future versions.

### Overview

- **Desktop app** (WebView2 window) — toggle each task on/off, hit **Start**, and the scheduler runs the whole daily chain, then schedules the next run for the following day.
- **Bilingual** UI: English / Vietnamese (switch right on the Home screen).
- Controls the game over **ADB** on an emulator (screen recognition via image templates — not blind tapping).
- Personal settings are stored in `config/` next to the exe; rotating logs in `log/`.

### Automated tasks

The scheduler runs the tasks in the order below; each one schedules its own next run (most at the **daily reset**):

| # | Task | What it does automatically |
|---|------|----------------------------|
| 1 | **Login** | Launches the game (if not running) and brings it to the main screen, waiting and dismissing popups; also handles the "tap to start" case after a network drop. |
| 2 | **Mail** | Opens the mailbox, **Claim All** to collect every attachment, dismisses reward popups. |
| 3 | **Dispatch** *(Commission)* | Collects finished commissions (**Claim All**), then fills all 4 slots: pick commission → **Quick Select** the best-fit squad → choose the **20h** tier (max reward) → **Accept**. Repeats every 4 hours. |
| 4 | **Shop** | Claims the **free daily gift box** in the shop. |
| 5 | **Bounty Trial** | Spends **Vigor** via Trial Quick Battle (Basic Trial by default). Skips if the difficulty isn't unlocked, reschedules if Vigor is low. |
| 6 | **Ascension** | Runs **one Monolith Quick Battle** (roguelike): auto-battles, picks cards by priority, buys/upgrades in the shop per strategy, saves the record. A run takes ~4–12 minutes. |
| 7 | **Event Daily** | **Quick Battle sweep** on the open event stage according to Vigor, then scans **Event Missions** to claim rewards. |
| 8 | **Grant** | Claims the **Startup Grant** rewards (Company Goal + Grant Milestone) when available. |
| 9 | **Daily Reward** | Claims **daily missions** + **activity-point milestones**. |
| 10 | **Cleanup** | Returns the game to the main screen; optionally closes the game afterwards. |

### What you can configure

**General**
- ADB serial & path to the emulator's `adb.exe`.
- **Daily reset** time (UTC) — default `11:00` UTC.
- After Cleanup: **close the game** or **keep it on the home screen** (default: keep).
- UI language (en/vi).

**Ascension** *(Monolith run)*
- Runs per session; choose **map** (Currents / Dust / Storm / Misstep) and **squad**.
- Behavior when a Potential preset isn't attached: warn / skip / abort.
- **Card priority**: by level gain / super-rare card / leftmost card.
- Shop strategy: only buy Melody when a Harmony Skill is present, enhance stop-milestone, coin reserve, refresh shelf/refresh cards, Brief mode, save Record, run timeout.

**Bounty Trial**
- Trial type: Basic / Tier-up / Skill / Emblem.
- Difficulty: keep the game's remembered value (0) or set 1–6.

**Event Daily**
- Choose **stage**: leave blank = highest stage, or specify (e.g. `1-12`).
- Battle count: `0` = max according to Vigor, or exactly N battles.

### Requirements

- **Windows 64-bit.**
- An Android emulator with **ADB** (MuMu Player recommended; tested with MuMu Global).
- **Stella Sora (EN)** — package `com.YoStarEN.StellaSora` — installed & logged in on the emulator.

### Install & run

1. Download **`StellaSoraTool-v0.1.0-win64.zip`** from the release Assets.
2. **Extract the whole folder** to your drive — keep `app.exe`, `_internal/` and `assets/` together.
3. Open the emulator, enable ADB, log into the game at the Home screen.
4. Run **`app.exe`**.
5. First time: open **Settings** and enter the **ADB serial** (e.g. `127.0.0.1:16384`) and the **adb path**.
6. Enable the tasks you want → hit **Start**.

### Notes

- **Disabled by default** are the 3 resource-heavy / config-needed tasks: **Ascension**, **Bounty Trial**, **Event Daily**.
- Recognition relies on **EN-server** image templates; other servers/languages may not match.
- Do not move `_internal/` or `assets/` out of the folder containing `app.exe`.
- `config/` and `log/` are created next to `app.exe` on first launch.

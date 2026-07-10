# Changelog — Stella Sora Tool

## v0.4.6 (2026-07-10) — pre-release — Web-UI fallback when the desktop UI fails

### Machines WITH .NET still crash "Failed to resolve Python.Runtime…"
- Additional cause (beyond a missing .NET): a **path containing accented Vietnamese characters** —
  `clr_loader` encodes the `Python.Runtime.dll` path to UTF-8 for the .NET shim, and an accented path
  gets misread → the DLL won't load; or the files being **blocked by Windows (Mark-of-the-Web)** after
  downloading. Both are common for Vietnamese users, and the machine **does have .NET 4.8**.
- **Web-UI fallback**: when the desktop UI fails to start, the app now asks *"Open the web UI instead?"* —
  press **Yes** to run the web interface (pywebio, opens in the browser) which **needs no .NET/clr**, so
  it runs on any machine and any path. Press No to quit.
- New **`app.exe --web`** flag: launch straight into the web UI (make a shortcut if the desktop UI always
  fails on that machine).
- Error message fixed: it now suggests **extracting to a non-accented path** (e.g. `C:\StellaSoraTool`) +
  **Unblock**-ing the zip + installing .NET — instead of only mentioning .NET like v0.4.5.

## v0.4.5 (2026-07-10) — pre-release — Friendly error when the machine is missing .NET Framework

### Fix: `app.exe` crash "Failed to resolve Python.Runtime…" on machines without .NET
- Cause: the desktop UI (pywebview → WebView2) needs **.NET Framework 4.8** to load `pythonnet`.
  A downloader's machine that is **missing/old .NET Framework (< 4.7.2)** crashes on launch with a
  confusing PyInstaller traceback. **The exe is not broken** — the target machine lacks a Windows
  component.
- The app now **catches this and shows a Vietnamese dialog** guiding the user to install
  **.NET Framework 4.8 + WebView2 Runtime** (with links) instead of a traceback. Other startup
  failures also get a short message pointing to the `log/` folder.
- **Docs**: README (VN/EN), user guides, and the bundled `README.txt` now state the .NET Framework 4.8
  + WebView2 requirement.

## v0.4.4 (2026-07-09) — pre-release — New WeeklyReward task + Grant/Mail/PurchaseGift fixes

### New task: WeeklyReward (task #15, enabled by default)
- After DailyReward, opens Missions ▸ **Weekly Affairs** tab, presses **Claim All** when it is lit,
  then claims the weekly-points chest row. Verified live on both paths (real claim + nothing-to-claim).

### Grant — infinite-loop fix
- `Grant` was the only task that never rescheduled itself after finishing. Normally harmless, but if
  its schedule ever slipped into the past (e.g. after a one-off error penalty), the scheduler re-ran
  it **back-to-back forever** — entering and leaving the Startup Grant screen every ~6 seconds until
  the click-spam guard tripped (`GameTooManyClickError`, seen in the field on 2026-07-09). Grant now
  schedules itself to the next server reset like every other task.
- **Scheduler hardening**: after any task finishes with its `next_run` still in the past, the
  scheduler logs a warning and pushes it +60 minutes — no future task can hot-loop this way again.
- Verified live: full claim run (Company Goal Today + Weekly targets → tier-up → Milestone) ending
  with a correct next-reset schedule; plus an offline regression test for the scheduler guard.

### Mail — stuck at Home
- The **new-mail red dot** overlapped the mail icon's corner and broke template matching
  (score 0.752 < 0.85), so the task never entered the mail screen. Template re-cropped to the
  dot-free left 2/3 of the envelope (threshold 0.80). Verified: matches with and without the dot,
  still rejects other screens; full Mail run OK.

### PurchaseGift — stuck on the "Items Obtained!" popup
- The blind-dismiss tap point (200,400) landed inside the popup's white item band, which swallows
  taps — the popup never closed. Moved to (350,575), below the band. (Claimed-already path and
  navigation were verified live; the popup path re-verifies on the next daily gift.)

### Docs
- New **English** and **日本語** user guides (`docs/user-guide.md`, `docs/user-guide-ja.md`) with a
  3-language switcher; JP guide notes the tool supports the **EN client only**.

## v0.4.3 (2026-07-08) — pre-release — Stop button now interrupts the current task immediately

### GUI / Scheduler
- **[Stop] interrupts the running task right away** (at the next screenshot/click — typically within
  a couple of seconds) instead of waiting for the task to finish. Works for the scheduler loop **and**
  the single-task "Run now" button; Ctrl+C in the CLI scheduler behaves the same way.
- An interrupted task is **not penalized**: no error log, no retry delay — its schedule stays untouched,
  so the next Start simply runs it again from the beginning. The game is left untouched too (the tool
  just stops sending input; anything half-done in-game stays as is).
- Internals: a global stop flag (`module/stop_signal.py`) checked at every
  `Device.screenshot/click/click_xy/swipe`, raising a dedicated `TaskInterrupted` that the scheduler
  handles separately. A new session clears the flag on start.
- **Verified live** (Mail task interrupted **0.94s** after pressing Stop) + 4 new offline test cases
  (`tests/test_stop_interrupt.py`); the ADB-retry test suite still passes.

## v0.4.2 (2026-07-08) — pre-release — Ascension runs ~28% faster

### Ascension — run speed
- Tuned **20 fixed post-click delays** across the run loop (shop buys, card picks, note popups,
  settle loops, continue screens). A full Diff-8 run drops **from ~12 to ~8.6 minutes** under the
  capture harness — typical plain runs go from ~8-9 down to **~6 minutes**.
- Deliberately left untouched: event-choice pacing (double-click on options has real consequences),
  the network-retry wait, and every OCR-stability retry.
- **Verified live** on a 100-step run: clean finish, coin reconciliation clean (0 mismatches,
  baseline had 1), no card-pick oscillation, no failed purchases, no click-spam guard trips.
- Profiled with `dev_tools/profile_ascension.py` (added in v0.4.1); the remaining time is mostly
  genuine game animation (card flips, floor transitions).

## v0.4.1 (2026-07-08) — pre-release — 12 audit fixes + Heartlink hardening

Full audit of the v0.4.0 batch (multi-agent review, every finding adversarially verified): 12 confirmed
issues — **all fixed**, the critical paths re-verified live in-game.

### Ascension
- The **"Return to Ascension?"** paused-run dialog is now handled by the scheduled task itself
  (`_recover_paused_run`: Give Up → confirm → save the leftover Record). Previously only the dev capture
  tool handled it, so a paused run (left behind by a crash/timeout) stalled every scheduled attempt.
- **Capture-session analysis**: self-healed ADB retry warnings are no longer mis-counted as crashes
  ("completed: NO" on healthy sessions); purchase-phase coin mismatches are now counted too
  (previously enhance-phase only).
- **Capture tool** no longer overwrites `config/stella.json` — config overrides are truly RAM-only now.

### Heartlink
- The **Start Invitation** dialog and the Date-Location screen are polled **together**: a slow dialog
  could be misread as the daily cap, silently losing the whole day's invites.
- Bottom tabs retry through the **stacked post-date overlays** (reaction → Gifts Received → Affinity UP)
  that used to swallow taps — this was breaking the Mail sub-task right after an Invite.
- Multi-target Mail search scrolls back to the top of the contact list for each target.
- **Mail send loop verified live up to the real 10/10 daily cap** (8 gifts in one go; at the cap the game
  rejects silently and the Affinity-bar check stops the loop with the correct count).

### GUI
- Saving Mail targets whose total exceeds the daily limit is **blocked with a warning** (was silently
  truncated server-side).
- The "send all to the top contact" checkbox now always reflects the real saved behaviour.
- Cancelling the report-export dialog no longer writes the report anyway.

### Dev tools & tests
- New `dev_tools/profile_ascension.py` — shows where a run's time goes (top time sinks + screenshot
  cadence); groundwork for an upcoming run-speed optimisation.
- `rebuild_digits.py` rejects malformed multi-digit CSV labels (substring-check bug).
- ADB retry tests: scoped sleep patch + a new connect()-failure case (4 cases total).

## v0.4.0 (2026-07-08) — pre-release — Heartlink dating + Ascension reliability + capture analysis

### New task: Heartlink (dating → Affinity)
- **`Heartlink`** — raises character **Affinity** through the in-game "phone". Two sub-tasks toggled by
  `do_invite` / `do_mail`:
  - **Invite** (≤5/day): pick a character → **Invite** → confirm the **Start Invitation** dialog →
    **Select Date Location** → **Skip** the date → **Send Gift** (x2 Affinity) / **Leave** → back.
    Already-dated characters (grey "Invited Today") are skipped; the daily cap ends the loop.
  - **Mail / Delivery Service** (10 gifts/day, global): send gifts to raise Affinity — pick a character
    → gift → **Send Gift** → repeat. The cap is detected when the Affinity bar stops changing.
  - `invite_count` (5), `send_gift` (on), `invite_targets` (prioritise named favourites via portrait
    match); `mail_count` (10), `mail_targets` (name+qty, else dump all to the top contact).
- **GUI**: a Heartlink page with two cards (Invite + Mail).
- **OFF by default** (new task + spends gift items when `send_gift`).

### Ascension — reliability & analysis
- **ADB retry/reconnect** in `module/device/adb.py` (backoff 2/5/10s, auto-reconnect) — fixes the single
  hard failure that killed long capture sessions (ADB drop mid-run).
- **Shop-room deadlock fix** — leave the shop via the correct "Nah, let's go up" option (never re-open
  the shelf); survived 26 consecutive runs live.
- **Home→Ascension nav fix** — re-cropped `GO_ENTER` (the Home art changes per featured character).
- **"Return to Ascension?" dialog** (`ASC_GIVE_UP`) handled when a paused run exists.
- **Dissolve weak Records at the Save screen** (off by default) — decide keep/discard by the rank
  **badge frame colour band** (`dissolve_record`, `dissolve_max_band`), no OCR.
- **Capture-session analysis** (user feature, no AI): pick a session → view metrics (buys/enhances/coins/
  time) → export a report → clean up images to free disk. Engine `module/ascension_analysis.py`.

### Dispatch
- **"Dispatch Again" 2-step fix** — the button opens a dialogue + bonus popup on the first press; press
  up to `COMMISSION_MAX_AGAIN` times, dismissing between, then fall back to manual re-dispatch to 4/4.

### Dev tools
- `dev_tools/ascension_capture.py` (frame+log capture), `analyze_capture.py` (offline analysis),
  `rebuild_digits.py` (merge missed OCR glyphs into templates).

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

# Stella Sora Tool (SST) — User Guide

[Tiếng Việt](huong-dan-su-dung.md) | **English** | [日本語](user-guide-ja.md)

> The full manual: installation → configuration → every feature.
> For **Stella Sora (EN server)** running on an **Android emulator** (MuMu Player recommended).
> Screenshots are from the real game; **the account name is masked** (blurred box, top-left).

> ⚠️ Automation may violate the game's Terms of Service → **use an alt account when trying it out**,
> and use it at your own risk. See the [README](../README_EN.md) "Disclaimer & Terms of Use" section.

---

## Table of contents
- [A. Installation & prerequisites](#a-installation--prerequisites)
- [B. The tool's interface](#b-the-tools-interface)
- [C. The game's main screen (hub)](#c-the-games-main-screen-hub)
- [D. Every task in detail](#d-every-task-in-detail)
- [E. The automatic scheduler](#e-the-automatic-scheduler)
- [F. Troubleshooting](#f-troubleshooting)

---

## A. Installation & prerequisites

### 1. Requirements

| Component | Requirement |
|---|---|
| Emulator | MuMu Player (recommended), or LDPlayer/BlueStacks — must expose **ADB** |
| Resolution | **MUST be exactly `1280 × 720`** (width × height — the game runs landscape). MuMu's "Android Device" panel shows exactly this number |
| Game | **Stella Sora (EN server)**, logged in and sitting at the Home screen |
| PC | Windows 10/11 |
| .NET | **.NET Framework 4.8** + **WebView2 Runtime** (the desktop UI needs them). Updated Win 10/11 usually ships both; if `app.exe` shows *"Failed to resolve Python.Runtime…"*, install [.NET 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48) + [WebView2](https://developer.microsoft.com/microsoft-edge/webview2/) and reboot |

> ⚠️ **The resolution must be exactly 1280×720.** The tool recognizes the screen with template images
> cropped at this exact size and does **not** auto-scale. Any other setting (1080×1920, 1600×900…)
> makes the tool error out and stop.
> (Resizing or zooming the MuMu **window** on your desktop is harmless — zoom freely.)

### 2. Two ways to run

**Option 1: portable build (no Python needed)**
1. Download the latest `StellaSoraTool-vX.Y.Z-win64.zip` from the Releases page.
2. Extract the whole folder — keep `app.exe`, `_internal/` and `assets/` together.
3. Run **`app.exe`**.

**Option 2: from source (for developers)**
```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
python app.py        # desktop app (recommended)
```

### 3. First-time configuration (REQUIRED)

Open the tool → go to the **Settings** page and fill in:

| Field | Meaning | Example |
|---|---|---|
| **Emulator serial** | The emulator's ADB address | `127.0.0.1:16384` (MuMu) |
| **adb.exe path** | The adb binary shipped with your emulator | `E:\MuMuPlayerGlobal\nx_device\12.0\shell\adb.exe` |
| **Daily reset (UTC)** | The game's daily reset time (Yostar EN default `11:00` UTC) | `11:00` |
| **Close game on Cleanup** | Whether to fully close the game when done | off (leave the game at Home) |

> How to find the **serial**: with the emulator open, run `adb devices` in a terminal — it lists the
> address (e.g. `127.0.0.1:16384`). MuMu Player Global usually uses port **16384**.

After saving, `config/stella.json` is created next to `app.exe`.

---

## B. The tool's interface

The tool can run **4 ways**:

| Command | Mode |
|---|---|
| `app.exe` / `python app.py` | **Desktop app** (WebView2 window) — recommended |
| `python gui.py` | Web UI at `http://localhost:22270` |
| `python sst.py` | CLI — 24/7 scheduler loop |
| `python sst.py <Task>` | CLI — run one task and exit |

**Desktop app layout:**
- **Left rail**: Home · sst (dashboard) · Settings.
- **Home**: switch **language VI/EN** and **Light/Dark theme**.
- **Dashboard (sst)**:
  - **Start** (launch the automatic scheduler) / **Stop** (interrupts the current task right away,
    then stops).
  - Task list: **toggle** each task, **Run now** button (marks a task due immediately).
  - Status cards: Scheduler / Running / Ready / Waiting.
  - **Log** panel (Auto Scroll) — watch it work live.
- Some tasks have their **own settings page** (Ascension, Bounty Trial, Event, Event First Clear,
  Heartlink) — see [section D](#d-every-task-in-detail).

---

## C. The game's main screen (hub)

Every task starts from the **Home** screen. The main buttons (numbered):

![Home screen with numbered buttons](images/home_annotated.png)

| # | Button | Related task |
|---|---|---|
| 1 | **Mail** (envelope, top-right) | `Mail` |
| 2 | **Missions** | `DailyReward` |
| 3 | **Shop** (left icon) | `Shop` |
| 4 | **Commission** | `Dispatch` |
| 5 | **Grant** | `Grant` |
| 6 | **Event banner** | `EventDaily`, `EventFirstClear` |
| 7 | **Go** (the van, bottom-right) | `BountyTrial`, `Ascension` (entered through here) |
| 8 | **Menu** (☰, very top-right) | Daily Check-in, in-game Settings |

Also in the top-right cluster (not numbered on the image): **Heartlink** (chat bubbles) → `Heartlink`,
**Purchase** (cart) → `PurchaseGift`, and the **Friends** icon (two people, next to Mail) → `FriendGift`.

> Navigation note (important): **the Android Back key does nothing** in this game — every "go back"
> is done with in-game buttons (the 🏠 button on sub-screens, or a screen-specific exit button).

---

## D. Every task in detail

Default run order:
`Login → Mail → Dispatch → Shop → PurchaseGift → BountyTrial → Ascension → EventDaily → EventFirstClear → Grant → Heartlink → FriendGift → DailyReward → Cleanup`.

**Enabled by default**: Login, Mail, Dispatch, Shop, PurchaseGift, Grant, FriendGift, DailyReward, Cleanup.
**Disabled by default** (turn on when you want them): **BountyTrial, Ascension, EventDaily,
EventFirstClear, Heartlink** — they spend resources/tickets or need per-event configuration.

---

### 1. `Login` — Log in & reach the Home screen
Starts the game (if not running), clears the launch popups, and lands on Home. Handles the
**"Network Error"** dialog (presses Retry/Start) on connection drops. Every other task builds on this.

### 2. `Mail` — Claim mail
Opens **Mail** (button 1) → presses **Claim All** to collect every attachment. Claimed mail shows a
**"Claimed"** label.

![Mail screen](images/mail.png)

### 3. `Dispatch` — Commissions
Opens **Commission** (button 4). Two jobs:
- **Claim returned squads**: Claim All, close the "Commission Complete!" popup with the **Back** button.
- **Re-dispatch**: fills empty slots back to **4/4** — for each commission → **Quick Select**
  (auto-picks a matching squad) → choose **20h** (best reward) → **Accept**. Stops when out of Trekkers.

![Commission screen](images/commission.png)

> Squads are away ~20h, so many runs are a "no-op" (nothing back yet) — harmless. When short on
> Trekkers the tool skips and reschedules itself.

### 4. `Shop` — Free shop items
Opens **Shop** (button 3) → claims the **free/daily** items. Already-claimed items show a "Claimed"
pill (the tool skips them).

![Shop screen](images/shop.png)

### 5. `PurchaseGift` — Free Daily Gift
Opens the **Purchase** screen (top-right cluster) and claims the free **Daily Gift** — but only when
the red dot says there is something to claim; otherwise it doesn't even enter the screen.

### 6. `BountyTrial` — Spend Vigor (Quick Battle sweep) · *OFF by default*
Opens **Go** (button 7) → **Bounty** → picks a Trial → **Quick Battle** to sweep as much as Vigor allows.

**Its settings page** (Bounty Trial):
| Option | Meaning |
|---|---|
| **Trial type** | `Basic` (materials) · `Tier-up` · `Skill` · `Emblem` |
| **Difficulty** | `0` = keep what the game remembers; `1–6` = force that tier (must already be cleared to sweep) |

> ⚠️ This task **spends Vigor** — enable it when you want your Vigor to go into Trials.

### 7. `Ascension` — Monolith runs · *OFF by default*
Opens **Go** (button 7) → **Ascension**. Each run costs **1 Monolith ticket** (no Vigor). The tool
picks cards, buys from mid-run shops, enhances, and saves the Record. This is the most configurable task.

**Its settings page** (Ascension) — main groups:
| Group | Typical options |
|---|---|
| Tickets & runs | **Runs per session** (stops on its own when out of tickets) |
| Map | Keep the game's last map / force Currents·Dust·Storm (avoid Misstep for farming) |
| Difficulty | `0` = auto-pick the highest already-cleared tier (recommended) / force tier 2–8 |
| Squad | `0` = keep as-is / force squad N |
| Preset | When "Preset not set": Warn / Skip / **Error & stop** (default) |
| Card picks | Highest level gain (default) / Prefer Super Rare / Leftmost |
| Shop | Buy Melody only when needed · enhance coin thresholds/reserve · refresh the final-room shelf |
| Run | Brief mode · Save Record · **Skip when Weekly Limit is full** · max run time |

> Defaults follow the community meta (POWER — strong Records). Only change things you understand.
> Strategy details: `docs/ascension-strategy.md`.

### 8. `EventDaily` — Event sweep · *OFF by default*
Opens the Home **event banner** (button 6) → Battle Stage → **Quick Battle** sweep; then claims
Event Mission rewards if the red dot is up.

**Its settings page** (Event):
| Option | Meaning |
|---|---|
| **Stage** | empty = highest stage; or enter `W-N` (e.g. `1-12`) for an exact stage |
| **Battle count** | `0` = as many as Vigor allows; `N` = exactly N |

> ⚠️ Events rotate: **each new event needs the banner re-cropped**
> (`assets/en/event/EVENT_BANNER.png`) and the stage reviewed before enabling. If the banner isn't
> found the tool skips safely (it never runs the wrong thing).

### 9. `EventFirstClear` — First-clear event stages · *OFF by default*
Walks the event's Battle Stage list and **auto-fights every stage that still shows grey stars**
(not yet cleared): enters the stage → **Deploy** → turns **Auto-Battle** on → waits for Victory,
then moves to the next one. Stops cleanly when nothing clearable is left (time-locked stages are
skipped). Has its own settings page in the **Event** group of the sidebar.

### 10. `Grant` — Startup Grant rewards · *ON by default*
Opens **Grant** (button 5) → the **Startup Grant** screen. Two tabs (**Grant Milestone** and
**Company Goal**), each with its own red dot. The tool claims **Company Goal first** (its progress
raises the Grant Tier, unlocking Milestone rewards) then **Claim All** on both. Free rewards, no risk.

![Startup Grant screen](images/grant.png)

### 11. `Heartlink` — Dates & gifts (Affinity) · *OFF by default*
Opens **Heartlink** (chat-bubble icon, top-right cluster). Two sub-tasks, each with its own card on
the Heartlink settings page:

- **Invite** (dates, up to **5/day**): picks a character whose **Invite** button is still teal
  (grey "Invited today" = already done), picks the first date location, fast-forwards with **Skip**,
  and at the end **Send Gift** (doubles the Affinity gained) or Leave. Stops when the daily cap hits.
- **Mail / Delivery Service** (gifts, **10/day account-wide**): opens the Mail tab, picks the target
  character, sends gifts one by one, and stops the moment the Affinity bar stops moving (= cap reached).

| Card | Options |
|---|---|
| Invite | number of invites (default 5) · send gift at date end · priority targets by name (favorites get dated first; needs a portrait crop per favorite, otherwise grid order is used) |
| Mail | gifts per day (default 10) · per-character rows (name + quantity, total ≤ 10) · or "always the top character" checkbox |

### 12. `FriendGift` — Friend stamina exchange · *ON by default*
Opens the **Friends** screen (two-people icon, top-right) → **Acquire All** (claim stamina your
friends sent) + **Gift All** (send yours back). Runs right before DailyReward so the day's exchange
is counted.

### 13. `DailyReward` — Daily missions
Opens **Missions** (button 2) → Daily tab → **Claim All** the missions plus the activity-point
milestones (e.g. 100 Stellanite Dust).

![Missions screen](images/missions.png)

### 14. `Cleanup` — Tidy up & finish
Returns the game to Home. If **"Close game on Cleanup"** is enabled in Settings, fully closes the game.

### (Bonus) Daily Check-in
Lives in the **Menu** (button 8) → **Daily Check-in**. The Menu also holds the game's **Settings**
(resolution), Redeem Code, etc.

![Game menu](images/menu.png)

---

## E. The automatic scheduler

- Every task has an **on/off** toggle and a **"next run"** timestamp (`next_run`).
- Press **Start** → the scheduler runs whatever is due, and each finished task **reschedules itself**:
  - Daily tasks → next **daily reset**.
  - Tasks short on resources (Dispatch with no squads back, not enough Vigor…) → retry in
    **minutes/hours**.
- You can leave it running **24/7**: it loops, runs on time, and recovers from errors on its own
  (saving logs + screenshots).
- To run one task by hand: **Run now** (GUI) or `python sst.py <Task>` (CLI).

> Pressing **Stop** **interrupts the current task immediately** (at the next screenshot/click —
> a few seconds at most) and then stops the scheduler. An interrupted task is **not penalized** —
> the next Start simply runs it again from the beginning, and the game is left untouched (the tool
> just stops pressing buttons; anything half-done in-game stays as is). Closing the app/exe outright
> kills the process mid-action → prefer pressing Stop first.

---

## F. Troubleshooting

| Symptom | Cause & fix |
|---|---|
| Resolution error / stops immediately | Emulator is not at **1280×720** → fix it in the emulator's settings |
| "Cannot connect to `<serial>`" | Wrong **serial** or **adb.exe path**; emulator not open → recheck Settings |
| Misdetected buttons / stuck on an odd screen | A game **UI update** broke a template image → the asset needs re-cropping |
| Task runs but keeps "no-op"-ing | Normal for Dispatch/Bounty when resources aren't ready — it reschedules itself |
| Event won't run | New event's banner not **re-cropped** yet / stage not set → see EventDaily |
| Running the exe on another PC | Update the **serial + adb path** for that machine's emulator |

> Logs & error screenshots are saved to the `log/` folder next to `app.exe` — attach them when
> asking for help.

---

📚 Related docs: [README](../README_EN.md) · [CHANGELOG_EN](../CHANGELOG_EN.md) ·
`docs/game-map.md` (navigation map) · `docs/ascension-strategy.md` (Ascension strategy).

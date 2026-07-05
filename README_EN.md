# Stella Sora Tool (SST)

[Tiếng Việt](README.md) | **English**

A tool that automates the daily routine for **Stella Sora (EN server)** on an Android emulator.
Architecture inspired by [AzurLaneAutoScript (ALAS)](https://github.com/LmeSzinc/AzurLaneAutoScript):
control via ADB, screen recognition by template matching (OpenCV), a scheduler that queues each task.

> ⚠️ This is a **personal, non-commercial project** for learning purposes. Please read the
> [Disclaimer & Terms of Use](#️-disclaimer--terms-of-use) before using it.

---

## 🚀 Just want to run the tool? (no Python needed)

For end users — **nothing to install besides an emulator**:

1. Go to **[Releases](https://github.com/lamtehe7-hash/stella-sora-tool/releases)** → download the
   latest `StellaSoraTool-vX.Y.Z-win64.zip`.
2. **Extract the whole folder** to your drive — keep `app.exe`, `_internal/` and `assets/` together
   (don't separate them).
3. Open an Android emulator (**MuMu Player** recommended), enable **ADB**, and log into
   **Stella Sora (EN)** at the Home screen.
4. Run **`app.exe`**. First time: open **Settings** and enter your **ADB serial**
   (e.g. `127.0.0.1:16384`) and the **adb.exe path**.
5. Enable the tasks you want → hit **Start**.

> `config/` and `log/` are created next to `app.exe` on first launch. No Python required.

📖 Full task list & config options: **[CHANGELOG_EN.md](CHANGELOG_EN.md)**.

---

## 📋 Available tasks

`Login` · `Mail` · `Dispatch` (Commission) · `Shop` · `BountyTrial` · `Ascension` · `EventDaily` ·
`Grant` · `DailyReward` · `Cleanup`

See full descriptions in [CHANGELOG_EN.md](CHANGELOG_EN.md).

---

## 🛠️ Run from source (for developers)

### Install

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
```

Requirements: an Android emulator running the game at **1280x720** (tested on MuMu Player Global),
the `adb.exe` shipped with the emulator.

### Run

| Command | Mode |
|---|---|
| `python app.py` | Alas-style desktop app (WebView2 window, recommended) |
| `python gui.py` | Web UI at http://localhost:22270 |
| `python sst.py` | CLI — 24/7 scheduler loop |
| `python sst.py <Task>` | CLI — run one task and exit |

The first run creates `config/stella.json` — set the **serial** and **adb.exe path** for your emulator.

### Build exe

```powershell
venv\Scripts\pyinstaller.exe --noconfirm app.spec
```

Output: `dist\app\app.exe` + `_internal\` + `assets\`. `assets/` must sit **next to the exe**;
`config/` and `log/` are created next to the exe at runtime.

---

## ⚖️ Disclaimer & Terms of Use

Please read carefully before downloading or using. **By downloading/using this tool, you agree to all of the terms below.**

- **Personal, non-commercial project.** Built for learning and research into automation. It is not a
  commercial product.
- **Not affiliated with the game developer.** This project is **not** sponsored, endorsed by, or
  affiliated with YoStar or the developers/publishers of Stella Sora in any way. "Stella Sora" and all
  related trademarks, logos and assets belong to their respective owners.
- **Free — commercial and illegal use are STRICTLY PROHIBITED.** In particular, you may not:
  - Sell, rent, charge for distributing, or repackage this tool for profit.
  - Use it to run boosting-for-hire services, or to trade accounts/in-game resources illegally.
  - Use it for any **unlawful** purpose (fraud, scams, money laundering, sabotage, etc.).
- **Account risk.** Automation may violate the game's Terms of Service (ToS/EULA) and can result in an
  **account ban**. You use it **entirely at your own risk**.
- **No warranty.** The software is provided "AS IS", without warranty of any kind. The author is **not
  liable** for any damages, loss of accounts/virtual assets, or legal consequences arising from use or
  misuse of the tool.
- **Privacy.** The tool does **not** collect or transmit any account information; all configuration
  (serial/adb) is entered by you and stored **locally** only.
- **Takedown on request.** If the game developer or a legitimate rights holder requests it, the project
  will cease distribution.

---

## 📄 License

Released under the **[PolyForm Noncommercial License 1.0.0](LICENSE)** — you may use, modify and share
it for **noncommercial** purposes; **any commercial use is prohibited**.

## 📚 Documentation

- [CHANGELOG_EN.md](CHANGELOG_EN.md) / [CHANGELOG_VN.md](CHANGELOG_VN.md) — release details.
- `docs/game-map.md` — in-game screen / navigation map.

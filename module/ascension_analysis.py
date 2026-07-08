"""Phân tích phiên capture Ascension — THUẦN XÁC ĐỊNH, KHÔNG cần AI.

Đọc `frames.jsonl` (coin timeline) + `session.log` (mọi quyết định của tool) trong 1 thư mục
`data/ascension_capture/<ts>/` rồi tính các chỉ số. Tách 2 nhóm:
- `player`: chỉ số người chơi quan tâm (số run, thời gian, coin, mua potential/note, enhance, event).
- `technical`: chỉ số gỡ lỗi tool (OCR fail, dao động chọn thẻ, lệch coin, crash).

Dùng bởi: `dev_tools/analyze_capture.py` (CLI) và `app.py` (giao diện) — cùng 1 engine, không nhân đôi.
"""
from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

# --- regex quyết định trong session.log (đã kiểm chứng trên phiên 20260707_140335) ---
_RUN_ENTER = re.compile(r"đã vào run (\d+)/")
_PATTERNS = {
    "purchase":     re.compile(r"đã mua slot(\d+) \((SALE )?(\d+)\) — còn (\d+|None)"),
    "melody_skip":  re.compile(r"slot(\d+) Melody không Harmony"),
    "event":        re.compile(r"event (\d+) option -> y=(\d+) \((.+?)\)"),
    "enhance":      re.compile(r"Enhance bậc (\d+) \((Free|\d+) coin"),
    "enh_estimate": re.compile(r"không đọc được giá enhance — ước tính (\d+)"),
    "card_select":  re.compile(r"Select thẻ x=(\d+)"),
    "card_osc":     re.compile(r"dao động chọn thẻ"),
    "refresh_shelf": re.compile(r"refresh kệ lượt"),
    "refresh_card":  re.compile(r"refresh bộ thẻ"),
    "leave":        re.compile(r"Leave Monolith"),
    "coin_recon":   re.compile(r"số dư \d+ != kỳ vọng sau enhance"),
}
_CRASH = re.compile(r"(AdbError|Traceback|\[capture\] Task lỗi|RequestHumanTakeover)")


def _fmt_hms(sec: float) -> str:
    sec = int(sec)
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}h{m:02d}m{s:02d}s" if h else f"{m}m{s:02d}s"


def _read_frames(path: Path) -> dict[int, list]:
    """run -> [(ts_ms, coins)] theo thứ tự."""
    frames: dict[int, list] = defaultdict(list)
    if not path.exists():
        return frames
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "run" not in o:
                continue
            frames[o["run"]].append((o.get("ts_ms"), o.get("coins")))
    return frames


def analyze_session(session_dir) -> dict:
    """Phân tích 1 thư mục capture. Trả dict metrics (player + technical + per_run).
    Chịu được file thiếu (trả các trường None/0). KHÔNG ném lỗi nếu chỉ thiếu 1 nguồn."""
    d = Path(session_dir)
    if not d.exists():
        raise FileNotFoundError(f"Không thấy thư mục phiên: {d}")

    config = {}
    cfg_p = d / "config_used.json"
    if cfg_p.exists():
        try:
            config = json.loads(cfg_p.read_text(encoding="utf-8"))
        except Exception:
            config = {}

    frames = _read_frames(d / "frames.jsonl")
    frames_total = sum(len(v) for v in frames.values())

    # coin theo run (bỏ run 0 = setup)
    run_ids = sorted(r for r in frames if r >= 1)

    def coin_peak(run):
        cs = [c for _, c in frames.get(run, []) if c is not None]
        return max(cs) if cs else None

    def coin_last(run):
        for _, c in reversed(frames.get(run, [])):
            if c is not None:
                return c
        return None

    def run_dur(run):
        fr = [t for t, _ in frames.get(run, []) if t is not None]
        return (fr[-1] - fr[0]) / 1000 if len(fr) >= 2 else 0.0

    # --- parse session.log theo run ---
    per = defaultdict(lambda: defaultdict(int))
    per_spend_buy = defaultdict(int)      # coin tiêu mua slot / run
    per_spend_enh = defaultdict(int)      # coin tiêu enhance / run
    per_buy_potion = defaultdict(int)     # mua slot 0-3 (Potion/Drink)
    per_buy_melody = defaultdict(int)     # mua slot 4-7 (Melody note)
    warnings = 0
    crash = None
    cur = 0

    log_p = d / "session.log"
    if log_p.exists():
        for ln in log_p.read_text(encoding="utf-8", errors="replace").splitlines():
            if "| WARNING |" in ln:
                warnings += 1
            if crash is None and _CRASH.search(ln) and ("ERROR" in ln or "Traceback" in ln
                                                         or "AdbError" in ln):
                crash = ln.strip()[:200]
            m = _RUN_ENTER.search(ln)
            if m:
                cur = int(m.group(1))
                continue
            for key, rgx in _PATTERNS.items():
                mm = rgx.search(ln)
                if not mm:
                    continue
                per[cur][key] += 1
                if key == "purchase":
                    slot = int(mm.group(1))
                    price = int(mm.group(3))
                    per_spend_buy[cur] += price
                    if slot >= 4:
                        per_buy_melody[cur] += 1
                    else:
                        per_buy_potion[cur] += 1
                elif key == "enhance":
                    per_spend_enh[cur] += 0 if mm.group(2) == "Free" else int(mm.group(2))

    def total(key):
        return sum(per[r][key] for r in per)

    # per-run bảng (chỉ run >=1)
    per_run = []
    for r in run_ids:
        per_run.append({
            "run": r,
            "dur_sec": round(run_dur(r)),
            "coin_peak": coin_peak(r),
            "coin_last": coin_last(r),
            "potion_bought": per_buy_potion[r],
            "melody_bought": per_buy_melody[r],
            "enhances": per[r]["enhance"],
            "events": per[r]["event"],
            "coin_spent": per_spend_buy[r] + per_spend_enh[r],
        })

    runs_completed = len(run_ids)
    # thời gian tổng: ưu tiên summary.json, else từ frames
    elapsed = None
    sm_p = d / "summary.json"
    if sm_p.exists():
        try:
            elapsed = json.loads(sm_p.read_text(encoding="utf-8")).get("elapsed_sec")
        except Exception:
            elapsed = None
    if elapsed is None:
        all_ts = [t for r in frames for t, _ in frames[r] if t is not None]
        elapsed = (max(all_ts) - min(all_ts)) / 1000 if len(all_ts) >= 2 else 0

    lasts = [coin_last(r) for r in run_ids if coin_last(r) is not None]
    peaks = [coin_peak(r) for r in run_ids if coin_peak(r) is not None]
    median = lambda xs: sorted(xs)[len(xs) // 2] if xs else None

    player = {
        "runs_completed": runs_completed,
        "target_runs": config.get("runs_per_session"),
        "map": config.get("map") or "(giữ game nhớ)",
        "difficulty": config.get("difficulty"),
        "objective": config.get("objective"),
        "total_time": _fmt_hms(elapsed),
        "avg_run_time": _fmt_hms(elapsed / runs_completed) if runs_completed else "—",
        "potion_bought": sum(per_buy_potion.values()),
        "melody_bought": sum(per_buy_melody.values()),
        "melody_skipped": total("melody_skip"),
        "enhances": total("enhance"),
        "events": total("event"),
        "cards_picked": total("card_select"),
        "shelf_refreshes": total("refresh_shelf"),
        "coin_spent_buy": sum(per_spend_buy.values()),
        "coin_spent_enhance": sum(per_spend_enh.values()),
        "coin_peak_avg": round(sum(peaks) / len(peaks)) if peaks else None,
        "coin_leftover_median": median(lasts),
    }
    technical = {
        "frames_total": frames_total,
        "warnings_total": warnings,
        "enhance_ocr_fail": total("enh_estimate"),
        "card_oscillation": total("card_osc"),
        "coin_recon_mismatch": total("coin_recon"),
        "crash": crash,
        "completed": sm_p.exists() and crash is None,
    }
    return {
        "session": d.name,
        "session_dir": str(d),
        "config": config,
        "player": player,
        "technical": technical,
        "per_run": per_run,
    }


def image_dirs(session_dir) -> list[Path]:
    """Danh sách thư mục ảnh (run_* / *_setup) — thứ chiếm ổ, có thể dọn sau khi phân tích."""
    d = Path(session_dir)
    return sorted(p for p in d.glob("run_*") if p.is_dir())


def images_size_bytes(session_dir) -> int:
    total = 0
    for rd in image_dirs(session_dir):
        for f in rd.rglob("*"):
            if f.is_file():
                try:
                    total += f.stat().st_size
                except OSError:
                    pass
    return total


def cleanup_images(session_dir) -> dict:
    """Xoá các thư mục ảnh (run_*), GIỮ frames.jsonl + session.log + summary.json + báo cáo.
    Trả {removed_dirs, freed_bytes}. An toàn: chỉ xoá thư mục con tên run_*."""
    dirs = image_dirs(session_dir)
    freed = images_size_bytes(session_dir)
    removed = 0
    for rd in dirs:
        try:
            shutil.rmtree(rd)
            removed += 1
        except OSError:
            pass
    return {"removed_dirs": removed, "freed_bytes": freed}


def _fmt_mb(b) -> str:
    return f"{b / 1024 / 1024:.1f} MB" if b else "0 MB"


def render_report_md(data: dict) -> str:
    """Kết xuất báo cáo Markdown (cho xuất file người dùng lưu)."""
    p, t = data["player"], data["technical"]
    L = [
        f"# Báo cáo phiên Ascension — {data['session']}",
        "",
        f"- Map: **{p['map']}** · Difficulty: **{p['difficulty']}** · Mục tiêu: **{p['objective']}**",
        f"- Số run hoàn tất: **{p['runs_completed']}"
        + (f"/{p['target_runs']}**" if p['target_runs'] else "**"),
        f"- Tổng thời gian: **{p['total_time']}** · TB mỗi run: **{p['avg_run_time']}**",
        "",
        "## Người chơi",
        f"| Chỉ số | Giá trị |",
        f"|---|---|",
        f"| Potential/Drink đã mua | {p['potion_bought']} |",
        f"| Melody note đã mua | {p['melody_bought']} |",
        f"| Melody bỏ qua (không cần Harmony) | {p['melody_skipped']} |",
        f"| Lượt Enhance | {p['enhances']} |",
        f"| Event đã xử lý | {p['events']} |",
        f"| Thẻ đã chọn | {p['cards_picked']} |",
        f"| Refresh kệ (phòng cuối) | {p['shelf_refreshes']} |",
        f"| Coin tiêu mua hàng | {p['coin_spent_buy']} |",
        f"| Coin tiêu enhance | {p['coin_spent_enhance']} |",
        f"| Coin đỉnh TB/run | {p['coin_peak_avg']} |",
        f"| Coin dư khi rời (median) | {p['coin_leftover_median']} |",
        "",
        "## Kỹ thuật (độ tin cậy tool)",
        f"- Frame chụp: {t['frames_total']} · Cảnh báo: {t['warnings_total']}",
        f"- OCR giá enhance hỏng: {t['enhance_ocr_fail']} · Dao động chọn thẻ: {t['card_oscillation']}"
        f" · Lệch coin: {t['coin_recon_mismatch']}",
        f"- Hoàn tất trọn vẹn: {'CÓ' if t['completed'] else 'KHÔNG'}"
        + (f" · Crash: `{t['crash']}`" if t['crash'] else ""),
        "",
        "## Từng run",
        "| Run | Thời gian | Coin đỉnh | Coin dư | Potion | Melody | Enhance | Event | Coin tiêu |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in data["per_run"]:
        L.append(f"| {r['run']} | {_fmt_hms(r['dur_sec'])} | {r['coin_peak']} | {r['coin_last']} "
                 f"| {r['potion_bought']} | {r['melody_bought']} | {r['enhances']} | {r['events']} "
                 f"| {r['coin_spent']} |")
    L.append("")
    L.append("_Sinh bởi module/ascension_analysis.py (thuần Python, không dùng AI)._")
    return "\n".join(L)


def render_report_text(data: dict) -> str:
    """Bản console gọn (cho CLI)."""
    p, t = data["player"], data["technical"]
    out = [
        f"=== Phiên {data['session']} — {p['map']} Diff{p['difficulty']} ({p['objective']}) ===",
        f"Run hoàn tất : {p['runs_completed']}"
        + (f"/{p['target_runs']}" if p['target_runs'] else "")
        + f"   | Thời gian {p['total_time']} (TB {p['avg_run_time']}/run)",
        f"Mua          : {p['potion_bought']} potion, {p['melody_bought']} melody "
        f"(bỏ {p['melody_skipped']}), {p['enhances']} enhance",
        f"Coin         : tiêu mua {p['coin_spent_buy']} + enhance {p['coin_spent_enhance']} "
        f"| đỉnh TB {p['coin_peak_avg']} | dư median {p['coin_leftover_median']}",
        f"Event/Thẻ    : {p['events']} event, {p['cards_picked']} thẻ, {p['shelf_refreshes']} refresh kệ",
        f"[Kỹ thuật] {t['warnings_total']} cảnh báo | OCR-enh fail {t['enhance_ocr_fail']} "
        f"| card-osc {t['card_oscillation']} | "
        + ("HOÀN TẤT" if t['completed'] else f"CHƯA XONG ({t['crash'] or 'dừng giữa chừng'})"),
    ]
    return "\n".join(out)

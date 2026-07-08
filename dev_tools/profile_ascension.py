# -*- coding: utf-8 -*-
"""Profile thời gian 1 phiên capture Ascension: gap giữa các dòng session.log được quy cho
hành động ĐẾN SAU gap (= "đã chờ bao lâu để tới hành động này"), gộp theo signature
(message đã strip số). Kèm cadence screenshot từ frames.jsonl.

Dùng: venv\\Scripts\\python.exe dev_tools\\profile_ascension.py data\\ascension_capture\\<session_ts>
(cần PYTHONIOENCODING=utf-8 trên console cp1252)

Kết quả nền 2026-07-08 (phiên 20260707_140335 26-run + 20260708_130704 1-run):
- p50 gap giữa 2 screenshot 2.13s; sleep cố định chiếm ~70-80%% thời gian run.
- Screenshot PNG chỉ ~0.32s — KHÔNG phải bottleneck (RAW đo 0.50s, CHẬM hơn vì transfer 3.5MB).
- Top bồn: dismiss Notes ~120s/run, chọn thẻ ~180s, mua slot ~130s, dispatch ~80s, OCR-miss ~27s.
Chi tiết + gói tối ưu đề xuất: HANDOVER.md §10 phiên 2026-07-08 (chiều).
"""
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

d = Path(sys.argv[1])
RUN_ENTER = re.compile(r"đã vào run (\d+)/|vào run mới (\d+)")
TS = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) \| (\w+)\s*\| (.*)$")


def sig(msg: str) -> str:
    s = re.sub(r"\d+", "N", msg)
    return s[:90]


events = []  # (dt, msg)
run_of = []  # run id per event
cur = 0
for ln in (d / "session.log").read_text(encoding="utf-8", errors="replace").splitlines():
    m = TS.match(ln)
    if not m:
        continue
    t = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timestamp() + int(m.group(2)) / 1000
    msg = m.group(4)
    r = RUN_ENTER.search(msg)
    if r:
        cur = int(r.group(1) or r.group(2))
    events.append((t, msg))
    run_of.append(cur)

# gaps trong run (bỏ run 0 = setup/nav) quy cho message ĐẾN SAU
agg_t = defaultdict(float)
agg_n = defaultdict(int)
run_dur = defaultdict(float)
for i in range(1, len(events)):
    if run_of[i] < 1:
        continue
    gap = events[i][0] - events[i - 1][0]
    if gap < 0 or gap > 600:
        continue
    agg_t[sig(events[i][1])] += gap
    agg_n[sig(events[i][1])] += 1
    run_dur[run_of[i]] += gap

nruns = len(run_dur)
if not nruns:
    sys.exit(f"Không tìm thấy run nào trong {d / 'session.log'} (marker 'đã vào run N/').")
tot = sum(run_dur.values())
print(f"=== {d.name}: {nruns} run, tổng {tot/60:.1f} phút, TB {tot/nruns/60:.2f} phút/run ===")
durs = sorted(run_dur.values())
print(f"run duration min/median/max: {durs[0]/60:.1f} / {durs[len(durs)//2]/60:.1f} / {durs[-1]/60:.1f} phút")

print(f"\n--- TOP 30 bồn thời gian (tổng {nruns} run; giây/run = chia đều) ---")
rows = sorted(agg_t.items(), key=lambda kv: -kv[1])[:30]
for s, tsec in rows:
    n = agg_n[s]
    print(f"{tsec/nruns:7.1f}s/run  x{n/nruns:5.1f}  ({tsec/n:5.2f}s/lần)  {s}")

# frames.jsonl: cadence screenshot
fp = d / "frames.jsonl"
if fp.exists():
    ts_by_run = defaultdict(list)
    for line in fp.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("run", 0) >= 1 and o.get("ts_ms"):
            ts_by_run[o["run"]].append(o["ts_ms"])
    nf = sum(len(v) for v in ts_by_run.values())
    gaps = []
    for v in ts_by_run.values():
        gaps += [(b - a) / 1000 for a, b in zip(v, v[1:]) if 0 <= b - a < 60000]
    gaps.sort()
    if gaps:
        print(f"\n--- frames.jsonl: {nf} screenshot / {len(ts_by_run)} run = {nf/len(ts_by_run):.0f} shot/run ---")
        print(f"gap giữa 2 shot p50/p75/p90: {gaps[len(gaps)//2]:.2f} / {gaps[int(len(gaps)*.75)]:.2f} / {gaps[int(len(gaps)*.9)]:.2f}s")
        print(f"tổng thời gian là 'giữa 2 shot liên tiếp <2s' (≈ chuỗi poll dày): "
              f"{sum(g for g in gaps if g < 2)/len(ts_by_run):.0f}s/run")

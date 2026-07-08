"""Gộp glyph OCR bị nhận-diện-hụt (log/coin_glyphs, log/lv_glyphs) vào bộ template số — KHÔNG cần AI.

Khi OCR số coin/giá enhance (`_read_number`) hoặc level thẻ (`_classify_digit`) gặp glyph lạ (score
dưới ngưỡng), tool TỰ lưu glyph vào `log/<kind>_glyphs/`. Script này giúp DÁN NHÃN chúng rồi thêm làm
template variant để OCR khá lên dần (coin dùng LIST biến thể → thêm là có hiệu lực ngay).

Quy trình:
  1) venv\\Scripts\\python.exe dev_tools\\rebuild_digits.py --review
     → sinh montage `log/glyph_review/<kind>_review.png` (glyph phóng to + số thứ tự) + `labels_<kind>.csv`.
  2) Mở montage xem, điền cột `digit` (0-9) trong CSV cho glyph ĐỌC ĐƯỢC; để TRỐNG glyph rác (sẽ bỏ qua).
  3) venv\\Scripts\\python.exe dev_tools\\rebuild_digits.py --apply
     → cài mỗi glyph có nhãn thành `assets/.../d<digit>_g<stem>.png`, chuyển glyph đã xử lý sang
       `log/glyph_review/done/`. Chạy Ascension lần sau là template mới có hiệu lực.

`--stats` (mặc định): chỉ đếm glyph đang chờ.
"""
import argparse
import csv
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "log" / "glyph_review"
KINDS = {
    "coin": (ROOT / "log" / "coin_glyphs", ROOT / "assets" / "en" / "ascension" / "coin_digits"),
    "lv":   (ROOT / "log" / "lv_glyphs",   ROOT / "assets" / "en" / "ascension" / "digits"),
}


def _glyphs(src: Path) -> list:
    if not src.exists():
        return []
    return sorted(p for p in src.glob("*.png") if p.is_file())


def _montage(glyphs: list, cols: int = 10, tile=(56, 72), pad: int = 6) -> np.ndarray:
    rows = (len(glyphs) + cols - 1) // cols
    cw, ch = tile[0] + pad * 2, tile[1] + pad * 2 + 16
    canvas = np.full((max(1, rows) * ch, cols * cw, 3), 40, np.uint8)
    for i, p in enumerate(glyphs):
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        r, c = divmod(i, cols)
        big = cv2.cvtColor(cv2.resize(img, tile, interpolation=cv2.INTER_NEAREST), cv2.COLOR_GRAY2BGR)
        y0, x0 = r * ch + 16 + pad, c * cw + pad
        canvas[y0:y0 + tile[1], x0:x0 + tile[0]] = big
        cv2.putText(canvas, str(i), (c * cw + pad, r * ch + 13),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80, 255, 80), 1, cv2.LINE_AA)
    return canvas


def do_review() -> None:
    REVIEW.mkdir(parents=True, exist_ok=True)
    any_g = False
    for kind, (src, _dst) in KINDS.items():
        glyphs = _glyphs(src)
        if not glyphs:
            print(f"[{kind}] 0 glyph chờ xử lý.")
            continue
        any_g = True
        cv2.imwrite(str(REVIEW / f"{kind}_review.png"), _montage(glyphs))
        csv_p = REVIEW / f"labels_{kind}.csv"
        with open(csv_p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["idx", "file", "digit"])
            for i, p in enumerate(glyphs):
                w.writerow([i, p.name, ""])
        print(f"[{kind}] {len(glyphs)} glyph → montage {REVIEW / f'{kind}_review.png'} "
              f"+ {csv_p} (điền cột 'digit' rồi chạy --apply)")
    if not any_g:
        print("Không có glyph nào để review (OCR đang chạy tốt hoặc chưa gặp glyph lạ).")


def do_apply() -> None:
    done = REVIEW / "done"
    done.mkdir(parents=True, exist_ok=True)
    total = 0
    for kind, (src, dst) in KINDS.items():
        csv_p = REVIEW / f"labels_{kind}.csv"
        if not csv_p.exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        with open(csv_p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        n = 0
        for row in rows:
            digit = (row.get("digit") or "").strip()
            # phải đúng 1 ký tự số — `in "0123456789"` là substring check, "23" vẫn lọt (bug review)
            if len(digit) != 1 or not digit.isdigit():
                continue
            src_p = src / row["file"]
            if not src_p.exists():
                continue
            stem = src_p.stem
            out = dst / f"d{digit}_g{stem}.png"
            shutil.copyfile(src_p, out)          # template load tự resize 12x16 -> giữ nguyên crop
            shutil.move(str(src_p), str(done / src_p.name))
            n += 1
        if n:
            print(f"[{kind}] cài {n} template variant vào {dst}, chuyển glyph đã xử lý → {done}")
        total += n
    print(f"Xong: {total} glyph được thêm làm template. Chạy lại tool là có hiệu lực." if total
          else "Chưa có glyph nào được dán nhãn (cột 'digit' trống). Điền CSV rồi chạy lại --apply.")


def do_stats() -> None:
    for kind, (src, dst) in KINDS.items():
        print(f"[{kind}] {len(_glyphs(src))} glyph chờ | "
              f"{len(list(dst.glob('d*.png'))) if dst.exists() else 0} template hiện có ({dst})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gộp glyph OCR hụt vào template số (coin/lv)")
    ap.add_argument("--review", action="store_true", help="sinh montage + CSV nhãn")
    ap.add_argument("--apply", action="store_true", help="cài glyph đã dán nhãn thành template")
    args = ap.parse_args()
    if args.review:
        do_review()
    elif args.apply:
        do_apply()
    else:
        do_stats()


if __name__ == "__main__":
    sys.exit(main())

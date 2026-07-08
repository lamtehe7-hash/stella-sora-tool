"""CLI phân tích phiên capture Ascension — THUẦN XÁC ĐỊNH, KHÔNG cần AI.

    venv\\Scripts\\python.exe dev_tools\\analyze_capture.py [<session_dir hoặc <ts>>] [--json]
                                                            [--export <file.md>] [--cleanup]

- Không truyền session: dùng phiên MỚI NHẤT trong data/ascension_capture/.
- --json     : in JSON metrics đầy đủ (cho máy đọc).
- --export F : ghi báo cáo Markdown ra F (mặc định in ra console dạng text).
- --cleanup  : sau khi phân tích, XOÁ các thư mục ảnh run_* để giải phóng ổ (giữ log + báo cáo).

Engine: module/ascension_analysis.py (dùng chung với giao diện app).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from module.ascension_analysis import (  # noqa: E402
    analyze_session, cleanup_images, images_size_bytes, render_report_md, render_report_text,
)

CAPTURE_ROOT = Path(__file__).resolve().parents[1] / "data" / "ascension_capture"


def _resolve(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if p.exists():
            return p
        p = CAPTURE_ROOT / arg          # cho phép truyền mỗi timestamp
        if p.exists():
            return p
        sys.exit(f"Không thấy phiên: {arg}")
    sessions = sorted(d for d in CAPTURE_ROOT.glob("2*") if d.is_dir())
    if not sessions:
        sys.exit(f"Không có phiên nào trong {CAPTURE_ROOT}")
    return sessions[-1]


def main() -> None:
    ap = argparse.ArgumentParser(description="Phân tích phiên capture Ascension (không cần AI)")
    ap.add_argument("session", nargs="?", help="thư mục phiên hoặc timestamp (mặc định: mới nhất)")
    ap.add_argument("--json", action="store_true", help="in JSON metrics đầy đủ")
    ap.add_argument("--export", metavar="FILE", help="ghi báo cáo Markdown ra file")
    ap.add_argument("--cleanup", action="store_true", help="xoá thư mục ảnh run_* sau khi phân tích")
    args = ap.parse_args()

    d = _resolve(args.session)
    data = analyze_session(d)

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(render_report_text(data))

    if args.export:
        out = Path(args.export)
        out.write_text(render_report_md(data), encoding="utf-8")
        print(f"\n[export] Báo cáo -> {out}")

    if args.cleanup:
        freed = images_size_bytes(d)
        res = cleanup_images(d)
        print(f"[cleanup] Đã xoá {res['removed_dirs']} thư mục ảnh, "
              f"giải phóng {res['freed_bytes'] / 1024 / 1024:.1f} MB "
              f"(ước tính trước dọn {freed / 1024 / 1024:.1f} MB).")


if __name__ == "__main__":
    main()

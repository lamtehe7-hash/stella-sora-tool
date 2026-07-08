"""Cờ "dừng NGAY" toàn cục cho nút [Dừng] của GUI.

Cơ chế: GUI (app.py/gui.py) gọi request_stop() → Device kiểm cờ ở đầu mỗi
screenshot/click/swipe và ném TaskInterrupted → task đang chạy bị ngắt ở thao tác
thiết bị kế tiếp (trễ tối đa ~1 nhịp sleep của task, thường ≤3s). Scheduler bắt
TaskInterrupted riêng: KHÔNG phạt task_delay (next_run giữ nguyên → lần Start sau
chạy lại task dở). Scheduler.run()/run_single() clear cờ lúc bắt đầu để phiên mới
không bị cờ cũ giết.
"""
import threading

_stop_event = threading.Event()


def request_stop() -> None:
    """Yêu cầu ngắt task đang chạy tại thao tác thiết bị kế tiếp."""
    _stop_event.set()


def clear_stop() -> None:
    _stop_event.clear()


def stop_requested() -> bool:
    return _stop_event.is_set()

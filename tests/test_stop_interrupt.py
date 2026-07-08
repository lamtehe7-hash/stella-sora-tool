"""Test cờ Dừng-ngay: module/stop_signal + Device._abort_if_stop_requested + Scheduler.stop().

Chạy trực tiếp (pytest chưa cài): venv\\Scripts\\python.exe tests\\test_stop_interrupt.py
Offline — không cần giả lập: adb thay bằng fake trả PNG tĩnh 1280×720.
"""
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

from module.device.device import Device
from module.exception import TaskInterrupted
from module.stop_signal import clear_stop, request_stop, stop_requested


class FakeAdb:
    def __init__(self):
        self.png = cv2.imencode('.png', np.zeros((720, 1280, 3), np.uint8))[1].tobytes()
        self.taps = []

    def screenshot_png(self):
        return self.png

    def tap(self, x, y):
        self.taps.append((x, y))

    def swipe(self, x1, y1, x2, y2, duration_ms=300):
        pass


class _Emu:
    serial, adb_path, package = 'dummy', 'dummy', 'dummy'


class _Cfg:
    emulator = _Emu()


def make_device() -> Device:
    d = Device(_Cfg())
    d.adb = FakeAdb()
    return d


def test_normal_when_flag_clear():
    clear_stop()
    d = make_device()
    assert d.screenshot().shape[:2] == (720, 1280), 'screenshot phải chạy bình thường khi chưa Dừng'
    d.click_xy(10, 20, 'TEST')
    assert d.adb.taps == [(10, 20)], 'click phải tap bình thường khi chưa Dừng'
    print('PASS: flag clear -> screenshot/click hoạt động bình thường')


def test_interrupt_when_flag_set():
    d = make_device()
    request_stop()
    for op, call in [('screenshot', d.screenshot),
                     ('click_xy', lambda: d.click_xy(1, 2, 'TEST')),
                     ('swipe', lambda: d.swipe(0, 0, 9, 9))]:
        try:
            call()
            raise AssertionError(f'{op} phải ném TaskInterrupted khi cờ Dừng đã set')
        except TaskInterrupted:
            pass
    assert d.adb.taps == [], 'không được tap thêm phát nào sau khi bấm Dừng'
    clear_stop()
    print('PASS: flag set -> screenshot/click/swipe ném TaskInterrupted, không tap thêm')


def test_scheduler_stop_sets_flag():
    from module.scheduler import Scheduler
    clear_stop()
    s = Scheduler()  # chỉ init, không start thread
    s.stop()
    assert s.stopping and stop_requested(), 'Scheduler.stop() phải set cả cờ vòng lặp lẫn cờ dừng-ngay'
    clear_stop()
    print('PASS: Scheduler.stop() set cờ dừng-ngay toàn cục')


def test_clear_resets():
    request_stop()
    clear_stop()
    assert not stop_requested()
    d = make_device()
    assert d.screenshot().shape[:2] == (720, 1280), 'sau clear_stop phải chạy lại bình thường'
    print('PASS: clear_stop reset — phiên mới không bị cờ cũ giết')


if __name__ == '__main__':
    test_normal_when_flag_clear()
    test_interrupt_when_flag_set()
    test_scheduler_stop_sets_flag()
    test_clear_resets()
    print('ALL PASS (4 case)')

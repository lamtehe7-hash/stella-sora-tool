"""Test retry/reconnect của module.device.adb.Adb.shell() — dev-only, KHÔNG cần giả lập thật.

Chạy:  venv\\Scripts\\python.exe tests\\test_adb_retry.py
       (hoặc `pytest tests/test_adb_retry.py` nếu đã cài pytest)

Bảo vệ hồi quy cho fix P0 (2026-07-07): 1 lần rớt ADB (AdbError:closed) giữa phiên dài KHÔNG được
giết cả session — phải tự reconnect + thử lại; cạn retry mới RequestHumanTakeover; lỗi LOGIC không bị nuốt;
connect() tự ném lỗi retryable giữa chừng cũng phải được retry (không thoát vòng).
"""
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import adbutils  # noqa: E402
import module.device.adb as adbmod  # noqa: E402
from module.device.adb import Adb  # noqa: E402
from module.exception import (EmulatorNotRunningError, GameStuckError,  # noqa: E402
                              RequestHumanTakeover)


@contextmanager
def _no_sleep():
    """Bỏ chờ backoff cho test nhanh — patch CÓ scope + restore (patch import-time trước đây
    đổi time.sleep của cả process, sẽ phá test module khác khi tests/ có thêm file)."""
    orig = adbmod.time.sleep
    adbmod.time.sleep = lambda s: None
    try:
        yield
    finally:
        adbmod.time.sleep = orig


def test_transient_then_recover():
    """Rớt transient 2 lần rồi hồi phục → trả kết quả, có reconnect."""
    st = {"n": 0, "connects": 0}

    class FakeDev:
        def shell(self, cmd, encoding="utf-8"):
            st["n"] += 1
            if st["n"] <= 2:
                raise adbutils.AdbError("closed")
            return "OK"

    a = Adb("127.0.0.1:16384", "adb")
    a.connect = lambda: (st.__setitem__("connects", st["connects"] + 1),
                         setattr(a, "_device", FakeDev()))
    a._device = FakeDev()
    with _no_sleep():
        assert a.shell("input tap 1 1") == "OK"
    assert st["n"] == 3 and st["connects"] == 2


def test_connect_raise_mid_retry():
    """connect() TỰ ném lỗi retryable (giả lập chưa sẵn sàng lại) giữa vòng retry → vẫn được
    retry tiếp (self.device nằm TRONG try của shell()), không thoát vòng, hồi phục OK."""
    st = {"n": 0, "connects": 0}

    class FakeDev:
        def shell(self, cmd, encoding="utf-8"):
            st["n"] += 1
            if st["n"] == 1:
                raise adbutils.AdbError("closed")
            return "OK"

    a = Adb("127.0.0.1:16384", "adb")

    def fake_connect():
        st["connects"] += 1
        if st["connects"] == 1:
            raise EmulatorNotRunningError("giả lập chưa sẵn sàng lại")
        a._device = FakeDev()

    a.connect = fake_connect
    a._device = FakeDev()
    with _no_sleep():
        assert a.shell("input tap 1 1") == "OK"
    # attempt0: shell rớt → attempt1: connect() ném (retryable, bị bắt) → attempt2: connect OK + shell OK
    assert st["connects"] == 2 and st["n"] == 2


def test_exhausted_raises_takeover():
    """Rớt mãi → RequestHumanTakeover sau 4 lần thử (1 + 3 retry), không crash trần."""
    st = {"n": 0}

    class FailDev:
        def shell(self, cmd, encoding="utf-8"):
            st["n"] += 1
            raise adbutils.AdbError("closed")

    b = Adb("127.0.0.1:16384", "adb")
    b.connect = lambda: setattr(b, "_device", FailDev())
    b._device = FailDev()
    try:
        with _no_sleep():
            b.shell("input tap 1 1")
        assert False, "phải ném RequestHumanTakeover"
    except RequestHumanTakeover:
        pass
    assert st["n"] == 4


def test_logic_error_passthrough():
    """Lỗi LOGIC (GameStuckError) KHÔNG nằm trong whitelist → không retry, ném thẳng."""
    class LogicDev:
        def shell(self, cmd, encoding="utf-8"):
            raise GameStuckError("stuck")

    c = Adb("127.0.0.1:16384", "adb")
    c._device = LogicDev()
    try:
        c.shell("x")
        assert False, "phải ném GameStuckError"
    except GameStuckError:
        pass


if __name__ == "__main__":
    fails = 0
    for fn in (test_transient_then_recover, test_connect_raise_mid_retry,
               test_exhausted_raises_takeover, test_logic_error_passthrough):
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{'ALL PASS' if not fails else f'{fails} FAIL'}")
    sys.exit(1 if fails else 0)

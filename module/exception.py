class EmulatorNotRunningError(Exception):
    """Không kết nối được giả lập qua ADB."""


class GameStuckError(Exception):
    """Màn hình không tiến triển / không nhận diện được page nào."""


class GameTooManyClickError(Exception):
    """Click lặp cùng một nút quá nhiều lần — flow đang kẹt vòng."""


class AssetMissingError(Exception):
    """File ảnh template chưa tồn tại — cần crop bằng dev_tools/crop.py."""


class TaskError(Exception):
    """Task thất bại có kiểm soát — scheduler sẽ hẹn chạy lại sau."""


class RequestHumanTakeover(Exception):
    """Lỗi không tự phục hồi được — dừng tool, cần người can thiệp."""

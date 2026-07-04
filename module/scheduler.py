"""Scheduler chạy được 2 chế độ: blocking (CLI sst.py) và thread có nút dừng (GUI).

Registry TASKS đặt ở đây để sst.py lẫn gui.py dùng chung.
"""
import threading

from module.base.button import set_server
from module.config import Config, utcnow
from module.device.device import Device
from module.exception import (GameStuckError, GameTooManyClickError,
                              RequestHumanTakeover, TaskError)
from module.logger import logger, save_error_log
from tasks.ascension import Ascension
from tasks.cleanup import Cleanup
from tasks.daily_reward import DailyReward
from tasks.dispatch import Dispatch
from tasks.login import Login
from tasks.mail import Mail
from tasks.shop import Shop
from tasks.stamina import Stamina

TASKS = {
    'Login': Login,
    'Mail': Mail,
    'DailyReward': DailyReward,
    'Dispatch': Dispatch,
    'Shop': Shop,
    'Stamina': Stamina,
    'Ascension': Ascension,  # 1 run Monolith Quick Battle/ngày (mission daily), tốn vé không tốn Vigor
    # Phase 4 còn lại: FriendGift
    'Cleanup': Cleanup,  # luôn cuối: về home / đóng game
}
ORDER = list(TASKS)  # thứ tự khai báo = thứ tự ưu tiên

# Khóa thiết bị: scheduler và "chạy 1 task" từ GUI không được đụng ADB cùng lúc
device_lock = threading.Lock()


def run_task(name: str, config: Config, device: Device) -> None:
    logger.info(f'===== Task: {name} =====')
    TASKS[name](config, device).run()
    logger.info(f'===== Xong: {name}, next_run={config.task(name).next_run} UTC =====')


class Scheduler(threading.Thread):
    """Vòng lặp task chạy nền. stop() dừng SAU khi task hiện tại xong (không ngắt giữa chừng)."""

    daemon = True

    def __init__(self):
        super().__init__(name='sst-scheduler')
        self._stop_event = threading.Event()
        self.state = 'idle'          # idle | running | waiting | stopped | error | human
        self.current_task: str = ''  # task đang chạy (khi state == running)
        self.error: str = ''

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def stopping(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:
        try:
            device = Device(Config.load())
            device.connect()
        except Exception as e:
            self.state, self.error = 'error', str(e)
            logger.error(f'Scheduler không khởi động được: {e}')
            return

        while not self.stopping:
            # Nạp lại config mỗi vòng để thay đổi từ GUI (enable/next_run) có hiệu lực ngay
            config = Config.load()
            set_server(config.server)
            name = config.get_next_task(ORDER)

            if name is None:
                wake = config.next_wake(ORDER)
                if wake is None:
                    logger.info('Không có task nào được bật — scheduler dừng.')
                    break
                sleep_s = max(10, min((wake - utcnow()).total_seconds(), 60))
                self.state = 'waiting'
                self._stop_event.wait(sleep_s)  # ngủ ngắn từng nhịp để nút Dừng ăn ngay
                continue

            self.state, self.current_task = 'running', name
            try:
                with device_lock:
                    run_task(name, config, device)
            except TaskError as e:
                logger.error(f'{name} thất bại: {e} — thử lại sau 30 phút')
                save_error_log(device)
                config.task_delay(name, minutes=30)
            except (GameStuckError, GameTooManyClickError) as e:
                logger.error(f'{name} kẹt: {e}')
                save_error_log(device)
                config.task_delay(name, minutes=60)
            except RequestHumanTakeover:
                save_error_log(device)
                logger.critical('CẦN NGƯỜI CAN THIỆP — scheduler dừng.')
                self.state, self.error = 'human', 'Cần người can thiệp — xem log/error/'
                return
            except Exception as e:  # lỗi bất ngờ: không cho chết thread GUI
                logger.exception(f'{name} lỗi bất ngờ: {e}')
                save_error_log(device)
                config.task_delay(name, minutes=60)
            finally:
                self.current_task = ''

        self.state = 'stopped'
        logger.info('Scheduler đã dừng.')


def run_single(name: str) -> None:
    """Chạy 1 task rồi thoát (CLI hoặc nút 'Chạy ngay' của GUI khi scheduler không chạy)."""
    config = Config.load()
    set_server(config.server)
    device = Device(config)
    device.connect()
    with device_lock:
        run_task(name, config, device)

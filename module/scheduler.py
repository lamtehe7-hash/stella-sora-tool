"""Scheduler chạy được 2 chế độ: blocking (CLI sst.py) và thread có nút dừng (GUI).

Registry TASKS đặt ở đây để sst.py lẫn gui.py dùng chung.
"""
import threading

from module.base.button import set_server
from module.config import Config, utcnow
from module.device.device import Device
from module.exception import (GameStuckError, GameTooManyClickError,
                              RequestHumanTakeover, TaskError, TaskInterrupted)
from module.logger import logger, save_error_log
from module.stop_signal import clear_stop, request_stop
from tasks.ascension import Ascension
from tasks.bounty_trial import BountyTrial
from tasks.cleanup import Cleanup
from tasks.daily_reward import DailyReward
from tasks.dispatch import Dispatch
from tasks.event_daily import EventDaily
from tasks.event_first_clear import EventFirstClear
from tasks.friend_gift import FriendGift
from tasks.grant import Grant
from tasks.heartlink import Heartlink
from tasks.login import Login
from tasks.mail import Mail
from tasks.purchase_gift import PurchaseGift
from tasks.shop import Shop

TASKS = {
    'Login': Login,
    'Mail': Mail,
    'Dispatch': Dispatch,
    'Shop': Shop,
    'PurchaseGift': PurchaseGift,  # nhận Daily Gift free ở màn Purchase (chỉ khi còn quà/chấm đỏ)
    'BountyTrial': BountyTrial,  # (đổi tên từ Stamina) tiêu Vigor: Trial Quick Battle sweep
    'Ascension': Ascension,  # 1 run Monolith Quick Battle/ngày (mission daily), tốn vé không tốn Vigor
    'EventDaily': EventDaily,  # Quick Battle sweep Battle Stage của sự kiện đang diễn ra (theo đợt)
    'EventFirstClear': EventFirstClear,  # tự đánh (Deploy+Auto-Battle) stage sự kiện còn sao xám
    'Grant': Grant,  # nhận quà Startup Grant (Company Goal + Milestone) SAU các task tạo progress
    'Heartlink': Heartlink,  # hẹn hò tăng Affinity (task con Invite + Mail/Delivery) — mặc định TẮT
    'FriendGift': FriendGift,  # trao đổi stamina với bạn (Acquire All + Gift All); TRƯỚC DailyReward
    'DailyReward': DailyReward,  # gần cuối: gom mission + điểm hoạt động SAU khi các task khác xong
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
    """Vòng lặp task chạy nền. stop() ngắt task hiện tại NGAY (TaskInterrupted tại thao tác
    thiết bị kế tiếp — xem module/stop_signal.py) rồi dừng vòng lặp; task bị ngắt không bị
    phạt task_delay nên lần Start sau sẽ chạy lại."""

    daemon = True

    def __init__(self):
        super().__init__(name='sst-scheduler')
        self._stop_event = threading.Event()
        self.state = 'idle'          # idle | running | waiting | stopped | error | human
        self.current_task: str = ''  # task đang chạy (khi state == running)
        self.error: str = ''

    def stop(self) -> None:
        self._stop_event.set()
        request_stop()  # ngắt task đang chạy ngay tại screenshot/click kế tiếp

    @property
    def stopping(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:
        clear_stop()  # cờ Dừng của phiên trước không được giết phiên này
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
            except TaskInterrupted:
                # Người dùng bấm Dừng: không phải lỗi — không save_error_log, không task_delay
                # (next_run giữ nguyên → lần Start sau chạy lại task dở này).
                logger.info(f'{name} bị ngắt theo yêu cầu Dừng của người dùng.')
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
    clear_stop()
    config = Config.load()
    set_server(config.server)
    device = Device(config)
    device.connect()
    with device_lock:
        run_task(name, config, device)

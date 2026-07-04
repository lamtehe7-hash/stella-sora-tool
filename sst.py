"""Stella Sora Tool — entry point CLI.

Chạy vòng lặp scheduler:  python sst.py
Chạy 1 task rồi thoát:    python sst.py Login
Giao diện web (kiểu ALAS): python gui.py
"""
import sys

from module.scheduler import TASKS, Scheduler, run_single


def main() -> None:
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in TASKS:
            print(f'Task không tồn tại: {name}. Có: {", ".join(TASKS)}')
            sys.exit(1)
        run_single(name)
    else:
        sched = Scheduler()
        sched.start()
        try:
            sched.join()
        except KeyboardInterrupt:
            print('Ctrl+C — dừng sau khi task hiện tại xong...')
            sched.stop()
            sched.join()


if __name__ == '__main__':
    main()

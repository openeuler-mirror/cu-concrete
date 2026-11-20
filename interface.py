from whiptail import Whiptail
import os
import sys
# pa=os.path.dirname(os.path.abspath(__file__))
# sys.path.append(pa)
from fixlist import fixlist
# from checklist import sub_checklist
# from rollbacklist import sub_rollbacklist
from checklist import checklist
from rollbacklist import rollbacklist
import json
import logging
from logging.handlers import RotatingFileHandler
import tempfile
from resetlist import resetlist
import time
TITLE = "安全加固工具"
HEIGHT = 25
WIDTH = 60
flag_path='flag.txt'
def main_menu():

    w = Whiptail(title=TITLE, backtitle="主菜单", height=HEIGHT, width=WIDTH)
    choice = w.menu(
        "请选择操作：",
        [
            ("1","加固"),
            ("2","还原"),
            ("3","修复"),
            ("4","日志"),
            ("5","退出")
        ]
    )
    return choice[0]

def text_box():
    w = Whiptail(title=TITLE, backtitle="日志", height=HEIGHT, width=WIDTH)

    log_path = LOG_FILE

    # 日志文件不存在或为空时只提示，不创建内容错误的空日志文件
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        w.msgbox("暂无日志记录")
        return

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.log') as tmpfile:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            tmpfile.write(f.read())
        tmpfile_name = tmpfile.name

    try:
        success = w.textbox(tmpfile_name)
        # 可以根据 success 判断用户是否点击 OK，但通常不需要
    except Exception as e:
        logging.error(f"显示日志失败: {e}")
    finally:
        if os.path.exists(tmpfile_name):
            os.unlink(tmpfile_name)


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(project_root, flag_path) 
    flag=None
    c=checklist()            
    logging.info("=" * 70)
    logging.info("安全加固工具启动（图形界面）")
    try:
        while True:
            if not os.path.exists(log_path):
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("1")
                    flag = 1
            else:
                with open(log_path, 'r', encoding='utf-8') as f:
                    flag = int(f.read().strip())
            if flag == 1:
                # 状态刷新属于界面内部行为，降为 DEBUG，避免每次返回主菜单都刷屏
                logging.debug("开始扫描系统安全状态（首次执行，逐项检测）")
                InstanceTuple = c.sub_checklist()
                flag += 1
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write(str(flag))
                logging.debug("系统安全状态扫描完成")
            else:
                logging.debug("刷新已保存的加固状态")
                InstanceTuple = c.sec_checklist()
            choice = main_menu()
            if choice == "1":
                f = fixlist()
                f.sub_fixlist("加固项", "加固项", InstanceTuple[0])
            elif choice in ["2", "3"]:
                if choice == "2":
                    r = rollbacklist()
                    r.sub_rollbacklist("还原项", "还原项", InstanceTuple[1])
                elif choice == "3":
                    r = resetlist()
                    r.sub_resetlist("修复项", "修复项", InstanceTuple[2])
            elif choice == "4":
                text_box()
            elif choice == "5":
                logging.info("用户选择退出")
                break
    except KeyboardInterrupt:
        logging.info("用户中断操作，程序退出")
    except Exception:
        logging.exception("界面运行发生未捕获异常，程序退出")
    finally:
        logging.info("安全加固工具退出")
        logging.info("=" * 70)


# ---------------- 日志配置 ----------------
# interface.py 位于 /opt/cu-concrete/，日志与 CLI 一并放在 /opt/cu-concrete/logs/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))   # /opt/cu-concrete
LOG_DIR = os.path.join(CURRENT_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")
# 单个日志文件最大 10MB，最多保留 5 个历史文件，防止日志无限增长占满磁盘
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5

LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logging(log_dir=LOG_DIR, log_file=LOG_FILE, level=logging.INFO):
    """全局日志配置：日志写入 /opt/cu-concrete/logs/app.log，支持轮转"""
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 避免重复添加同一个文件的处理器
    target = os.path.abspath(log_file)
    for h in root_logger.handlers[:]:
        if getattr(h, 'baseFilename', None) and os.path.abspath(h.baseFilename) == target:
            root_logger.removeHandler(h)
            h.close()

    root_logger.addHandler(handler)
    logging.getLogger(__name__).info(f"日志初始化完成: {log_file}")


if __name__ == "__main__":
    # 默认 INFO：界面内部的状态刷新等细节用 DEBUG 记录，不落盘；
    # 需要排查问题时可改为 logging.DEBUG
    setup_logging(level=logging.INFO)
    
    main()
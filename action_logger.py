"""
加固/还原/修复执行过程的日志辅助模块（TUI 与 CLI 共用）

界面执行时 whiptail 会占满终端，异常堆栈和失败原因无法直接看到；
命令行的结果也只在终端打印。因此把每一项的开始/成功/失败/汇总统一
写入日志文件，保证操作可追溯。
"""
import logging
import os

LOGGER_NAME = 'cu_concrete.action'
logger = logging.getLogger(LOGGER_NAME)


def get_logger():
    """返回 TUI 专用 logger"""
    return logger


def item_info(instance):
    """取出加固项的 部门_编号、描述、模块名"""
    dep, item_id = '?', '?'
    try:
        dep = instance.config.get('dep')
        item_id = instance.config.get('id')
    except Exception:
        pass
    try:
        desc = instance.get_des()
    except Exception:
        desc = ''
    return f"{dep}_{item_id}", desc, type(instance).__name__


def log_start(action, instances):
    logger.info(f"[{action}] 开始执行，共 {len(instances)} 项")


def log_item_begin(action, instance):
    dep_id, desc, name = item_info(instance)
    logger.info(f"[{action}] 开始 | {dep_id} | {desc} | {name}")


def log_item_success(action, instance):
    dep_id, desc, _ = item_info(instance)
    logger.info(f"[{action}] 成功 | {dep_id} | {desc}")


def log_item_failure(action, instance, error):
    """记录失败项，包含完整异常堆栈"""
    dep_id, desc, name = item_info(instance)
    logger.error(f"[{action}] 失败 | {dep_id} | {desc} | {name} | 错误: {error}", exc_info=True)


def log_summary(action, succeeded, failed):
    logger.info(f"[{action}] 执行结束 | 成功 {len(succeeded)} 项 | 失败 {len(failed)} 项")
    for instance, error in failed:
        dep_id, desc, _ = item_info(instance)
        logger.error(f"[{action}] 失败项明细 | {dep_id} | {desc} | {error}")


def mark_failed(instance):
    """
    把失败的加固项在状态表(pkl)中的状态置为 1(加固失败)，保证状态与日志一致。
    仅在状态记录已存在时更新，避免产生缺列的残缺记录。
    """
    pkl_file = getattr(instance, 'pkl_file', None)
    if not pkl_file or not os.path.exists(pkl_file):
        return False
    try:
        import Panda as pd
        df = pd.read_pickle(pkl_file)
        if df is None:
            return False
        row = f"{instance.config['dep']}{instance.config['id']}"
        if row not in df._data:
            return False
        df.loc[row, 'status'] = 1
        df.to_pickle(pkl_file)
        return True
    except Exception:
        return False

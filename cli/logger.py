"""
日志模块
"""

import logging
import os

def setup_logger(level=logging.INFO):
    """
    设置日志记录器
    
    Args:
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 创建日志目录
    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, 'cu_concrete.log')
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 统一由 root logger 的处理器落盘：
    #   - CLI 自身用 'cu_concrete' logger 记录，靠 propagate 传到 root
    #   - 加固项内部用 logging.info()/logging.error()，本身就走 root
    # 若两者各自再挂一个指向同一文件的处理器，同一条日志会被写两遍。
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    target = os.path.abspath(log_file)
    for h in root_logger.handlers[:]:
        if getattr(h, 'baseFilename', None) and os.path.abspath(h.baseFilename) == target:
            root_logger.removeHandler(h)
            h.close()
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 创建logger（不单独挂处理器，避免与 root 重复写入）
    logger = logging.getLogger('cu_concrete')
    logger.setLevel(level)
    logger.propagate = True

    return logger
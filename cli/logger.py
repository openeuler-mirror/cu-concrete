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
    
    # 创建logger
    logger = logging.getLogger('cu_concrete')
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if not logger.handlers:
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        
        # # 创建控制台处理器
        # console_handler = logging.StreamHandler()
        # console_handler.setLevel(level)
        
        # 创建格式器并添加到处理器
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 将处理器添加到logger
        logger.addHandler(file_handler)
    
    return logger
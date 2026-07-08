"""
任务管理器 - 实现异步任务执行、云池互斥、状态管理和日志记录
支持文件持久化存储历史数据
"""
import os
import re
import time
import json
import threading
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def find_policy_yaml(project_root: str, policy_id: str) -> str | None:
    """根据策略ID查找对应的 YAML 配置文件路径"""
    # 在 department_*_policy 目录下查找
    for dept_dir in Path(project_root).glob("department_*_policy"):
        if dept_dir.is_dir():
            # 查找匹配的策略目录
            for policy_dir in dept_dir.glob(f"{policy_id}"):
                if policy_dir.is_dir():
                    yaml_file = policy_dir / f"{policy_id}.yaml"
                    if yaml_file.exists():
                        return str(yaml_file)
    return None

# 数据存储目录配置
DATA_DIR = Path("/opt/cu-concrete/data")
TASKS_FILE = DATA_DIR / "tasks.json"
LOGS_DIR = DATA_DIR / "logs"
RESULTS_DIR = DATA_DIR / "results"
BACKUP_ROOT = DATA_DIR / "backup"

# 文件写入锁，防止多线程同时操作文件
_file_write_lock = threading.Lock()
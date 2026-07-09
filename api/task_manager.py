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

# 确保数据目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

# 内存中的任务存储（运行时状态，服务重启后从文件恢复）
_tasks: Dict[str, dict] = {}
_tasks_lock = threading.Lock()

# 云池运行状态互斥（同一云池内串行，不同云池并行）
_running_pools: set = set()
_running_pools_lock = threading.Lock()

# 日志存储（每个任务的最大日志行数）
_task_logs: Dict[str, list] = {}
_task_logs_lock = threading.Lock()
MAX_LOG_LINES = 1000

# 任务时间戳映射（任务ID -> 时间戳目录名）
_task_timestamps: Dict[str, str] = {}
_task_timestamps_lock = threading.Lock()

def _load_tasks_from_file():
    """从文件加载任务数据"""
    global _tasks
    try:
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _tasks = data.get('tasks', {})
            logger.info(f"从文件加载了 {len(_tasks)} 个任务")
    except Exception as e:
        logger.error(f"加载任务文件失败: {e}")
        _tasks = {}
        
def _save_tasks_to_file():
    """保存任务数据到文件（线程安全）"""
    try:
        with _file_write_lock:  # 获取文件写入锁
            with _tasks_lock:  # 同时保护内存数据
                data = {
                    'tasks': _tasks,
                    'updated_at': datetime.datetime.now().isoformat()
                }
                # 先写入临时文件，再重命名，确保原子性
                temp_file = TASKS_FILE.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp_file.replace(TASKS_FILE)
    except Exception as e:
        logger.error(f"保存任务文件失败: {e}")
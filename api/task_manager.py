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


def _get_log_file_path(task_id: str) -> Path:
    """获取任务日志文件路径"""
    return LOGS_DIR / f"{task_id}.log"


def _load_logs_from_file(task_id: str) -> list:
    """从文件加载任务日志"""
    log_file = _get_log_file_path(task_id)
    try:
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                return f.read().splitlines()
    except Exception as e:
        logger.error(f"加载日志文件失败 {task_id}: {e}")
    return []


def _save_logs_to_file(task_id: str, logs: list):
    """保存任务日志到文件（线程安全）"""
    log_file = _get_log_file_path(task_id)
    try:
        with _file_write_lock:  # 获取文件写入锁
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(logs))
    except Exception as e:
        logger.error(f"保存日志文件失败 {task_id}: {e}")


# 启动时加载历史数据
_load_tasks_from_file()


def generate_task_id() -> str:
    """生成唯一任务ID: 年月日 + 随机后缀"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    random_suffix = os.urandom(4).hex()
    return f"{timestamp}-{random_suffix}"


def get_or_create_task_timestamp(task_id: str) -> str:
    """
    获取或创建任务的时间戳
    使用任务ID作为时间戳标识
    """
    with _task_timestamps_lock:
        if task_id in _task_timestamps:
            return _task_timestamps[task_id]
        
        # 使用任务ID作为时间戳
        _task_timestamps[task_id] = task_id
        logger.info(f"任务 {task_id} 使用任务ID作为时间戳")
        return task_id


def create_task(pool_id: str, pool_name: str) -> str:
    """
    创建新任务
    
    Returns:
        task_id: 任务唯一标识
    """
    task_id = generate_task_id()
    
    with _tasks_lock:
        _tasks[task_id] = {
            'task_id': task_id,
            'pool_id': pool_id,
            'pool_name': pool_name,
            'status': 'running',  # running, completed, failed
            'created_at': datetime.datetime.now().isoformat(),
            'completed_at': None,
            'error_message': None,
            'result_file': None,
            'total_hosts': 0,
            'timestamp': None,  # 将在任务执行时设置
            'policy_names': [],  # 加固策略中文名称列表
            'script_name': None,  # 执行脚本名称
        }
    
    # 保存到文件
    _save_tasks_to_file()
    
    with _task_logs_lock:
        _task_logs[task_id] = []
    
    logger.info(f"创建任务 {task_id}，云池: {pool_id}")
    return task_id


def update_task_status(task_id: str, status: str, result_file: str = None, 
                       total_hosts: int = 0, 
                       error_message: str = None):
    """更新任务状态"""
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id]['status'] = status
            _tasks[task_id]['completed_at'] = datetime.datetime.now().isoformat()
            if result_file:
                _tasks[task_id]['result_file'] = result_file
            _tasks[task_id]['total_hosts'] = total_hosts
            if error_message:
                _tasks[task_id]['error_message'] = error_message
            logger.info(f"任务 {task_id} 状态更新为: {status}")
    
    # 保存到文件
    _save_tasks_to_file()


def update_task_policy_names(task_id: str, policy_names: list):
    """更新任务加固策略中文名称列表"""
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id]['policy_names'] = policy_names
    _save_tasks_to_file()


def update_task_script(task_id: str, script_name: str):
    """更新任务执行脚本信息"""
    with _tasks_lock:
        if task_id in _tasks:
            _tasks[task_id]['script_name'] = script_name
    _save_tasks_to_file()


def append_task_log(task_id: str, message: str):
    """追加任务日志"""
    with _task_logs_lock:
        if task_id not in _task_logs:
            # 尝试从文件加载已有日志
            _task_logs[task_id] = _load_logs_from_file(task_id)
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        _task_logs[task_id].append(f"[{timestamp}] {message}")
        # 限制日志行数
        if len(_task_logs[task_id]) > MAX_LOG_LINES:
            _task_logs[task_id] = _task_logs[task_id][-MAX_LOG_LINES:]
        
        # 保存到文件
        _save_logs_to_file(task_id, _task_logs[task_id])


def get_task_status(task_id: str) -> Optional[dict]:
    """获取任务状态"""
    with _tasks_lock:
        task = _tasks.get(task_id)
        if task:
            return task.copy()
        
        # 如果内存中没有，尝试从文件加载
        _load_tasks_from_file()
        task = _tasks.get(task_id)
        return task.copy() if task else None


def get_task_logs(task_id: str) -> str:
    """获取任务日志"""
    with _task_logs_lock:
        if task_id not in _task_logs:
            # 从文件加载
            _task_logs[task_id] = _load_logs_from_file(task_id)
        
        logs = _task_logs[task_id]
        return "\n".join(logs)


def get_all_tasks(current: int = 1, pageSize: int = 10) -> list:
    """
    获取所有任务列表（支持分页）
    
    Args:
        current: 当前页码，从1开始
        pageSize: 每页数量
    """
    with _tasks_lock:
        tasks = list(_tasks.values())
    
    # 按时间倒序
    tasks.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # 分页
    total = len(tasks)
    offset = (current - 1) * pageSize
    tasks = tasks[offset:offset + pageSize]
    
    return {
        'count': total,
        'pageIndex': current,
        'pageSize': pageSize,
        'list': tasks
    }


def is_pool_running(pool_id: str) -> bool:
    """检查云池是否正在运行任务"""
    with _running_pools_lock:
        return pool_id in _running_pools


def acquire_pool_lock(pool_id: str) -> bool:
    """
    获取云池执行锁
    
    Returns:
        bool: 是否成功获取锁
    """
    with _running_pools_lock:
        if pool_id in _running_pools:
            return False
        _running_pools.add(pool_id)
        logger.info(f"云池 {pool_id} 获取执行锁")
        return True


def release_pool_lock(pool_id: str):
    """释放云池执行锁"""
    with _running_pools_lock:
        if pool_id in _running_pools:
            _running_pools.remove(pool_id)
            logger.info(f"云池 {pool_id} 释放执行锁")


def run_ansible_playbook_async(task_id: str, pool_id: str, pool_info: dict):
    """
    异步执行Ansible Playbook
    
    使用任务ID作为数据目录标识，确保精确匹配
    """
    def target():
        try:
            # 记录脚本信息
            script_name = os.path.basename(pool_info['playbook_path'])
            update_task_script(task_id, script_name)
            
            # 记录加固策略中文名称列表
            policy_ids = pool_info.get('list', [])
            policy_names = []
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for policy_id in policy_ids:
                # 查找对应的 YAML 文件读取中文描述
                yaml_path = find_policy_yaml(current_dir, policy_id)
                if yaml_path:
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            import yaml
                            config = yaml.safe_load(f)
                            if config and 'description' in config:
                                policy_names.append(config['description'])
                            else:
                                policy_names.append(policy_id)
                    except Exception as e:
                        logger.warning(f"读取策略配置失败 {policy_id}: {e}")
                        policy_names.append(policy_id)
                else:
                    policy_names.append(policy_id)
            update_task_policy_names(task_id, policy_names)
            
            append_task_log(task_id, f"开始执行云池 {pool_id} 的加固任务")
            append_task_log(task_id, f"Playbook路径: {pool_info['playbook_path']}")
            append_task_log(task_id, f"加固策略数: {len(policy_names)}")
            
            # 使用任务ID作为数据标识
            with _task_timestamps_lock:
                _task_timestamps[task_id] = task_id
            append_task_log(task_id, f"任务标识: {task_id}")
            
            # 执行ansible-playbook，传入任务ID环境变量
            playbook_path = pool_info['playbook_path']
            inventory_path = pool_info['ansible_inventory']
            cmd = [
                'ansible-playbook',
                '-i', inventory_path,
                playbook_path
            ]
            
            append_task_log(task_id, f"执行命令: {' '.join(cmd)}")
            append_task_log(task_id, f"环境变量 CU_CONCRETE_TASK_ID={task_id}")
            

            # 设置环境变量，确保 ansible 使用相同任务ID
            env = os.environ.copy()
            env['CU_CONCRETE_TASK_ID'] = task_id
            
            # 使用Popen实时获取输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            # 实时读取输出
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    append_task_log(task_id, line)
            
            process.wait()
            
            if process.returncode != 0:
                error_msg = f"ansible-playbook 执行失败 (exit code {process.returncode})"
                append_task_log(task_id, f"ERROR: {error_msg}")
                update_task_status(task_id, 'failed', error_message=error_msg)
                return
            
            append_task_log(task_id, "ansible-playbook 执行成功，开始生成结果文件")
            
            # 使用任务ID作为目录标识进行合并
            combine_result = run_combine_to_csv(pool_info, task_id)
            
            if not combine_result['success']:
                error_msg = f"combine_to_csv 执行失败: {combine_result['error']}"
                append_task_log(task_id, f"ERROR: {error_msg}")
                update_task_status(task_id, 'failed', error_message=error_msg)
                return
            
            append_task_log(task_id, f"结果文件生成成功: {combine_result['output_file']}")
            append_task_log(task_id, f"主机总数: {combine_result.get('total_hosts', 0)}")
            
            # 更新任务状态为完成
            update_task_status(
                task_id=task_id,
                status='completed',
                result_file=combine_result['output_file'],
                total_hosts=combine_result.get('total_hosts', 0)
            )
            
        except Exception as e:
            error_msg = f"执行任务时发生错误: {str(e)}"
            append_task_log(task_id, f"ERROR: {error_msg}")
            update_task_status(task_id, 'failed', error_message=error_msg)
        finally:
            # 无论成功失败，都要释放锁
            release_pool_lock(pool_id)
    
    # 启动后台线程
    thread = threading.Thread(target=target, daemon=True)
    thread.start()


def run_combine_to_csv(pool_info: dict, task_id: str = None) -> dict:
    """
    执行 combine_to_csv 逻辑
    
    Args:
        pool_info: 云池配置信息
        task_id: 任务ID，只处理该任务对应的数据
    """
    try:
        records = []
        expected_cols = {'status', 'module_name', 'module_path'}
        
        # 使用任务ID作为结果文件名，确保唯一性
        if not task_id:
            return {'success': False, 'error': '任务ID不能为空'}
        OUTPUT_CSV = f"result_{task_id}.csv"
        STATUS_MAP = {
            "0": "未加固",
            "1": "加固失败", 
            "2": "已加固"
        }

        def extract_host(dirname: str) -> str | None:
            m = re.match(r"cu-concrete-(.+)", dirname)
            return m.group(1) if m else None

        # 确定要处理的任务目录
        if task_id:
            # 使用指定任务ID的目录
            task_dirs = [BACKUP_ROOT / f"cu-concrete-{task_id}"]
            logger.info(f"只处理指定任务目录: cu-concrete-{task_id}")
        else:
            # 回退：查找最新的目录（不推荐，仅兼容旧逻辑）
            all_dirs = [d for d in BACKUP_ROOT.glob("cu-concrete-*") if d.is_dir()]
            if not all_dirs:
                return {'success': False, 'error': '未找到任何任务目录'}
            # 按修改时间排序获取最新的
            latest_dir = sorted(all_dirs, key=lambda x: x.stat().st_mtime, reverse=True)[0]
            task_dirs = [latest_dir]
            logger.warning(f"未指定任务ID，使用最新的目录: {latest_dir.name}")
            
        for task_dir in task_dirs:
            if not task_dir.exists():
                logger.warning(f"任务目录不存在: {task_dir}")
                continue
                
            logger.info(f"处理任务目录: {task_dir.name}")
            
            for host_dir in task_dir.glob("cu-concrete-*"):
                if not host_dir.is_dir():
                    continue
                host = extract_host(host_dir.name)
                if not host:
                    continue
                    
                # 查找 pkl 文件

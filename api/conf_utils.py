# 1、conf_data.json: 用来做生成的加固文本，配置映射
# 2、conf_harden.json: 用来做不同模式的加固配置映射

# 本文件做配置关系映射
import json
import yaml
import os
import re
import shutil
from pathlib import Path
import logging
# 设置日志
logger = logging.getLogger(__name__)
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses
# 导入配置文件
path= Path(__file__).parent
# 项目根目录（部署在 /opt/cu-concrete 时与部署目录一致）
project_root = path.parent
# 云池与机器信息配置（含云池台账与各云池下的机器台账）
cloud_pools_path = path / "conf_cloud_pools_info.yaml"
# 导入配置数据库路径
config_data_path = path / "conf_data.json"
# 模板配件文件：inventory 模板（[servers] 段会被替换为选中的机器）与 playbook 模板
ini_template_path = project_root / "data/fetch/fetch_template.ini"
playbook_template_path = project_root / "data/fetch/playbook_template.yml"

from rest_framework.response import Response
from rest_framework import status

# ==================== 公共路径 ====================

def get_policy_base_path() -> Path:
    """
    获取加固策略（department_*_policy）的扫描根目录，即项目根目录
    生产环境项目部署在 /opt/cu-concrete，此处与部署目录一致；
    本地开发时指向仓库根目录，避免硬编码 Linux 路径导致扫描不到策略
    """
    return project_root


# ==================== 云池与机器信息读写 ====================

def _normalize_machine(machine: dict) -> dict:
    """补全机器条目的默认字段"""
    machine = machine or {}
    return {
        'ip': str(machine.get('ip', '')).strip(),
        'name': str(machine.get('name', '') or '').strip(),
        'user': str(machine.get('user', '') or 'root').strip(),
        'port': int(machine.get('port', 22) or 22),
        'os': str(machine.get('os', '') or '').strip(),
        'desc': str(machine.get('desc', '') or '').strip()
    }


def _normalize_pool(pool: dict) -> dict:
    """补全云池条目的默认字段"""
    pool = pool or {}
    machines = pool.get('machines') or []
    if not isinstance(machines, list):
        machines = []
    return {
        'id': str(pool.get('id', '')).strip(),
        'name': str(pool.get('name', '') or '').strip(),
        'desc': str(pool.get('desc', '') or '').strip(),
        'createTime': pool.get('createTime') or '',
        'machines': [_normalize_machine(m) for m in machines if isinstance(m, dict) and m.get('ip')]
    }


def read_pools() -> list:
    """
    读取云池与机器信息（每次从磁盘读取，保证多进程/多请求数据一致）
    Returns:
        list: [{id, name, desc, createTime, machines: [{ip, name, user, port, os, desc}]}, ...]
    """
    if not os.path.exists(cloud_pools_path):
        logger.error(f"云池配置文件 {cloud_pools_path} 不存在")
        return []
    with open(cloud_pools_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    pools = data.get('pools') or []
    # 兼容旧的 {pool_id: {...}} 结构
    if isinstance(data, dict) and not pools:
        pools = [{'id': pool_id, **(info or {})} for pool_id, info in data.items()]

    return [_normalize_pool(pool) for pool in pools if pool.get('id')]


def write_pools(pools: list) -> bool:
    """
    写回云池与机器信息（先写临时文件再替换，避免写入中断导致文件损坏）
    """
    data = {'pools': [_normalize_pool(pool) for pool in pools if pool.get('id')]}
    tmp_path = cloud_pools_path.with_suffix(cloud_pools_path.suffix + '.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    os.replace(tmp_path, cloud_pools_path)
    logger.info(f"云池配置已更新，共 {len(data['pools'])} 个云池")
    return True


def get_pool(pool_id: str):
    """按云池ID获取云池信息，不存在时返回 None"""
    for pool in read_pools():
        if pool['id'] == pool_id:
            return pool
    return None


# 查找云池列表
def pool_list(request):
    try:
        # 获取所有云池数据（数据源：conf_cloud_pools_info.yaml）
        all_pools = [
            {
                'id': pool['id'],
                'name': pool['name'],
                'desc': pool['desc'],
                'machineCount': len(pool['machines'])
            }
            for pool in read_pools()
        ]
        # 处理分页参数
        try:
            current_param = request.query_params.get('current', '1')
            pageSize_param = request.query_params.get('pageSize', str(len(all_pools)))
            # 验证并转换参数
            current = int(current_param) if current_param.isdigit() and int(current_param) > 0 else 1
            pageSize = int(pageSize_param) if pageSize_param.isdigit() and int(pageSize_param) > 0 else len(all_pools)
        except (ValueError, TypeError):
            # 如果参数转换失败，使用默认值
            current = 1
            pageSize = len(all_pools)
        # 分页处理
        total_count = len(all_pools)
        start_index = (current - 1) * pageSize
        end_index = start_index + pageSize
        paginated_pools = all_pools[start_index:end_index]
        # 构造响应数据
        response_data = {
            'count': total_count,
            'pageIndex': current,
            'pageSize': pageSize,
            'list': paginated_pools
        }
        return CommonResponses.QUERY_SUCCESS(response_data)
    # 异常处理
    except Exception as e:
        logger.error(f"获取云池列表时出错: {str(e)}")
        return ApiResponse.error(f'获取云池列表时出错: {str(e)}', 500)

# ==================== 机器列表 / 安全配置读取（任务执行与配置生成共用） ====================

def parse_ini_hosts(ini_content: str) -> list:
    """
    解析 ansible inventory ini 内容，返回结构化机器列表
    统一跳过：空行、注释行、组定义行([xxx])、变量定义行(ansible_xxx=)
    """
    hosts = []
    for raw_line in (ini_content or '').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or line.startswith(';') or line.startswith('['):
            continue
        # 变量定义行, 例如 ansible_user=root
        if '=' in line:
            continue
        parts = line.split()
        ip = parts[0]
        # 兼容 "ip 主机名" 形式
        name = parts[1] if len(parts) > 1 and '=' not in parts[1] else ip
        hosts.append({'name': name, 'ip': ip})
    return hosts


def read_ini_hosts(ini_path: str) -> list:
    """
    从 inventory ini 文件中读取机器列表，文件不存在或不可读时返回空列表
    """
    if not ini_path or not os.path.exists(ini_path):
        return []
    try:
        with open(ini_path, 'r', encoding='utf-8') as f:
            return parse_ini_hosts(f.read())
    except Exception as e:
        logger.error(f"读取 inventory 文件 {ini_path} 失败: {str(e)}")
        return []


def get_pool_hosts(pool_id: str, config_name: str = None) -> list:
    """
    获取云池的机器列表（前端两个 tab 共用同一套逻辑，全部由后端解析）

    Args:
        pool_id: 云池ID, 例如: pool-1
        config_name: 安全配置文件名, 为空时取云池台账中的机器列表
            - 传入时: 解析该安全配置对应的 inventory 文件（即配置生成时选择的机器范围，任务执行页使用）
            - 不传入时: 读取 conf_cloud_pools_info.yaml 中该云池的机器台账（配置生成页使用）
    Returns:
        list: [{'name': 主机名, 'ip': IP}, ...]
    """
    pool = get_pool(pool_id)
    if not pool:
        return []

    # 1、指定了安全配置时，解析该配置对应的 inventory（执行范围以配置为准）
    if config_name:
        record = get_config_record(pool_id, config_name)
        if record:
            hosts = read_ini_hosts(record.get('serverConfigPath'))
            if hosts:
                return hosts

    # 2、读取云池台账中的机器列表
    return [
        {'name': machine['name'] or machine['ip'], 'ip': machine['ip']}
        for machine in pool['machines']
    ]


def extract_harden_items(yml_path: str) -> list:
    """
    从生成的 playbook yml 中解析加固项列表, 例如: 1_1,1_2
    """
    if not yml_path or not os.path.exists(yml_path):
        return []
    try:
        with open(yml_path, 'r', encoding='utf-8') as f:
            yml_content = f.read()
    except Exception as e:
        logger.error(f"读取 playbook 文件 {yml_path} 失败: {str(e)}")
        return []

    match = re.search(r'python3\s+main\.py\s+harden\s+items\s+([0-9_]+(?:\s*,\s*[0-9_]+)*)', yml_content)
    if not match:
        return []
    return [item for item in match.group(1).replace(' ', '').split(',') if item]


def get_config_dep_ids(harden_items: list) -> list:
    """
    将 1_3 形式的加固项转换为结果过滤所需的 dep_id（13）
    """
    dep_ids = []
    for item in harden_items or []:
        if '_' in item:
            dep, item_id = item.split('_', 1)
            dep_ids.append(f'{dep}{item_id}')
        else:
            dep_ids.append(str(item))
    return dep_ids


def get_config_record(pool_name: str, file_name: str):
    """
    从配置数据库(conf_data.json)中读取单条配置记录并标准化返回
    记录不存在时返回 None
    """
    if not os.path.exists(config_data_path):
        logger.error(f"配置数据库 {config_data_path} 不存在")
        return None
    try:
        with open(config_data_path, 'r', encoding='utf-8') as f:
            conf_data = json.load(f)
    except Exception as e:
        logger.error(f"读取配置数据库失败: {str(e)}")
        return None

    file_data = conf_data.get(pool_name, {}).get(file_name)
    if not file_data:
        return None

    # 加固项从 playbook 文件中解析（配置记录未单独保存该字段）
    harden_items = extract_harden_items(file_data.get('execFilePath'))

    return {
        'name': file_name,
        'harden_model': file_data.get('harden-model'),
        'hosts': file_data.get('hosts', []),
        'serverConfigPath': file_data.get('serverConfigPath'),
        'execFilePath': file_data.get('execFilePath'),
        'generatePersonName': file_data.get('generatePersonName'),
        'generateTime': file_data.get('generateTime'),
        'harden_items': harden_items,
        'dep_ids': get_config_dep_ids(harden_items),
    }

# 根据pool名获取所有配置文件名
def find_pool_configs(pool_name: str):
    """
    根据云池名获取所有配置文件

    注意：云池下没有任何配置属于正常业务状态，返回 200 + 空列表，
    仅在配置数据库文件缺失时返回 404
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(config_data_path):
            return ApiResponse.error(f'配置文件 {config_data_path} 不存在', 404)
        # 读取并解析JSON文件
        with open(config_data_path, "r", encoding="utf-8") as f:
            conf_data = json.load(f)
        # 获取并返回对应pool的所有配置（云池不存在或无配置时为空列表）
        pool_configs = conf_data.get(pool_name) or {}
        config_file_list = list(pool_configs.keys())
        if not config_file_list:
            logger.info(f"云池 {pool_name} 下暂无配置文件，返回空列表")
        
        # 修复1：安全处理文件名，避免索引越界
        # 先收集 (生成时间, 文件名, 配置名)，用于按生成时间倒序
        collected_configs = []
        for filename in config_file_list:
            # 安全分割文件名
            parts = filename.split('_')
            
            # 确保至少有两个部分，否则使用整个文件名
            if len(parts) >= 2:
                # 取前两部分作为名称
                name = '_'.join(parts[:2])
            else:
                # 如果只有一个部分或没有下划线，使用整个文件名
                name = filename
                
            # 获取生成时间（缺失时为空串，排序时排在最后）
            generate_time = pool_configs[filename].get("generateTime", "") or ""
            
            collected_configs.append((generate_time, filename, name))
        
        # 按生成时间倒序排列（时间格式 YYYY-MM-DD HH:MM:SS，字符串比较即时间比较）
        collected_configs.sort(key=lambda item: item[0], reverse=True)
        
        formatted_configs = [
            {
                'id': filename,
                'name': name,
                'description': f'生成于 {generate_time}' if generate_time else '生成于 未知时间'
            }
            for generate_time, filename, name in collected_configs
        ]
        
        # 修复2：返回标准分页格式
        return CommonResponses.QUERY_SUCCESS({
            'count': len(formatted_configs),
            'pageIndex': 1,
            'pageSize': len(formatted_configs),
            'list': formatted_configs
        })
    # 异常处理
    except Exception as e:
        logger.error(f"获取配置列表时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'获取所有配置文件时出错: {str(e)}', 500)

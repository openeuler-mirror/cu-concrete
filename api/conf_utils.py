# 1、conf_data.json: 用来做生成的加固文本，配置映射
# 2、conf_harden.json: 用来做不同模式的加固配置映射

# 本文件做配置关系映射
import json
from django.http import JsonResponse
import yaml
import os
import re
import uuid
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
import logging
# 设置日志
logger = logging.getLogger(__name__)
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses
# 导入配置文件
path= Path(__file__).parent
config_path = path / "config.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    CLOUD_POOLS = yaml.load(f,Loader=yaml.Loader)
# 导入配置数据库路径
config_data_path = path / "conf_data.json"
# 模板配件文件
playbook_template_path = path.parent / "data/fetch/playbook_template.yml"

from rest_framework.response import Response
from rest_framework import status

# 查找云池列表
def pool_list(request):
    try:
        # 获取所有云池数据
        all_pools = []
        for pool_id, pool_info in CLOUD_POOLS.items():
            all_pools.append({
                'id': pool_id,
                'name': pool_info['name']
            })
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
    
# 根据pool名获取所有配置文件名
def find_pool_configs(pool_name: str):
    """
    根据云池名获取所有配置文件
    """
    # 检查文件是否存在
    if not os.path.exists(config_data_path):
        return ApiResponse.error(f'配置文件 {config_data_path} 不存在', 404)
    # 读取并解析JSON文件
    with open(config_data_path, "r", encoding="utf-8") as f:
        conf_data = json.load(f)
    # 根据pool_name查找对应配置
    if pool_name not in conf_data:
        return ApiResponse.error(f'未找到名为 {pool_name} 的云池配置', 404)
    # 获取对应pool的配置key列表
    pool_configs = conf_data[pool_name]
    config_file_list = list(pool_configs.keys())
    print("提取的配置文件名列表：", config_file_list)
    
    # 临时返回原始列表
    return CommonResponses.QUERY_SUCCESS({
        'list': config_file_list
    })
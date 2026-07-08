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
    # 获取所有云池数据
    all_pools = []
    for pool_id, pool_info in CLOUD_POOLS.items():
        all_pools.append({
            'id': pool_id,
            'name': pool_info['name']
        })
    # 构造基础响应数据
    response_data = {
        'list': all_pools
    }
    return CommonResponses.QUERY_SUCCESS(response_data)
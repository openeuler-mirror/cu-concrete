from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import csv
from pathlib import Path
import re
import yaml
import shutil
import os
import logging
# 设置日志
logger = logging.getLogger(__name__)

# 导入drf_yasg相关模块
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render
import uuid
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses

# 导入任务管理器
from . import task_manager

import pandas
from django.http import JsonResponse
import json
# 导入事件总线
from .eventbus import Eventbus
# 创建事件总线对象
event_bus = Eventbus()

# 云池地址
path= Path(__file__).parent / "config.yaml"
with open(path, 'r', encoding='utf-8') as f:
    CLOUD_POOLS = yaml.load(f,Loader=yaml.Loader)


def index(request):
    """
    渲染主页（非 API, 保持原样）
    """
    return render(request, 'index.html')

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter(
            'pool_id', 
            openapi.IN_QUERY,
            description='云池ID, 例如: pool-1, pool-2, pool-3',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="任务已提交",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "任务已提交",
                    "data": {
                        "task_id": "20240311-abc123",
                        "status": "running",
                        "pool_id": "pool-1",
                        "pool_name": "云池1"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="请求参数错误",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "缺少pool_id参数",
                    "data": None
                }
            }
        ),
        400: openapi.Response(
            description="无效的云池ID",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "无效的云池ID: pool-xxx",
                    "data": None
                }
            }
        ),
        409: openapi.Response(
            description="云池正在执行其他任务",
            examples={
                "application/json": {
                    "code": 409,
                    "message": "云池 pool-1 正在执行其他任务，请稍后再试",
                    "data": None
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "提交任务时发生错误: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['POST'])
def execute_playbook(request):
    """
    执行ansible-playbook脚本的接口（异步模式）
    接收云池ID参数, 创建异步任务执行playbook
    
    同一云池内串行执行（互斥），不同云池并行执行
    
    Query Parameters:
        pool_id (str): 云池ID, 例如: pool-1, pool-2, pool-3
    
    Returns:
        Response: 包含任务ID的响应对象
            {
                "code": 200,
                "message": "任务已提交",
                "data": {
                    "task_id": "任务ID",
                    "status": "running",
                    "pool_id": "云池ID",
                    "pool_name": "云池名称"
                }
            }
    """
    try:
        # 从查询参数获取 pool_id
        pool_id = request.query_params.get('pool_id')
        
        if not pool_id:
            return CommonResponses.MISSING_PARAMETER('pool_id')
        
        if pool_id not in CLOUD_POOLS:
            return CommonResponses.INVALID_PARAMETER(f'无效的云池ID: {pool_id}')
        
        pool_info = CLOUD_POOLS[pool_id]
        
        # 检查云池是否正在运行任务（同一云池串行）
        if task_manager.is_pool_running(pool_id):
            return CommonResponses.CONFLICT(f'云池 {pool_id} 正在执行其他任务，请稍后再试')
        
        # 获取云池锁
        if not task_manager.acquire_pool_lock(pool_id):
            return CommonResponses.CONFLICT(f'云池 {pool_id} 正在执行其他任务，请稍后再试')
        
        # 创建任务
        task_id = task_manager.create_task(pool_id, pool_info['name'])
        
        # 启动异步执行
        task_manager.run_ansible_playbook_async(task_id, pool_id, pool_info)
        
        logger.info(f"任务 {task_id} 已提交，云池: {pool_id}")
        
        # 立即返回任务信息
        return CommonResponses.OPERATION_SUCCESS({
            'task_id': task_id,
            'status': 'running',
            'pool_id': pool_id,
            'pool_name': pool_info['name']
        }, message='任务已提交')
        
    except Exception as e:
        logger.error(f"提交任务时发生错误: {str(e)}")
        return ApiResponse.server_error(f'提交任务时发生错误: {str(e)}')


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'current', 
            openapi.IN_QUERY,
            description="当前页码, 从1开始",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1,
            example=1
        ),
        openapi.Parameter(
            'pageSize',
            openapi.IN_QUERY,
            description="每页记录数",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10,
            example=10
        ),
    ],
    responses={
        200: openapi.Response(
            description="返回云池列表（带分页）",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "count": 3,
                        "pageIndex": 1,
                        "pageSize": 10,
                        "list": [
                            {
                                "id": "pool-1",
                                "name": "云池1"
                            },
                            {
                                "id": "pool-2", 
                                "name": "云池2"
                            }
                        ]
                    }
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取云池列表时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['GET'])
def pool_list(request):
    """
    返回可用的云池列表（DRF 视图，带分页）
    
    Query Parameters:
        page_index (int, optional): 页码, 默认为1
        page_size (int, optional): 每页大小，默认为全部
        
    Returns:
        Response: 包含云池列表的响应对象（带分页）
        {
            "requestId": "唯一请求ID",
            "code": 200,
            "message": "查询成功",
            "data": {
                "count": 总记录数,
                "pageIndex": 当前页码,
                "pageSize": 每页大小,
                "list": [
                    {
                        "id": "云池ID",
                        "name": "云池名称"
                    }
                ]
            }
        }
    """
    try:
        return event_bus.eventbus_pool_list(request)
    except Exception as e:
        logger.error(f"获取云池列表时出错: {str(e)}")
        return ApiResponse.error(f'获取云池列表时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description='任务ID',
            type=openapi.TYPE_STRING,
            required=True
        ),
        openapi.Parameter(
            'current', 
            openapi.IN_QUERY,
            description="当前页码, 从1开始",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=1,
            example=1
        ),
        openapi.Parameter(
            'pageSize',
            openapi.IN_QUERY,
            description="每页记录数",
            type=openapi.TYPE_INTEGER,
            required=False,
            default=10,
            example=10
        )
    ],
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "count": 100,
                        "pageIndex": 1,
                        "pageSize": 10,
                        "list": [
                            {
                                "task_id": "20231201-123456",
                                "host": "example-host",
                                "dep_id": "1",
                                "status": "已加固",
                                "module_name": "安全模块名称"
                            }
                        ]
                    }
                }
            }
        ),
        400: openapi.Response(
            description="缺少task_id参数",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "缺少task_id参数",
                    "data": None
                }
            }
        ),
        400: openapi.Response(
            description="无效的文件路径",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "无效的文件路径",
                    "data": None
                }
            }
        ),
        404: openapi.Response(
            description="文件不存在",
            examples={
                "application/json": {
                    "code": 404,
                    "message": "文件不存在",
                    "data": None
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取结果文件时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['GET'])
def get_results(request):
    """
    获取执行结果文件内容并转换为JSON格式（DRF 视图，带分页）
    
    Query Parameters:
        task_id (str): 任务ID
        current (int, optional): 页码, 默认为1
        pageSize (int, optional): 每页大小, 默认为10
        
    Returns:
        Response: 包含文件内容的响应对象（带分页）
        {
            "requestId": "唯一请求ID",
            "code": 200,
            "message": "查询成功",
            "data": {
                "count": 总记录数,
                "pageIndex": 当前页码,
                "pageSize": 每页大小,
                "list": [
                    {
                        "column1": "value1",
                        "column2": "value2",
                        ...
                    }
                ]
            }
        }
    """
    try:
        task_id = request.query_params.get('task_id')
        
        if not task_id:
            return CommonResponses.MISSING_PARAMETER('task_id')
        
        # 清理 task_id，移除可能存在的 result_ 前缀和 .csv 后缀
        task_id = task_id.replace('result_', '').replace('.csv', '')
        
        # 后端拼接文件路径
        result_file = f"/opt/cu-concrete/data/results/result_{task_id}.csv"
        result_path = Path(result_file).resolve()
        project_root = Path('/opt/cu-concrete').resolve()
        
        if not str(result_path).startswith(str(project_root)):
            return ApiResponse.error('无效的文件路径', 400)
        
        if not result_path.exists():
            return CommonResponses.FILE_NOT_FOUND()
        
        with open(result_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        import io
        import csv
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)
        rows = []
        for row in csv_reader:
            if any(field.strip() for field in row.values()):
                rows.append(row)
        
        # 处理分页参数，添加参数验证
        try:
            current_param = request.query_params.get('current', '1')
            pageSize_param = request.query_params.get('pageSize', str(len(rows)))
            
            # 验证并转换参数
            current = int(current_param) if current_param.isdigit() and int(current_param) > 0 else 1
            pageSize = int(pageSize_param) if pageSize_param.isdigit() and int(pageSize_param) > 0 else 10
            
        except (ValueError, TypeError):
            # 如果参数转换失败，使用默认值
            current = 1
            pageSize = len(rows)
        
        # 分页处理
        total_count = len(rows)
        start_index = (current - 1) * pageSize
        end_index = start_index + pageSize
        paginated_data = rows[start_index:end_index]
        
        # 构造响应数据
        response_data = {
            'count': total_count,
            'pageIndex': current,
            'pageSize': pageSize,
            'list': paginated_data
        }
        
        return CommonResponses.QUERY_SUCCESS(response_data)
        
    except Exception as e:
        logger.error(f"获取结果文件时出错: {str(e)}")
        return ApiResponse.error(f'获取结果文件时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'current',
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            default=1,
            description='当前页码'
        ),
        openapi.Parameter(
            'pageSize',
            openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            default=10,
            description='每页数量'
        )
    ],
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "count": 100,
                        "pageIndex": 1,
                        "pageSize": 10,
                        "list": [
                            {
                                "task_id": "20240311-abc123",
                                "pool_id": "pool-1",
                                "pool_name": "云池1",
                                "status": "completed"
                            }
                        ]
                    }
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取任务列表时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['GET'])
def list_tasks(request):
    """
    获取任务列表（支持分页）
    
    Query Parameters:
        current (int): 当前页码, 默认1
        pageSize (int): 每页数量, 默认10
        
    Returns:
        任务列表（按时间倒序）
    """
    try:
        current = int(request.query_params.get('current', 1))
        pageSize = int(request.query_params.get('pageSize', 10))
        
        result = task_manager.get_all_tasks(current, pageSize)
        return CommonResponses.QUERY_SUCCESS(result)
    except Exception as e:
        logger.error(f"获取任务列表时出错: {str(e)}")
        return ApiResponse.error(f'获取任务列表时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description='任务ID',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "task_id": "20240311-abc123",
                        "pool_id": "pool-1",
                        "pool_name": "云池1",
                        "status": "completed",
                        "created_at": "2024-03-11T12:34:56",
                        "completed_at": "2024-03-11T12:35:30",
                        "result_file": "/opt/cu-concrete/data/results/result_20240311-abc123.csv",
                        "total_hosts": 2,
                        "policy_names": ["uid为0用户检查"],
                        "script_name": "harden.yml"
                    }
                }
            }
        ),
        400: openapi.Response(
            description="缺少task_id参数",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "缺少task_id参数",
                    "data": None
                }
            }
        ),
        404: openapi.Response(
            description="任务不存在",
            examples={
                "application/json": {
                    "code": 404,
                    "message": "任务 20240311-abc123 不存在",
                    "data": None
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取任务状态时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['GET'])
def get_task(request):
    """
    获取任务状态
    
    Query Parameters:
        task_id (str): 任务ID
        
    Returns:
        任务详细信息
    """
    try:
        task_id = request.query_params.get('task_id')
        if not task_id:
            return CommonResponses.MISSING_PARAMETER('task_id')
        
        task = task_manager.get_task_status(task_id)
        if not task:
            return CommonResponses.RESOURCE_NOT_FOUND(f'任务 {task_id} 不存在')
        return CommonResponses.QUERY_SUCCESS(task)
    except Exception as e:
        logger.error(f"获取任务状态时出错: {str(e)}")
        return ApiResponse.error(f'获取任务状态时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description='任务ID',
            type=openapi.TYPE_STRING,
            required=True
        ),
    ],
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "task_id": "20240311-abc123",
                        "content": [
                            "[12:34:56] 开始执行云池 pool-1 的加固任务",
                            "[12:34:56] Playbook路径: /path/to/playbook.yml",
                            "[12:35:30] 任务执行完成"
                        ]
                    }
                }
            }
        ),
        400: openapi.Response(
            description="缺少task_id参数",
            examples={
                "application/json": {
                    "code": 400,
                    "message": "缺少task_id参数",
                    "data": None
                }
            }
        ),
        404: openapi.Response(
            description="任务不存在",
            examples={
                "application/json": {
                    "code": 404,
                    "message": "任务 20240311-abc123 不存在",
                    "data": None
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取任务日志时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)
@api_view(['GET'])
def get_task_logs_view(request):
    """
    获取任务日志
    
    Query Parameters:
        task_id (str): 任务ID
        
    Returns:
        任务执行日志
    """
    try:
        task_id = request.query_params.get('task_id')
        if not task_id:
            return CommonResponses.MISSING_PARAMETER('task_id')
        
        # 检查任务是否存在
        task = task_manager.get_task_status(task_id)
        if not task:
            return CommonResponses.RESOURCE_NOT_FOUND(f'任务 {task_id} 不存在')
        
        logs = task_manager.get_task_logs(task_id)
        
        return CommonResponses.QUERY_SUCCESS({
            'task_id': task_id,
            'content': logs
        })
    except Exception as e:
        logger.error(f"获取任务日志时出错: {str(e)}")
        return ApiResponse.error(f'获取任务日志时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'pool_id',
            openapi.IN_QUERY,
            description='云池ID',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "count": 3,
                        "list": [
                            {"name": "host-1", "ip": "192.168.1.1"},
                            {"name": "host-2", "ip": "192.168.1.2"}
                        ]
                    }
                }
            }
        ),
        400: openapi.Response(description="缺少pool_id参数"),
        404: openapi.Response(description="云池不存在"),
        500: openapi.Response(description="服务器内部错误")
    }
)
@api_view(['GET'])
def pool_hosts(request):
    """
    获取云池的机器列表
    
    Query Parameters:
        pool_id (str): 云池ID
        
    Returns:
        机器列表
    """
    try:
        pool_id = request.query_params.get('pool_id')
        if not pool_id:
            return CommonResponses.MISSING_PARAMETER('pool_id')
        
        if pool_id not in CLOUD_POOLS:
            return CommonResponses.RESOURCE_NOT_FOUND(f'云池 {pool_id} 不存在')
        
        pool_info = CLOUD_POOLS[pool_id]

        # 从云池配置中获取机器列表
        hosts = []
        
        # 优先从ansible_inventory文件读取
        inventory_path = pool_info.get('ansible_inventory')
        if inventory_path and os.path.exists(inventory_path):
            with open(inventory_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行、注释行、组定义行和变量定义行
                    if line and not line.startswith('[') and not line.startswith('#') and not line.startswith('ansible_'):
                        hosts.append({'name': line, 'ip': line})
        else:
            # 回退到hosts或list字段
            host_list = pool_info.get('hosts', [])
            
            if isinstance(host_list, str) and os.path.exists(host_list):
                # 如果hosts是文件路径
                with open(host_list, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('[') and not line.startswith('#'):
                            hosts.append({'name': line, 'ip': line})
            elif isinstance(host_list, list):
                # hosts是列表
                for host in host_list:
                    if isinstance(host, dict):
                        hosts.append(host)
                    else:
                        hosts.append({'name': str(host), 'ip': str(host)})

        return CommonResponses.QUERY_SUCCESS({
            'count': len(hosts),
            'list': hosts
        })
    except Exception as e:
        logger.error(f"获取云池机器列表时出错: {str(e)}")
        return ApiResponse.error(f'获取云池机器列表时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='get',
    responses={
        200: openapi.Response(
            description="查询成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "查询成功",
                    "data": {
                        "count": 60,
                        "list": [
                            {
                                "id": "CheckEmptyAccount_1",
                                "name": "检查空口令账号",
                                "description": "检测系统中是否存在空口令账号",
                                "category": "系统安全",
                                "dep": 1
                            }
                        ]
                    }
                }
            }
        ),
        500: openapi.Response(
            description="服务器内部错误",
            examples={
                "application/json": {
                    "code": 500,
                    "message": "获取加固项列表时出错: 具体错误信息",
                    "data": None
                }
            }
        )
    }
)

@api_view(['GET'])
def harden_items_list(request):
    """
    获取所有可用的加固项列表
    
    动态扫描department_1_policy、department_2_policy、department_3_policy......目录下的YAML文件
    
    Returns:
        加固项列表, 包含id、name、description、category、dep等信息
    """
    try:
        items = []
        base_path = Path("/opt/cu-concrete").resolve()
        # 定义部门映射
        dep_mapping = {
            'department_1_policy': '系统安全',
            'department_2_policy': '容器安全',
            'department_3_policy': '应用安全'
        }

        # 扫描三个策略目录
        for dep_dir, category in dep_mapping.items():
            dep_path = base_path / dep_dir

            if not dep_path.exists():
                continue
            
            # 遍历目录下的所有子目录
            for item_dir in dep_path.iterdir():
                
                if not item_dir.is_dir():
                    continue
                    
                # 查找YAML文件
                yaml_files = list(item_dir.glob('*.yaml'))
                if not yaml_files:
                    continue
                    
                yaml_file = yaml_files[0]
                
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    if config and 'description' in config:
                        items.append({
                            'id': item_dir.name,
                            'name': config.get('description', item_dir.name),
                            'description': config.get('description', ''),
                            'category': category,
                            'dep': config.get('dep', 0),
                            'item_id': config.get('id', 0)
                        })
                except Exception as e:
                    logger.warning(f"读取YAML文件失败 {yaml_file}: {str(e)}")
                    continue
        # 按部门和ID排序
        items.sort(key=lambda x: (x['dep'], x['item_id']))
        return CommonResponses.QUERY_SUCCESS({
            'count': len(items),
            'list': items
        })
    except Exception as e:
        logger.error(f"获取加固项列表时出错: {str(e)}")
        return ApiResponse.error(f'获取加固项列表时出错: {str(e)}', 500)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'pool_id': openapi.Schema(type=openapi.TYPE_STRING, description='云池ID'),
            'hosts': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description='选择的机器列表'),
            'harden_items': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description='选择的加固项ID列表'),
        },
        required=['pool_id', 'hosts', 'harden_items']
    ),
    responses={
        200: openapi.Response(
            description="生成配置文件成功",
            examples={
                "application/json": {
                    "code": 200,
                    "message": "配置文件生成成功",
                    "data": {
                        "ini_content": "inventory.ini内容",
                        "yml_content": "playbook.yml内容",
                        "filename": "配置包文件名"
                    }
                }
            }
        )
    }
)

# 生成配置
@api_view(['POST'])
def generate_config(request):
    """
    根据选择的云池、机器和加固项生成Ansible配置文件
    
    直接修改 /opt/cu-concrete/data/fetch/fetch.ini 和 fetch.yml 文件
    
    Request Body:
        pool_id (str): 云池ID
        hosts (list): 选择的机器列表, 包含ip、name等信息
        harden_items (list): 选择的加固项ID列表
    
    Returns:
        操作结果
    """
    try:
        data = request.data
        # 定义参数：(参数名, 默认值)
        required_params = [
            ("pool_id", None),
            ("hosts", []),
            ("harden_model", None),
            ("harden_items", []),
        ]
        # 统一获取 + 校验 + 组装字典
        params_dict = {}
        for name, default in required_params:
            value = data.get(name, default)
            if not value:
                return CommonResponses.MISSING_PARAMETER(name)
            params_dict[name] = value
        params_json = json.dumps(params_dict)
        # 生成配置并保存
        return event_bus.eventbus_generate_config(params_json)
    
    except Exception as e:
        logger.error(f"生成配置文件时出错: {str(e)}")
        return ApiResponse.error(f'生成配置文件时出错: {str(e)}', 500)

# 保存生成的配置文件
@api_view(['GET', 'POST'])
def save_generated_config(request):
    try:
        data = request.data
        # 定义所有需要校验的参数：(参数名, 默认值)
        required_params = [
            ("pool_id", None),
            ("hosts", []),
            ("harden_model", None),
            ("harden_items", []),
            ("generate_person_name", None),
            ("config_name", None),
            ("ini_content", None),
            ("yml_content", None),
        ]
        # 统一获取 + 统一校验
        params_dict = {}
        for name, default in required_params:
            value = data.get(name, default)
            # 空值直接返回
            if not value:
                return CommonResponses.MISSING_PARAMETER(name)
            params_dict[name] = value
        # 最终 JSON
        params_json = json.dumps(params_dict)
        # 保存配置文件
        return event_bus.eventbus_save_generated_config(params_json)
        
    except Exception as e:
        logger.error(f"生成配置文件时出错: {str(e)}")
        return ApiResponse.error(f'生成配置文件时出错: {str(e)}', 500)

# 根据pool名获取所有配置文件名
@api_view(['GET', 'POST'])
def from_pool_get_configs(request):
    """
    根据pool名获取所有配置文件名
    """
    try:
        # 正确获取pool_id参数
        if request.method == 'GET':
            pool_id = request.query_params.get('pool_id')
        else:  # POST
            pool_id = request.data.get('pool_id')
        
        if not pool_id:
            return CommonResponses.MISSING_PARAMETER('pool_id')
        
        # 直接调用并返回
        return event_bus.eventbus_find_pool_configs(pool_id)
    except Exception as e:
        logger.error(f"获取配置列表时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'获取所有配置文件名时出错: {str(e)}', 500)   

# 根据配置文件名获取配置文件内容
@api_view(['GET', 'POST'])
def from_file_get_config(request):
    try:
        # 正确获取参数 - 区分GET和POST请求
        if request.method == 'GET':
            pool_id = request.query_params.get('pool_id')
            config_name = request.query_params.get('config_name')
        else:  # POST
            pool_id = request.data.get('pool_id')
            config_name = request.data.get('config_name')
        
        if not pool_id:
            return CommonResponses.MISSING_PARAMETER('pool_id')
        if not config_name:
            return CommonResponses.MISSING_PARAMETER('config_name')
        
        # 传递两个参数给event_bus
        return event_bus.eventbus_get_config_content(pool_id, config_name)
    except Exception as e:
        logger.error(f"获取配置文件内容时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'获取配置文件内容时出错: {str(e)}', 500)

# 保存修改的配置文件内容
@api_view(['GET', 'POST'])
def save_conf_content(request):
    """
    保存修改后的配置内容
    接收POST请求, 包含:
    - pool_name: 云池名称
    - config_name: 配置名称
    - ini_content: 修改后的INI内容
    - yml_content: 修改后的YML内容
    """
    if request.method == 'POST':
        try:
            # 解析JSON数据
            data = json.loads(request.body)
            
            # 获取请求参数
            pool_id = data.get('pool_id')
            config_name = data.get('config_name')
            ini_content = data.get('ini_content')
            yml_content = data.get('yml_content')
            
            # 验证必要参数
            if not all([pool_id, config_name, ini_content, yml_content]):
                return JsonResponse({
                    'code': 400,
                    'message': '缺少必要参数',
                    'data': None
                }, status=400)
            
            # 这里添加实际保存配置的逻辑
            return event_bus.eventbus_save_conf_content(pool_id, config_name, ini_content, yml_content)
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'message': f'服务器错误: {str(e)}',
                'data': None
            }, status=500)
    
    return JsonResponse({
        'code': 405,
        'message': '方法不允许',
        'data': None
    }, status=405)
    
# 删除配置
@api_view(['GET', 'POST'])
def delete_conf(request):
    """
    删除指定配置
    接收POST请求, 包含:
    - pool_id: 云池ID（如 pool-1）
    - config_name: 配置文件名（如 playbook_123456.yml）
    """
    if request.method == 'POST':
        try:
            # 解析JSON数据
            data = json.loads(request.body)
            
            # 获取请求参数
            pool_id = data.get('pool_id')
            config_name = data.get('config_name')
            
            # 验证必要参数
            if not all([pool_id, config_name]):
                return CommonResponses.MISSING_PARAMETER('pool_id 或 config_name')
            
            # 调用工具函数
            return event_bus.eventbus_delete_conf(pool_id, config_name)
            
        except Exception as e:
            logger.error(f"删除配置时出错: {str(e)}", exc_info=True)
            return ApiResponse.error(f'删除配置时出错: {str(e)}', 500)
    
    return ApiResponse.error('方法不允许', 405)


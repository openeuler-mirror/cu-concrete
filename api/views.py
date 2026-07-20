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

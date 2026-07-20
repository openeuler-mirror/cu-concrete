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

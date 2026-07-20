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

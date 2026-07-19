# 做事件总线, 实现功能：
# 1、使用单例模式
# 2、实现事业部 和 公司层 的加固项匹配
# 3、生成ansible脚本 并生成记录

from rest_framework.response import Response
from rest_framework import status
import threading
import os
import time
from .conf_utils import *
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses


class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

class Eventbus(Singleton):
    def __init__(self):
        # 双重校验，避免重复初始化
        if hasattr(self, '_initialized'):
            return

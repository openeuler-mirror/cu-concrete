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
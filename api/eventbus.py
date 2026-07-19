# 做事件总线, 实现功能：
# 1、使用单例模式
# 2、实现事业部 和 公司层 的加固项匹配
# 3、生成ansible脚本 并生成记录

from rest_framework.response import Response
from rest_framework import status
import threading
import os
import time

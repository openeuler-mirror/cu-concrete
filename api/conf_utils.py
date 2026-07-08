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
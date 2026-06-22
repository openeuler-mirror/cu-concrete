import os
import importlib.util
import subprocess
import time
import logging
import pickle
import time
import Panda as pd
_module_cache = {}
_cls_cache = {}

def load_check_class(department_id):
    """
    根据部门ID和策略ID,自动查找并实例化对应的类
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    department_folder = f'department_{department_id}_policy'
    department_path = os.path.join(base_path, department_folder)
    department_data_pkl = os.path.join(department_path, 'data_status.pkl')
    if not os.path.isdir(department_path):
        raise FileNotFoundError(f'未找到部门策略文件夹：{department_path}')
    global _module_cache, _cls_cache
    fixinstance = {}
    rbinstancee = {}
    resetinstance = {}

def load_sec_class(department_id):
    """
    根据部门ID和策略ID,自动查找并实例化对应的类
    """
    pass

def load_departments(department_ids):
    """
    批量加载多个部门的策略模块并使用单个进度条展示进度。
    department_ids: 可迭代的部门数字（例如 [1,2])
    返回 [fixinstance, rbinstancee, resetinstance] 三个字典，键为描述，值为实例
    """
    pass

def load_departments_no_ui(department_ids):
    """
    批量加载多个部门的策略模块但不显示进度条。
    department_ids: 可迭代的部门数字（例如 [1,2])
    返回 [fixinstance, rbinstancee, resetinstance] 三个字典，键为描述，值为实例
    """
    pass
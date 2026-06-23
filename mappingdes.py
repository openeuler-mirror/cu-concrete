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
    cmd = ['whiptail', '--title', '正在加载策略...', '--gauge', '正在检测安全策略状态...', '10', '70', '0']
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
    listfolder = [folder for folder in os.listdir(department_path) if folder not in ['.git', '__pycache__'] and os.path.isdir(os.path.join(department_path, folder))]
    status = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    status.to_pickle(department_data_pkl)
    for i, folder in enumerate(listfolder):
        folder_path = os.path.join(department_path, folder)
        module_name = folder
        module_path = os.path.join(folder_path, f'{module_name}.py')
        if not os.path.isfile(module_path):
            continue
        if module_name not in _cls_cache:
            if module_name not in _module_cache:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                _module_cache[module_name] = module
            cls = getattr(_module_cache[module_name], module_name)
            _cls_cache[module_name] = cls
        else:
            cls = _cls_cache[module_name]
        try:
            instance = cls()
            if not instance.check():
                fixinstance[instance.get_des()] = instance
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'status'] = 0
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'module_name'] = module_name
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'module_path'] = module_path
            else:
                rbinstancee[instance.get_des()] = instance
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'status'] = 2
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'module_name'] = module_name
                status.loc[str(instance.config['dep']) + str(instance.config['id']), 'module_path'] = module_path
            percent = int((i + 1) / len(listfolder) * 100)
            process.stdin.write(f'{percent}\n')
            process.stdin.flush()
            time.sleep(0.001)
        except AttributeError:
            raise AttributeError(f'模块 {module_name} 中未找到类 {module_name}')
    status.to_pickle(department_data_pkl)
    process.stdin.close()
    process.wait()
    return [fixinstance, rbinstancee, resetinstance]

def load_sec_class(department_id):
    """
    根据部门ID和策略ID,自动查找并实例化对应的类
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    department_folder = f'department_{department_id}_policy'
    department_path = os.path.join(base_path, department_folder)
    department_data_pkl = os.path.join(department_path, 'data_status.pkl')
    if not os.path.isdir(department_path):
        raise FileNotFoundError(f'未找到部门策略文件夹：{department_path}')
    fixinstance = {}
    rbinstancee = {}
    resetinstance = {}
    start_time = time.time()
    status = pd.read_pickle(department_data_pkl)
    global _module_cache, _cls_cache
    for index, value in status['status'].items():
        module_name = status.loc[index, 'module_name']
        module_path = status.loc[index, 'module_path']
        if module_name not in _cls_cache:
            if module_name not in _module_cache:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                _module_cache[module_name] = module
            cls = getattr(_module_cache[module_name], module_name)
            _cls_cache[module_name] = cls
        else:
            cls = _cls_cache[module_name]
        instance = cls()
        if value == 0:
            fixinstance[instance.get_des()] = instance
        elif value == 1:
            resetinstance[instance.get_des()] = instance
        else:
            rbinstancee[instance.get_des()] = instance
    return [fixinstance, rbinstancee, resetinstance]

def load_departments(department_ids):
    """
    批量加载多个部门的策略模块并使用单个进度条展示进度。
    department_ids: 可迭代的部门数字（例如 [1,2])
    返回 [fixinstance, rbinstancee, resetinstance] 三个字典，键为描述，值为实例
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    global _module_cache, _cls_cache
    fixinstance = {}
    rbinstancee = {}
    resetinstance = {}
    entries = []
    for dep in department_ids:
        department_folder = f'department_{dep}_policy'
        department_path = os.path.join(base_path, department_folder)
        department_data_pkl = os.path.join(department_path, 'data_status.pkl')
        if not os.path.isdir(department_path):
            logging.warning(f'未找到部门策略文件夹：{department_path}')
            continue
        for folder in os.listdir(department_path):
            folder_path = os.path.join(department_path, folder)
            if folder in ['.git', '__pycache__']:
                continue
            if not os.path.isdir(folder_path):
                continue
            module_name = folder
            module_path = os.path.join(folder_path, f'{module_name}.py')
            if not os.path.isfile(module_path):
                continue
            entries.append((dep, module_name, module_path, department_data_pkl))
    total = len(entries)
    cmd = ['whiptail', '--title', '正在加载策略...', '--gauge', '正在检测安全策略状态...', '10', '70', '0']

def load_departments_no_ui(department_ids):
    """
    批量加载多个部门的策略模块但不显示进度条。
    department_ids: 可迭代的部门数字（例如 [1,2])
    返回 [fixinstance, rbinstancee, resetinstance] 三个字典，键为描述，值为实例
    """
    pass
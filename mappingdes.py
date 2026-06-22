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
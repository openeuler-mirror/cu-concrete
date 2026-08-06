import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import json
import yaml
import time
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)
#TestCase-部门编号-子加固项名称-子加固项编号
class DelDangeFile_19(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "DelDangeFile_19.yaml")
        with open(file=self.config_file,mode='r+',encoding='utf-8') as f :
            config = yaml.load(f,Loader = yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None

    def finalfix(self):
        self.status=2
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=2
        self.status_form.to_pickle(self.pkl_file)

    def fix(self):
        self.status = 1
        # 每次加固前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)
        
        # 搜索并处理危险文件
        home_dir = self.config['query']['path']
        for file_name in self.config['query']['form']:
            cmd = ['find', home_dir, '-type', 'f', '-name', file_name]
            result = base_shell(cmd)
            if result[1] == 0 and result[0]:
                file_list = result[0].strip().split('\n')
                for file_path in file_list:
                    if file_path:
                        # 备份文件（_bak后缀）
                        bsf.cp_shell(file_path, file_path + '_bak')
                        # 删除原文件
                        cmd_rm = ['rm', '-f', file_path]
                        base_shell(cmd_rm)
        
        data = 'type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()

    def check(self):
        except_value = True
        home_dir = self.config['query']['path']
        dangerous_files = self.config['query']['form']  # ['.netrc', '.rhosts']
        
        # 遍历/home目录检查是否存在危险文件
        for root, dirs, files in os.walk(home_dir):
            for file in files:
                if file in dangerous_files:
                    except_value = False
                    return except_value
        
        return except_value
    
    def rollback(self):
        home_dir = self.config['query']['path']
        for file_name in self.config['query']['form']:
            # 1. 先查找原始文件是否存在
            cmd_find = ['find', home_dir, '-type', 'f', '-name', file_name]
            result = base_shell(cmd_find)

            if result[1] == 0 and result[0]:
                # 原始文件已存在，跳过
                continue

            # 2. 原始文件不存在，查找备份文件
            cmd_find_bak = ['find', home_dir, '-type', 'f', '-name', file_name + '_bak']
            result_bak = base_shell(cmd_find_bak)

            if result_bak[1] == 0 and result_bak[0]:
                # 3. 有备份文件，重命名恢复
                backup_files = result_bak[0].strip().split('\n')
                for backup_file in backup_files:
                    if backup_file and backup_file.endswith('_bak'):
                        original_file = backup_file[:-4]
                        bsf.mv_shell(backup_file, original_file)
            else:
                # 4. 没有备份文件，创建空的原始文件
                original_path = os.path.join(home_dir, file_name)
                bsf.touch_shell(original_path)

        # 更新状态
        result = self.check()
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import json
import yaml
import re
import time
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
# import pandas as pd
import Panda as pd
logger = logging.getLogger(__name__)
# TestCase-部门编号-子加固项名称-子加固项编号
# 优化：统一日志变量命名
class CheckUidZero_4(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "CheckUidZero_4.yaml")
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
        bsf.cp_shell(self.config['query'][0]['path'],self.config['backup_path'])
        result=bsf.awk_shell(":",self.config['query'][0]['form'],self.config['query'][0]['path'])
        users = [user for user in result[0].splitlines() if user != 'root']
        for user in users:
            cmd=['id',user]
            uid_str=base_shell(cmd)[0]
            match = re.search(r'uid=(\d+)', uid_str)
            if match and int(match.group(1)) == 0:
                cmd=['userdel','-f',user]
                base_shell(cmd)
        data = f"type:fix,des:{self.config['description']}"
        logging.info(data)
        self.finalfix()
        
    def check(self):
        expected_value = True
        result=bsf.awk_shell(":",self.config['query'][0]['form'],self.config['query'][0]['path'])
        users = [user for user in result[0].splitlines() if user != 'root']
        for user in users:
            cmd=['id',user]
            uid_str=base_shell(cmd)[0]
            match = re.search(r'uid=(\d+)', uid_str)
            if match and int(match.group(1)) == 0:
                expected_value = False
        return expected_value
            

    def rollback(self):
        pass
        result = self.check()
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
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

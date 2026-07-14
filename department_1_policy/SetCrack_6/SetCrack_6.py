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
logger = logging.getLogger(__name__)
# TestCase-部门编号-子加固项名称-子加固项编号
# 优化：统一日志变量命名
class SetCrack_6(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "SetCrack_6.yaml")
        with open(file=self.config_file, mode='r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.Loader)
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
        bsf.touch_shell(self.config['backup_path'])
        bsf.cp_shell(self.config['query']['path'], self.config['backup_path'])
        flag = bsf.grep_shell(self.config['query']['form'], self.config['query']['path'])
        if len(flag[0]) != 0:
            bsf.sed_shell(flag[0], self.config['change']['value'], self.config['query']['path'])
        else:
            cmd = ['sudo', 'tee', '-a', self.config['query']['path']]
            value = self.config['change']['value']
            base_shell(cmd, input=f'\n{value}')
        data = 'type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()
    
    def check(self):
        """检查策略是否满足要求。"""
        expected_value = True
        result=bsf.grep_shell(self.config['change']['value'],self.config['query']['path'])
        if result[1]!=0:
            expected_value = False
        return expected_value

    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        bsf.cp_shell(self.config['backup_path'], self.config['query']['path'])
        result = self.check()
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description


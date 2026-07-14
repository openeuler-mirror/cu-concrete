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
class RebuildUser_5(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "RebuildUser_5.yaml")
        with open(file=self.config_file, mode='r', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None

    def finalfix(self):
        self.status = 2
        key = str(self.config['dep']) + str(self.config['id'])
        self.status_form.loc[key, 'status'] = 2
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
        if len(bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0])!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0],self.config['change']['value'][0],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][0],self.config['query']['path'])
        if len(bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0])!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0],self.config['change']['value'][1],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][1],self.config['query']['path'])
        if len(bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0])!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0],self.config['change']['value'][2],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][2],self.config['query']['path'])
        if len(bsf.grep_shell(self.config['query']['form'][3],self.config['query']['path'])[0])!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][3],self.config['query']['path'])[0],self.config['change']['value'][3],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][3],self.config['query']['path'])
        data = f"type:fix,des:{self.config['description']}"
        logging.info(data)
        self.finalfix()
        
        
    def check(self):
        """检查策略是否满足要求。"""
        expected_value = True
        line = bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0]

        parts = line.split()  # 按换行字符分割
        value = int(parts[1])  # 第二个元素是数值
 
        if value==99999:
            expected_value = False
            
        line = bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0]
        parts = line.split()  # 按空白字符分割
        value = int(parts[1])  # 第二个元素是数值

        if value==5:
            expected_value = False

        line = bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0]
        parts = line.split()  # 按空白字符分割
        value = int(parts[1])  # 第二个元素是数值

        if value==0:
            expected_value = False
            
        line = bsf.grep_shell(self.config['query']['form'][3],self.config['query']['path'])[0]
        parts = line.split()  # 按空白字符分割
        value = int(parts[1])  # 第二个元素是数值

        if value!=7:
            expected_value = False
        return expected_value

    def rollback(self):
        if bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0]!=None:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0],self.config['recovery']['value'][0],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][0],self.config['query']['path'])
            
        if bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0]!=None:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0],self.config['recovery']['value'][1],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][1],self.config['query']['path'])
            
        if bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0]!=None:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0],self.config['recovery']['value'][2],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][2], self.config['query']['path'])

        if bsf.grep_shell(self.config['query']['form'][3], self.config['query']['path'])[0] is not None:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][3], self.config['query']['path'])[0], self.config['recovery']['value'][3], self.config['query']['path'])
        else:
            bsf.append_line(self.config['recovery']['value'][3], self.config['query']['path'])
        result = self.check()
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            bsf.append_line(self.config['recovery']['value'][3],self.config['query']['path'])
        result=self.check()
        if result==False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description

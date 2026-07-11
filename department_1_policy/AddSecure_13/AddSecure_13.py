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
class AddSecure_13(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "AddSecure_13.yaml")
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
        cmd = ['id', self.config['query']['form']]
        result = base_shell(cmd)
        if result[1] != 0:
            cmd2 = ['useradd', self.config['query']['form']]
            base_shell(cmd2)
            cmd='{}:{}'.format(self.config['query']['form'],self.config['change']['value1'])
            base_shell(['chpasswd'],input=cmd)

        
        bsf.remove_line(self.config['change']['value2'],self.config['query']['path'])
        cmd=['sudo','tee','-a',self.config['query']['path']]
        value=self.config['change']['value2']
        base_shell(cmd,input=f'\n{value}')
        
        cmd3=['mkdir','-p',self.config['change']['path1']]
        base_shell(cmd3)
        cmd4=['chmod',self.config['change']['value3'][0],self.config['change']['path1']]
        base_shell(cmd4)
        
        if not os.path.exists(self.config['change']['path2']) and os.path.exists(self.config['query']['path2']):
            bsf.cp_shell(self.config['query']['path2'],self.config['change']['path2'])
            cmd4=['chmod',self.config['change']['value3'][1],self.config['change']['path2']]
            base_shell(cmd4)
            u_g="{}:{}".format(self.config['query']['form'],self.config['query']['form'])
            cmd5=['chown',u_g,self.config['change']['path2']]
            base_shell(cmd5)
        
        if not os.path.exists(self.config['change']['path3']) and os.path.exists(self.config['query']['path3']):
            bsf.cp_shell(self.config['query']['path3'],self.config['change']['path3'])
            cmd6=['chmod',self.config['change']['value3'][2],self.config['change']['path3']]
            base_shell(cmd6)
            u_g="{}:{}".format(self.config['query']['form'],self.config['query']['form'])
            cmd7=['chown',u_g,self.config['change']['path3']]
            base_shell(cmd7)
        
        if not os.path.exists(self.config['change']['path4']) and os.path.exists(self.config['query']['path4']):
            bsf.cp_shell(self.config['query']['path4'],self.config['change']['path4'])
            cmd7=['chmod',self.config['change']['value3'][2],self.config['change']['path4']]
            base_shell(cmd7)
            u_g="{}:{}".format(self.config['query']['form'],self.config['query']['form'])
            cmd8=['chown',u_g,self.config['change']['path4']]
            base_shell(cmd8)
        data = f"type:fix,des:{self.config['description']}"
        logging.info(data) 
        self.finalfix()  
        
    def check(self):
        expected_value = True
        cmd=['id',self.config['query']['form']]
        result=base_shell(cmd)
        if result[1]!=0:
            expected_value = False
        return expected_value
        
    def rollback(self):
        result=base_shell(['lsattr','/etc/passwd'])
        if 'i' in result[0]:
            base_shell(['chattr','-i','/etc/passwd'])
            base_shell(['chattr','-i','/etc/shadow'])
            base_shell(['chattr','-i','/etc/group'])
            cmd=['userdel','-f',self.config['query']['form']]
            base_shell(cmd)
            base_shell(['chattr','+i','/etc/passwd'])
            base_shell(['chattr','+i','/etc/shadow'])
            base_shell(['chattr','+i','/etc/group'])
        else:
            cmd=['userdel','-f',self.config['query']['form']]
            base_shell(cmd)
        bsf.remove_line(self.config['change']['value2'],self.config['query']['path'])
        cmd2=['rm','-rf',self.config['change']['path']]
        base_shell(cmd2)
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

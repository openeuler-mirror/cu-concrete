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
class RmToShred_31(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "RmToShred_31.yaml")
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
            
        # 将系统原生rm命令移动为rm-rule备份
        backup_cmd = ['bash', '-c', "sudo mv /usr/bin/rm /usr/bin/rm-rule 2>/dev/null || true"]
        base_shell(backup_cmd)
            
        # 创建新的rm脚本文件，包含shred安全删除功能
        rm_script_content = self.config['change']['value']
            
        # 写入新的rm脚本文件
        script_cmd = ['sudo', 'tee', '/usr/bin/rm']
        base_shell(script_cmd, input=f'#!/bin/bash\n\n{rm_script_content}')
            
        # 设置脚本执行权限
        chmod_cmd = ['bash', '-c', 'sudo chmod +x /usr/bin/rm']
        base_shell(chmod_cmd)
            
        data='type:fix,des:{}'.format(self.config['description'])
        logging.info(data) 
        self.finalfix()

    def check(self):
        # 检查/usr/bin/rm脚本文件是否存在且包含正确的函数定义
        import os
        if not os.path.exists('/usr/bin/rm'):
            return False
        
        # 检查文件内容是否包含预期的rm函数定义
        result = bsf.grep_shell(self.config['query']['form'], '/usr/bin/rm')
        if len(result[0]) != 0:
            # 如果找到了函数定义，说明加固成功
            return True
        else:
            # 没有找到函数定义
            return False
    
    def rollback(self):
        # 删除自定义的rm脚本文件
        delete_cmd = ['bash', '-c', 'sudo rm -f /usr/bin/rm']
        base_shell(delete_cmd)
                
        # 将rm-rule恢复为rm
        restore_cmd = ['bash', '-c', 'sudo mv /usr/bin/rm-rule /usr/bin/rm 2>/dev/null || true']
        base_shell(restore_cmd)
                
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

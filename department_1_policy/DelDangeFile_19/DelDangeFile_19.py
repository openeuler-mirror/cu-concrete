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
        
        # 查找危险文件
        cmd=['find','/home','-type','f','-name',self.config['query']['form'][0]]
        cmd2=['find','/home','-type','f','-name',self.config['query']['form'][1]]
        
        result1=base_shell(cmd)
        result2=base_shell(cmd2)
        # 处理查找到的文件
        if result1[1] == 0 and result1[0]:  # 如果命令执行成功且找到了文件
            files1 = result1[0].strip().split('\n')

            for file_path in files1:
                if file_path:  # 确保路径不为空
                    # 备份文件
                    bsf.cp_shell(file_path, file_path+'.bak')
                    # 删除文件
                    cmd_rm = ['rm', '-f', file_path]
                    base_shell(cmd_rm)
                    
        if result2[1] == 0 and result2[0]:  # 如果命令执行成功且找到了文件
            files2 = result2[0].strip().split('\n')
            for file_path in files2:
                if file_path:  # 确保路径不为空
                    # 备份文件
                    bsf.cp_shell(file_path, file_path+'.bak')
                    # 删除文件
                    cmd_rm = ['rm', '-f', file_path]
                    base_shell(cmd_rm)
                    
        data='type:fix,des:{}'.format(self.config['description'])
        logging.info(data) 
        self.finalfix() 

    def check(self):
        except_value=True
        cmd=['find','/home','-type','f','-name',self.config['query']['form'][0]]
        cmd2=['find','/home','-type','f','-name',self.config['query']['form'][1]]
        result1=base_shell(cmd)
        result2=base_shell(cmd2)
        
        # # 输出调试信息（实际使用时应该移除）
        # print(result1,result2,self.config['query']['form'])
        
        # 检查是否有找到危险文件
        # 如果命令执行成功（返回码为0）且找到了文件（stdout不为空），则需要加固
        if (result1[1] == 0 and result1[0]) or (result2[1] == 0 and result2[0]):
            except_value=False
        return except_value
    
    def rollback(self):
        # 在回滚时，应该恢复备份的文件
        cmd=['find','/home','-type','f','-name',self.config['query']['form'][0]+'.bak']
        cmd2=['find','/home','-type','f','-name',self.config['query']['form'][1]+'.bak']
        
        result1=base_shell(cmd)
        result2=base_shell(cmd2)
        
        if result1[1] == 0 and result1[0]:
            backup_files1 = result1[0].strip().split('\n')
            for backup_file in backup_files1:
                if backup_file and backup_file.endswith('.bak'):
                    original_file = backup_file[:-4]  # 移除.bak后缀
                    bsf.cp_shell(backup_file, original_file)
                    
        if result2[1] == 0 and result2[0]:
            backup_files2 = result2[0].strip().split('\n')
            for backup_file in backup_files2:
                if backup_file and backup_file.endswith('.bak'):
                    original_file = backup_file[:-4]  # 移除.bak后缀
                    bsf.cp_shell(backup_file, original_file)
        
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
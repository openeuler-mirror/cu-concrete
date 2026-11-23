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
import logging
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_18_SetLoginBanner(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_18_SetLoginBanner.yaml")
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
        banner = self.config['banner']
        paths = self.config['query']['path']
        backups = self.config['change']['value']
        for i, path in enumerate(paths):
            # 备份原文件
            if os.path.isfile(path):
                bsf.cp_shell(path, backups[i])
            # 删除原文件并重建, 写入警告语
            # 先删除(含符号链接场景, lexists 可识别断链), 再重建普通文件
            if os.path.lexists(path):
                os.remove(path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(banner + '\n')
            bsf.chown_file('root:root', path)
            bsf.chmod_file('644', path)
        self.finalfix()

    def check(self):
        # 三个文件均存在且内容为警告语, 才视为已加固
        banner = self.config['banner']
        for path in self.config['query']['path']:
            if not os.path.isfile(path):
                return False
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                if f.read().strip() != banner:
                    return False
        return True

    def rollback(self):
        paths = self.config['query']['path']
        backups = self.config['change']['value']
        for i, path in enumerate(paths):
            # 有备份则用备份覆盖还原; 原文件本就不存在时还原为不存在
            if os.path.isfile(backups[i]):
                bsf.cp_shell(backups[i], path)
            elif os.path.exists(path):
                os.remove(path)
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

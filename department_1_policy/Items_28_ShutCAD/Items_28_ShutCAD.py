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
class Items_28_ShutCAD(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_28_ShutCAD.yaml")
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
        path = self.config['query']['path']
        # 加固态 = 该软链接不存在
        # 用 lexists 而不是 exists: 软链接目标被删(断链)时 exists 返回 False, 断链会漏删
        if os.path.lexists(path):
            # os.remove 删除的是软链接本身,不会跟到目标文件
            os.remove(path)
        # 软链接变化后让 systemd 重新加载 unit, 否则旧的 unit 仍在缓存里
        base_shell(['systemctl', 'daemon-reload'])
        self.finalfix()
    
    def check(self):
        # check() 返回 True = 已加固; 返回 False = 未加固
        # 已加固 = 该软链接不存在
        # 用 lexists: 断链的软链接也算"存在", 必须算未加固
        path = self.config['query']['path']
        return not os.path.lexists(path)
    
    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        path = self.config['query']['path']
        target = self.config['query']['link_target']
        # 还原: 重新创建软链接(ln -sfn 覆盖已存在的同名链接)
        base_shell(['ln', '-sfn', target, path])
        # 软链接变化后让 systemd 重新加载 unit
        base_shell(['systemctl', 'daemon-reload'])
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

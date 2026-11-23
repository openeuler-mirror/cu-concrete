import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import yaml
import logging
from base_fix import base_fix
from base_shell import base_shell
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)


#TestCase-部门编号-子加固项名称-子加固项编号
class Items_39_DisUnkFailLog(base_fix):
    """关闭未知账号登录失败日志：/etc/login.defs 中设置 LOG_UNKFAIL_ENAB no"""

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_39_DisUnkFailLog.yaml")
        with open(file=self.config_file, mode='r+', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.Loader)
        self.pkl_file = os.path.join(os.path.dirname(self.current_dir), 'data_status.pkl')
        self.config = config
        self.status = None
        self.status_form = None

    def finalfix(self):
        self.status = 2
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status'] = 2
        self.status_form.to_pickle(self.pkl_file)

    def fix(self):
        self.status = 1
        # 每次加固前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        if self.status_form is None:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)
        path = self.config['path']
        # 写入加固值
        for e in self.config['entries']:
            self.set_kv(path, e['key'], e.get('value', ''), sep=e.get('sep', ' '))
        self.finalfix()

    def check(self):
        # 所有配置项都达到加固值才视为已加固
        path = self.config['path']
        for e in self.config['entries']:
            if not self.is_hardened(path, e['key'], e.get('value', ''), e.get('sep', ' ')):
                return False
        return True

    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        if self.status_form is None:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        path = self.config['path']
        # 还原: 本项所有配置项都不设还原值, 统一删除该配置行, 回到 sshd 内置默认值
        for e in self.config['entries']:
            self.remove_kv(path, e['key'], e.get('sep', ' '))
        result = self.check()
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description = self.config['description']
        return description
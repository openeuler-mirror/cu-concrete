"""
系统还原模块
"""
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from checklist import checklist
from rollbacklist import rollbacklist

class Restorer:

    def __init__(self, logger):
        self.logger = logger
        self.checker = checklist()
        self.rollback_list = rollbacklist()

    def list_items(self):
        """列出所有可加固项"""
        print('正在扫描系统安全状态...')
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        flag_path = os.path.join(path, 'flag.txt')

    def restore_all(self):
        """还原所有已加固项"""
        pass

    def restore_items(self, item_ids):
        """还原指定ID的项"""
        pass

    def _execute_restore(self, items):
        """执行还原操作"""
        pass
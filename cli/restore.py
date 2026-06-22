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
        if not os.path.exists(flag_path):
            with open(flag_path, 'w', encoding='utf-8') as f:
                content = f.write('1')
                flag = 1
        else:
            with open(flag_path, 'r', encoding='utf-8') as f:
                flag = int(f.read().strip())
        if flag == 1:
            instance_tuple = self.checker.sub_checklist_noui()
            available_items = instance_tuple[1] if instance_tuple else []
            flag += 1
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(flag))
        else:
            instance_tuple = self.checker.sec_checklist()
            available_items = instance_tuple[1] if instance_tuple else []
        if not available_items:
            print('没有可还原项的项目')
            return
        print('\n可还原项列表:')
        print('-' * 50)
        for item in available_items[0]:
            print(f'{item[0]} - {item[1]}')

    def restore_all(self):
        """还原所有已加固项"""
        pass

    def restore_items(self, item_ids):
        """还原指定ID的项"""
        pass

    def _execute_restore(self, items):
        """执行还原操作"""
        pass
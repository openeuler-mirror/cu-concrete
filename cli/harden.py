"""
安全加固模块
"""
import os
import sys
import importlib.util
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from checklist import checklist
from fixlist import fixlist

class Hardener:

    def __init__(self, logger):
        self.logger = logger
        self.checker = checklist()
        self.fix_list = fixlist()

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
            available_items = instance_tuple[0] if instance_tuple else []
            flag += 1
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(flag))
        else:
            instance_tuple = self.checker.sec_checklist()
            available_items = instance_tuple[0] if instance_tuple else []
        if not available_items:
            print('没有可加固的项目')
            return
        print('\n可加固项列表:')
        print('-' * 50)
        for item in available_items[0]:
            print(f'{item[0]} - {item[1]}')
        print('-' * 50)
        print(f'总共 {len(available_items[0])} 个可加固项')

    def harden_all(self):
        """执行所有加固项"""
        self.logger.info('开始执行全部加固项')
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
            available_items = instance_tuple[0] if instance_tuple else []
            flag += 1
            with open(flag_path, 'w', encoding='utf-8') as f:
                f.write(str(flag))
        else:
            instance_tuple = self.checker.sec_checklist()
            available_items = instance_tuple[0] if instance_tuple else []
        if not available_items:
            print('没有可加固的项目')
            self.logger.info('没有可加固的项目')
            return
        print(f'发现 {len(available_items[0])} 个可加固项，开始执行...')
        self._execute_harden(available_items)
        self.logger.info('全部加固项执行完成')

    def harden_items(self, item_ids):
        """执行指定ID的加固项"""
        pass

    def _execute_harden(self, items):
        """执行加固操作"""
        pass
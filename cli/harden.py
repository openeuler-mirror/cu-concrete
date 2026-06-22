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
        print('加固完成！')

    def harden_items(self, item_ids):
        """执行指定ID的加固项"""
        self.logger.info(f'开始执行指定加固项: {item_ids}')
        print('正在扫描系统安全状态...')
        instance_tuple = self.checker.sec_checklist()
        available_items = instance_tuple[0] if instance_tuple else []
        target_item_ids = item_ids[1].split(',') if len(item_ids) > 1 else []
        target_items_list = [item for item in available_items[0] if item[0] in target_item_ids]
        target_instances = {}
        for description, instance in available_items[1].items():
            dep_id = '{}_{}'.format(instance.config['dep'], instance.config['id'])
            if dep_id in target_item_ids:
                target_instances[description] = instance
        target_items = (target_items_list, target_instances)
        if not target_items_list:
            print('没有匹配的可加固项')
            self.logger.warning('没有匹配的可加固项')
            return
        print(f'找到 {len(target_items[0])} 个匹配项，开始执行...')
        self._execute_harden(target_items)
        self.logger.info('指定加固项执行完成')
        print('加固完成！')

    def _execute_harden(self, items):
        """执行加固操作"""
        choice_list = []
        for desc, instance in items[1].items():
            choice_list.append(instance)
        for i, instance in enumerate(choice_list):
            dep_id = f"{instance.config['dep']}_{instance.config['id']}"
            description = instance.get_des()
            print(f'[{i + 1}/{len(choice_list)}] 正在加固 {description}...')
            try:
                instance.fix()
            except Exception as e:
                self.logger.error(f'加固失败 [{dep_id}] {description}: {e}')
                print(f'错误: {e}')
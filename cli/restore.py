"""
系统还原模块
"""

import os
import sys

# 添加项目根目录到Python路径
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
        print("正在扫描系统安全状态...")
        path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        flag_path = os.path.join(path, 'flag.txt')
        if not os.path.exists(flag_path):
            with open(flag_path, 'w', encoding='utf-8') as f:
                content = f.write("1")
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
            instance_tuple =  self.checker.sec_checklist()
            available_items = instance_tuple[1] if instance_tuple else []


        if not available_items:
            print("没有可还原项的项目")
            return
            
        print("\n可还原项列表:")
        print("-" * 50)
        for item in available_items[0]:
            print(f"{item[0]} - {item[1]}")
            # item 是一个元组 (dep_id, description, status)
            # dep_id, description, status = item[0],item[1],item[2]
            # print(f"[{dep_id}] {description}")
        print("-" * 50)
        print(f"总共 {len(available_items[0])} 个可还原项")
        
    def restore_all(self):
        """还原所有已加固项"""
        self.logger.info("开始执行全部还原项")
        print("正在扫描系统安全状态...")
        
        path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        flag_path = os.path.join(path, 'flag.txt')
        if not os.path.exists(flag_path):
            with open(flag_path, 'w', encoding='utf-8') as f:
                content = f.write("1")
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
            instance_tuple =  self.checker.sec_checklist()
            available_items = instance_tuple[1] if instance_tuple else []

                
        if not available_items:
            print("没有可还原的项目")
            self.logger.info("没有可还原的项目")
            return
            
        print(f"发现 {len(available_items[0])} 个可还原项，开始执行...")
        self._execute_restore(available_items)
        self.logger.info("全部还原项执行完成")
        print("还原完成！")
        
    def restore_items(self, item_ids):
        """还原指定ID的项"""
        self.logger.info(f"开始执行指定还原项: {item_ids}")
        print("正在扫描系统安全状态...")
        
        instance_tuple = self.checker.sec_checklist()
        # available_items 是 [(fixinstanse, fix_instance), ...] 格式
        available_items = instance_tuple[1] if instance_tuple else []
        
        # item_ids 是一个列表 ['items', '2-17,2-18']
        # 我们需要获取 '2-17,2-18' 并按逗号分割
        target_item_ids = item_ids[1].split(',') if len(item_ids) > 1 else []      
        # 从 available_items[0] (fixinstanse) 中筛选出匹配的项
        # fixinstanse 中的每个元素是 (dep_id, description, status) 元组
        target_items_list = [item for item in available_items[0] if item[0] in target_item_ids]
        
        # 从 available_items[1] (fix_instance) 中筛选出匹配的实例
        # 需要通过描述来匹配
        target_instances = {}
        for description, instance in available_items[1].items():
            # 构造dep_id用于比较
            dep_id = "{}_{}".format(instance.config['dep'], instance.config['id'])
            if dep_id in target_item_ids:
                target_instances[description] = instance

        # 构造传递给 _execute_harden 的数据结构
        target_items = (target_items_list, target_instances)
        
        if not target_items:
            print("没有匹配的可还原项")
            self.logger.warning("没有匹配的可还原项")
            return
            
        print(f"找到 {len(target_items[0])} 个匹配项，开始执行...")
        self._execute_restore(target_items)
        self.logger.info("指定还原项执行完成")
        print("还原完成！")
        
    def _execute_restore(self, items):
        """执行还原操作"""
        choice_list = []
        for desc,instance in items[1].items():
            choice_list.append(instance)
        # 执行还原
        for i, instance in enumerate(choice_list):
            dep_id = f"{instance.config['dep']}_{instance.config['id']}"
            description = instance.get_des()
            # 移除了INFO日志记录 self.logger.info(f"正在还原 [{dep_id}] {description}")
            print(f"[{i+1}/{len(choice_list)}] 正在还原 [{dep_id}] {description}...")
            try:
                instance.rollback()
                # 移除了INFO日志记录 self.logger.info(f"还原完成 [{dep_id}] {description}")
            except Exception as e:
                self.logger.error(f"还原失败 [{dep_id}] {description}: {e}")
                print(f"错误: {e}")
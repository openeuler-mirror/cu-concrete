from whiptail import Whiptail
import time
import subprocess
import os
from mappingdes import load_check_class,load_sec_class,load_departments,load_departments_no_ui
import re
import logging
TITLE = "安全加固工具"
HEIGHT = 25
WIDTH = 60

class checklist:
    
    def get_folder(self,i):
        folder_str='department_{}_policy'.format(i)
        return folder_str
    
    def sub_checklist(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        #获得未加固的（自增）子加固项列表，用于fixlist的自增列表项。
        fixinstanse=[]
        #获得未加固项的实例字典，用于fixlist的加固调用。
        fix_instance={}
        #获取同级目录下的所有文件夹      
        all_dir=[name for name in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, name))]
        #获得已加固的（自增）子加固项列表，用于rollback的自增列表项
        rbinstance=[]
        #获得已加固项的实例字典，用于rollback的加固调用。
        rb_instance={}

        #获得需修复的（自增）子加固项列表，用于reset的自增列表项
        resetinstance=[]
        #获得需修复的加固项的实例字典，用于reset的加固调用。
        reset_instance={}
        #folder_path按照_切分文件名，获取部门id号，调用load_check检测所有未被加固的加固项，并返回字典，字典键是des,字典值是实例对象。
        # for folder_path in [d for d in all_dir if d not in ['.git', '__pycache__']]:
        # 自动匹配所有 department_<n>_policy 文件夹，避免硬编码范围导致遗漏
        import re
        pattern = re.compile(r'^department_\d+_policy$')
        folder_list = [d for d in all_dir if pattern.match(d)]

        # 提取部门 id 列表并批量加载（只调用一次进度条）
        dept_ids = [int(d.split('_')[1]) for d in folder_list]
        if dept_ids:
            result = load_departments(dept_ids)
            fix_instance.update(result[0])
            rb_instance.update(result[1])
            reset_instance.update(result[2])
            fix_instance = dict(sorted(fix_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            rb_instance = dict(sorted(rb_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            reset_instance = dict(sorted(reset_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
        for index,key in enumerate(fix_instance.keys()):
            # fixinstanse.append(("{}".format(index+1),"{}".format(key),"off"))
            fixinstanse.append(("{}_{}".format(fix_instance[key].config['dep'],fix_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(rb_instance.keys()):
            # rbinstance.append(("{}".format(index+1),"{}".format(key),"off"))
            rbinstance.append(("{}_{}".format(rb_instance[key].config['dep'],rb_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(reset_instance.keys()):
            # resetinstance.append(("{}".format(index+1),"{}".format(key),"off"))
            # 这里应该向列表 `resetinstance` 添加项，之前误用 `reset_instance.append` 会导致 AttributeError
            resetinstance.append(("{}_{}".format(reset_instance[key].config['dep'],reset_instance[key].config['id']),"{}".format(key),"off"))
        return [(fixinstanse,fix_instance),(rbinstance,rb_instance),(resetinstance,reset_instance)]
    
    def sec_checklist(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        #获得未加固的（自增）子加固项列表，用于fixlist的自增列表项。
        fixinstanse=[]
        #获得未加固项的实例字典，用于fixlist的加固调用。
        fix_instance={}
        #获取同级目录下的所有文件夹      
        all_dir=[name for name in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, name))]
        #获得已加固的（自增）子加固项列表，用于rollback的自增列表项
        rbinstance=[]
        #获得已加固项的实例字典，用于rollback的加固调用。
        rb_instance={}

        #获得需修复的（自增）子加固项列表，用于reset的自增列表项
        resetinstance=[]
        #获得需修复的加固项的实例字典，用于reset的加固调用。
        reset_instance={}
        #folder_path按照_切分文件名，获取部门id号，调用load_check检测所有未被加固的加固项，并返回字典，字典键是des,字典值是实例对象。
        # for folder_path in [d for d in all_dir if d not in ['.git', '__pycache__']]:     
        folder_list=[]
        # for i in range(9):
        # for i in range(9):
        #     folder_list.append(self.get_folder(i+1))
        # for folder_path in [d for d in all_dir if pattern.match(d)]:
        # 逐部门读取每个文件夹下的 data_status.pkl（不重新执行检查）
        import re
        pattern = re.compile(r'^department_\d+_policy$')
        folder_list = [d for d in all_dir if pattern.match(d)]
        for folder_path in [d for d in folder_list if d in all_dir]:
            result = load_sec_class(int(folder_path.split('_')[1]))
            fix_instance.update(result[0])
            rb_instance.update(result[1])
            reset_instance.update(result[2])
            fix_instance = dict(sorted(fix_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            rb_instance = dict(sorted(rb_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            reset_instance = dict(sorted(reset_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
        for index,key in enumerate(fix_instance.keys()):
            # fixinstanse.append(("{}".format(index+1),"{}".format(key),"off"))
            fixinstanse.append(("{}_{}".format(fix_instance[key].config['dep'],fix_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(rb_instance.keys()):
            # rbinstance.append(("{}".format(index+1),"{}".format(key),"off"))
            rbinstance.append(("{}_{}".format(rb_instance[key].config['dep'],rb_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(reset_instance.keys()):
            # resetinstance.append(("{}".format(index+1),"{}".format(key),"off"))
             resetinstance.append(("{}_{}".format(reset_instance[key].config['dep'],reset_instance[key].config['id']),"{}".format(key),"off"))
        return [(fixinstanse,fix_instance),(rbinstance,rb_instance),(resetinstance,reset_instance)]


    def sub_checklist_noui(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        #获得未加固的（自增）子加固项列表，用于fixlist的自增列表项。
        fixinstanse=[]
        #获得未加固项的实例字典，用于fixlist的加固调用。
        fix_instance={}
        #获取同级目录下的所有文件夹      
        all_dir=[name for name in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, name))]
        #获得已加固的（自增）子加固项列表，用于rollback的自增列表项
        rbinstance=[]
        #获得已加固项的实例字典，用于rollback的加固调用。
        rb_instance={}

        #获得需修复的（自增）子加固项列表，用于reset的自增列表项
        resetinstance=[]
        #获得需修复的加固项的实例字典，用于reset的加固调用。
        reset_instance={}
        #folder_path按照_切分文件名，获取部门id号，调用load_check检测所有未被加固的加固项，并返回字典，字典键是des,字典值是实例对象。
        # for folder_path in [d for d in all_dir if d not in ['.git', '__pycache__']]:     
        folder_list=[]
        # for i in range(9):
        # for i in range(9):
        #     folder_list.append(self.get_folder(i+1))
        # for folder_path in [d for d in all_dir if pattern.match(d)]:
        # 逐部门读取每个文件夹下的 data_status.pkl（不重新执行检查）
        import re
        pattern = re.compile(r'^department_\d+_policy$')
        folder_list = [d for d in all_dir if pattern.match(d)]
        # 提取部门 id 列表并批量加载（只调用一次进度条）
        dept_ids = [int(d.split('_')[1]) for d in folder_list]
        if dept_ids:
            result = load_departments_no_ui(dept_ids)
            fix_instance.update(result[0])
            rb_instance.update(result[1])
            reset_instance.update(result[2])
            fix_instance = dict(sorted(fix_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            rb_instance = dict(sorted(rb_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            reset_instance = dict(sorted(reset_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
        for index,key in enumerate(fix_instance.keys()):
            # fixinstanse.append(("{}".format(index+1),"{}".format(key),"off"))
            fixinstanse.append(("{}_{}".format(fix_instance[key].config['dep'],fix_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(rb_instance.keys()):
            # rbinstance.append(("{}".format(index+1),"{}".format(key),"off"))
            rbinstance.append(("{}_{}".format(rb_instance[key].config['dep'],rb_instance[key].config['id']),"{}".format(key),"off"))
        for index,key in enumerate(reset_instance.keys()):
            # resetinstance.append(("{}".format(index+1),"{}".format(key),"off"))
            # 这里应该向列表 `resetinstance` 添加项，之前误用 `reset_instance.append` 会导致 AttributeError
            resetinstance.append(("{}_{}".format(reset_instance[key].config['dep'],reset_instance[key].config['id']),"{}".format(key),"off"))
        return [(fixinstanse,fix_instance),(rbinstance,rb_instance),(resetinstance,reset_instance)]
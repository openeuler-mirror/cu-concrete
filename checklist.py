from whiptail import Whiptail
import time
import subprocess
import os
from mappingdes import load_check_class, load_sec_class, load_departments, load_departments_no_ui
import re
import logging
TITLE = '安全加固工具'
HEIGHT = 25
WIDTH = 60

class checklist:

    def get_folder(self, i):
        folder_str = 'department_{}_policy'.format(i)
        return folder_str

    def sub_checklist(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fixinstanse = []
        fix_instance = {}
        all_dir = [name for name in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, name))]
        rbinstance = []
        rb_instance = {}
        resetinstance = []
        reset_instance = {}
        import re
        pattern = re.compile('^department_\\d+_policy$')
        folder_list = [d for d in all_dir if pattern.match(d)]
        dept_ids = [int(d.split('_')[1]) for d in folder_list]
        if dept_ids:
            result = load_departments(dept_ids)
            fix_instance.update(result[0])
            rb_instance.update(result[1])
            reset_instance.update(result[2])
            fix_instance = dict(sorted(fix_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            rb_instance = dict(sorted(rb_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))
            reset_instance = dict(sorted(reset_instance.items(), key=lambda item: (item[1].config['dep'], item[1].config['id'])))

    def sec_checklist(self):
        pass

    def sub_checklist_noui(self):
        pass
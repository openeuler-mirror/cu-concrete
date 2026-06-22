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

    def sec_checklist(self):
        pass

    def sub_checklist_noui(self):
        pass
from whiptail import Whiptail
import os
import sys
from fixlist import fixlist
from checklist import checklist
from rollbacklist import rollbacklist
import json
import logging
import tempfile
from resetlist import resetlist
import time
TITLE = '安全加固工具'
HEIGHT = 25
WIDTH = 60
flag_path = 'flag.txt'

def main_menu():
    w = Whiptail(title=TITLE, backtitle='主菜单', height=HEIGHT, width=WIDTH)
    choice = w.menu('请选择操作：', [('1', '加固'), ('2', '还原'), ('3', '修复'), ('4', '日志'), ('5', '退出')])
    return choice[0]

def text_box():
    w = Whiptail(title=TITLE, backtitle='日志', height=HEIGHT, width=WIDTH)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    log_path = os.path.join(project_root, 'logs', 'app.log')
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write('日志文件为空\n')
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.log') as tmpfile:
        with open(log_path, 'r', encoding='utf-8') as f:
            tmpfile.write(f.read())
        tmpfile_name = tmpfile.name
    try:
        success = w.textbox(tmpfile_name)
    except Exception as e:
        logging.error(f'显示日志失败: {e}')
    finally:
        if os.path.exists(tmpfile_name):
            os.unlink(tmpfile_name)

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(project_root, flag_path)
    flag = None
    c = checklist()
    while True:
        if not os.path.exists(log_path):
            with open(log_path, 'w', encoding='utf-8') as f:
                content = f.write('1')
                flag = 1
        else:
            with open(log_path, 'r', encoding='utf-8') as f:
                flag = int(f.read().strip())
        if flag == 1:
            InstanceTuple = c.sub_checklist()
            flag += 1
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(str(flag))
        else:
            InstanceTuple = c.sec_checklist()
        choice = main_menu()
        if choice == '1':
            f = fixlist()
            f.sub_fixlist('加固项', '加固项', InstanceTuple[0])
        elif choice in ['2', '3']:
            if choice == '2':
                r = rollbacklist()
                r.sub_rollbacklist('还原项', '还原项', InstanceTuple[1])
            elif choice == '3':
                r = resetlist()
                r.sub_resetlist('修复项', '修复项', InstanceTuple[2])
        elif choice == '4':
            text_box()
        elif choice == '5':
            break

def setup_logging(log_dir='logs', log_file='app.log', level=logging.INFO):
    """全局日志配置：基于当前文件位置，确保日志在项目根目录"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    full_log_dir = os.path.join(project_root, log_dir)
    os.makedirs(full_log_dir, exist_ok=True)
if __name__ == '__main__':
    setup_logging(level=logging.DEBUG)
    main()
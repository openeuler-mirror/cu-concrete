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

def main():
    pass

def setup_logging(log_dir='logs', log_file='app.log', level=logging.INFO):
    """全局日志配置：基于当前文件位置，确保日志在项目根目录"""
    pass
if __name__ == '__main__':
    setup_logging(level=logging.DEBUG)
    main()
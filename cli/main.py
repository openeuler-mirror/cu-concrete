"""
cu-concrete CLI 工具
提供命令行接口用于加固、还原、修复系统，并记录相应日志
"""
import argparse
import sys
import os
import logging
from datetime import datetime
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from cli.harden import Hardener
from cli.restore import Restorer
from cli.repair import Repairer
from cli.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(description='cu-concrete 安全加固工具命令行接口')
    parser.add_argument('-v', '--verbose', action='store_true', help='启用详细输出')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    harden_parser = subparsers.add_parser('harden', help='执行安全加固')
    harden_parser.add_argument('--all', action='store_true', help='执行所有加固项')
    harden_parser.add_argument('--list', action='store_true', help='列出可加固项')
    harden_parser.add_argument('items', nargs='*', help='指定要加固的项ID')
    restore_parser = subparsers.add_parser('restore', help='还原已加固项')
    restore_parser.add_argument('--all', action='store_true', help='还原所有已加固项')
    restore_parser.add_argument('--list', action='store_true', help='列出可还原项')
if __name__ == '__main__':
    main()
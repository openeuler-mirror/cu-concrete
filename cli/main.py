#!/usr/bin/env python3
"""
cu-concrete CLI 工具
提供命令行接口用于加固、还原、修复系统，并记录相应日志
"""

import argparse
import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
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
    
    # 加固命令
    harden_parser = subparsers.add_parser('harden', help='执行安全加固')
    harden_parser.add_argument('--all', action='store_true', help='执行所有加固项')
    harden_parser.add_argument('--list', action='store_true', help='列出可加固项')
    harden_parser.add_argument('items', nargs='*', help='指定要加固的项ID')
    
    # 还原命令
    restore_parser = subparsers.add_parser('restore', help='还原已加固项')
    restore_parser.add_argument('--all', action='store_true', help='还原所有已加固项')
    restore_parser.add_argument('--list', action='store_true', help='列出可还原项')
    restore_parser.add_argument('items', nargs='*', help='指定要还原的项ID')
    
    # 修复命令
    repair_parser = subparsers.add_parser('repair', help='执行系统修复')
    repair_parser.add_argument('--all', action='store_true', help='执行所有修复项')
    repair_parser.add_argument('--list', action='store_true', help='列出可修复项')
    repair_parser.add_argument('items', nargs='*', help='指定要修复的项ID')
    
    # # 日志命令
    # log_parser = subparsers.add_parser('log', help='查看操作日志')
    # log_parser.add_argument('--clear', action='store_true', help='清空日志')
    # log_parser.add_argument('--export', type=str, help='导出日志到指定文件')
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger(log_level)
    
    if args.command == 'harden':
        hardener = Hardener(logger)
        if args.list:
            hardener.list_items()
        elif args.all:
            hardener.harden_all()
        elif args.items:
            hardener.harden_items(args.items)
        else:
            hardener.list_items()
            
    elif args.command == 'restore':
        restorer = Restorer(logger)
        if args.list:
            restorer.list_items()
        elif args.all:
            restorer.restore_all()
        elif args.items:
            restorer.restore_items(args.items)
        else:
            restorer.list_items()
            
    elif args.command == 'repair':
        repairer = Repairer(logger)
        if args.list:
            repairer.list_items()
        elif args.all:
            repairer.repair_all()
        elif args.items:
            repairer.repair_items(args.items)
        else:
            repairer.list_items()
            
    # elif args.command == 'log':
    #     # 处理日志相关操作
    #     log_file = os.path.join(project_root, 'logs', 'cu_concrete.log')
    #     if args.clear:
    #         if os.path.exists(log_file):
    #             open(log_file, 'w').close()
    #             print("日志已清空")
    #         else:
    #             print("日志文件不存在")
    #     elif args.export:
    #         if os.path.exists(log_file):
    #             try:
    #                 with open(log_file, 'r') as src, open(args.export, 'w') as dst:
    #                     dst.write(src.read())
    #                 print(f"日志已导出到 {args.export}")
    #             except Exception as e:
    #                 print(f"导出日志失败: {e}")
    #         else:
    #             print("日志文件不存在")
    #     else:
    #         if os.path.exists(log_file):
    #             with open(log_file, 'r') as f:
    #                 print(f.read())
    #         else:
    #             print("暂无日志")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
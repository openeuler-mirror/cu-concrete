#!/usr/bin/env python3
"""
cu-concrete 主入口文件

使用方法:
    图形界面: python main.py
    命令行界面: python main.py [命令] [参数...]

示例:
    python main.py --help          # 显示帮助信息
    python main.py generate doc    # 生成文档
    python main.py build project   # 构建项目
"""

import sys
import subprocess
import os

def main():
    if len(sys.argv) > 1:
        # 如果提供了命令行参数，则运行CLI接口
        cli_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cli', 'main.py')
        cli_args = [sys.executable, cli_path] + sys.argv[1:]
        os.execv(sys.executable, cli_args)
    else:
        # 否则运行图形界面
        path = os.path.dirname(os.path.realpath(__file__))
        path_join = os.path.join(path, 'start_interface.sh')
        subprocess.run(path_join)

if __name__ == '__main__':
    main()
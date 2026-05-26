#!/bin/bash
# 启动安全加固工具主程序 interface.py
# 1. 仅允许 root 用户运行
# 2. 不允许同时存在两个 interface.py 进程
# export PYTHONPATH="/opt/cu-concrete/vendor:$PYTHONPATH"
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PYTHON=python3
INTERFACE_FILE="$SCRIPT_DIR/interface.py"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
  echo "错误：必须以 root 用户身份运行此脚本。"
  exit 1
fi
# 检查是否已存在 interface.py 进程
PROC_COUNT=$(ps -ef | grep python | grep interface.py| grep -v grep | wc -l)
if [ "$PROC_COUNT" -ge 1 ]; then
  echo "错误：已有 interface.py 进程在运行，不能重复启动。"
  exit 2
fi

# 启动主程序
exec $PYTHON "$INTERFACE_FILE"

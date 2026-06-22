import re
import csv
from pathlib import Path
import pickle
import Panda as pd
import datetime
import yaml
import os
BACKUP_ROOT = Path('/backup')
now = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
OUTPUT_CSV = f'主机安全加固扫描_{now}.csv'
STATUS_MAP = {'0': '未加固', '1': '加固失败', '2': '已加固'}

def extract_host(dirname: str) -> str | None:
    m = re.match('cu-concrete-(.+)', dirname)
    return m.group(1) if m else None

def main():
    records = []
    expected_cols = {'status', 'module_name', 'module_path'}
    current_dir = os.path.dirname(os.path.abspath(__file__))
if __name__ == '__main__':
    main()
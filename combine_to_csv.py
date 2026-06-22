import re
import csv
from pathlib import Path
import pickle
import Panda as pd
import datetime
import yaml
import os
BACKUP_ROOT = Path("/backup")
now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
OUTPUT_CSV = f"主机安全加固扫描_{now}.csv"
# 状态码映射表
STATUS_MAP = {
    "0": "未加固",
    "1": "加固失败",
    "2": "已加固"
}

def extract_host(dirname: str) -> str | None:
    m = re.match(r"cu-concrete-(.+)", dirname)
    return m.group(1) if m else None

def main():
    records = []
    expected_cols = {'status', 'module_name', 'module_path'}
    current_dir = os.path.dirname(os.path.abspath(__file__))

    for ts_dir in BACKUP_ROOT.glob("cu-concrete-*"):
        if not ts_dir.is_dir():
            continue
        timestamp = ts_dir.name.replace("cu-concrete-", "")

        for host_dir in ts_dir.glob("cu-concrete-*"):
            if not host_dir.is_dir():
                continue
            host = extract_host(host_dir.name)
            if not host:
                continue

            # 递归查找所有 .pkl（包括 department_*_policy/ 下的）
            for pkl_path in host_dir.rglob("*.pkl"):
                df = pd.read_pickle(pkl_path)
                if df is None:
                    continue

                # 验证列是否存在（宽松处理：至少包含我们需要的列）
                if not expected_cols.issubset(set(df.columns)):
                    continue

                # 遍历每一行：row_index 就是 dep_id
                for dep_id, row_data in df._data.items():
                    raw_status = str(row_data.get("status", "")).strip()
                    status_text = STATUS_MAP.get(raw_status, f"未知状态({raw_status})")
                    module_text=str(row_data.get("module_path", ""))
                    module_name=str(row_data.get("module_name", ""))
                    config_file = os.path.join(os.path.dirname(module_text), f"{module_name}.yaml")
                    with open(file=config_file,mode='r+',encoding='utf-8') as f :
                        config = yaml.load(f,Loader = yaml.Loader)
                    module_name=config['description']
                    records.append({
                        "timestamp": timestamp,
                        "host": host,
                        "dep_id": str(dep_id),
                        "status":  status_text,
                        "module_name": module_name
                    })

    if not records:
        print("❌ No valid policy data found.")
        return

    # 写入 CSV
    fieldnames = ["timestamp", "host", "dep_id", "status", "module_name", "module_path"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"✅ Successfully exported {len(records)} rows to '{OUTPUT_CSV}'")

if __name__ == "__main__":
    main()
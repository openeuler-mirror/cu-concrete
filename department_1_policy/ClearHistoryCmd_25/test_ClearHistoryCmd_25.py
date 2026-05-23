import os
import pytest
import pandas as pd
from ClearHistoryCmd_25 import ClearHistoryCmd_25
yaml_path = os.path.join(os.path.dirname(__file__), 'ClearHistoryCmd_25.yaml')
pkl_path = '/tmp/test_data_status.pkl'
bash_history_path = '/tmp/test_bash_history'
bash_history_bak_path = '/tmp/test_bash_history_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/ClearHistoryCmd_25.yaml')
    with open(bash_history_path, 'w') as f:
        f.write('ls\ncd /\ncat /etc/passwd\n')
    with open(bash_history_bak_path, 'w') as f:
        f.write('ls\ncd /\ncat /etc/passwd\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/ClearHistoryCmd_25.yaml', bash_history_path, bash_history_bak_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = ClearHistoryCmd_25()
    obj.config_file = '/tmp/ClearHistoryCmd_25.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 25, 'query': {'path': bash_history_path, 'path1': bash_history_bak_path}, 'description': '删除历史命令行记录'}
    obj.status_form = pd.read_pickle(pkl_path)

def test_init():
    pass

def test_finalfix():
    pass

def test_fix():
    pass

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
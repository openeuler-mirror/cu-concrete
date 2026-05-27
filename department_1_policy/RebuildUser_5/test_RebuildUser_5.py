import os
import pandas as pd
import pytest
from RebuildUser_5 import RebuildUser_5
yaml_path = os.path.join(os.path.dirname(__file__), 'RebuildUser_5.yaml')
pkl_path = '/tmp/test_data_status.pkl'
login_defs_path = '/tmp/test_login.defs'
backup_path = '/tmp/test_login.defs.bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/RebuildUser_5.yaml')
    with open(login_defs_path, 'w') as f:
        f.write('PASS_MAX_DAYS    99999\nPASS_MIN_LEN     5\nPASS_MIN_DAYS    0\nPASS_WARN_AGE    7\n')
    with open(backup_path, 'w') as f:
        f.write('PASS_MAX_DAYS    99999\nPASS_MIN_LEN     5\nPASS_MIN_DAYS    0\nPASS_WARN_AGE    7\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/RebuildUser_5.yaml', login_defs_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = RebuildUser_5()
    obj.config_file = '/tmp/RebuildUser_5.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 5, 'query': {'form': ['^[[:space:]]*PASS_MAX_DAYS', '^[[:space:]]*PASS_MIN_LEN', '^[[:space:]]*PASS_MIN_DAYS', '^[[:space:]]*PASS_WARN_AGE'], 'path': login_defs_path}, 'change': {'value': ['PASS_MAX_DAYS    90', 'PASS_MIN_LEN     8', 'PASS_MIN_DAYS    1', 'PASS_WARN_AGE    7']}, 'recovery': {'value': ['PASS_MAX_DAYS    99999', 'PASS_MIN_LEN     5', 'PASS_MIN_DAYS    0', 'PASS_WARN_AGE    7']}, 'description': '用户密码长度和有效期相关设定', 'backup_path': backup_path}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 5
    assert isinstance(obj.status_form, pd.DataFrame)

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
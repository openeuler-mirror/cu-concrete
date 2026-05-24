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

def build_instance():
    pass

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
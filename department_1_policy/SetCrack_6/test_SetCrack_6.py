import os
import pytest
import pandas as pd
from SetCrack_6 import SetCrack_6
yaml_path = os.path.join(os.path.dirname(__file__), 'SetCrack_6.yaml')
pkl_path = '/tmp/test_data_status.pkl'
system_auth_path = '/tmp/test_system-auth'
backup_path = '/tmp/test_system-auth_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/SetCrack_6.yaml')
    with open(system_auth_path, 'w') as f:
        f.write('auth        required      pam_env.so\nauth        sufficient    pam_unix.so\npassword    requisite     pam_pwquality.so\n')
    with open(backup_path, 'w') as f:
        f.write('auth        required      pam_env.so\nauth        sufficient    pam_unix.so\npassword    requisite     pam_pwquality.so\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/SetCrack_6.yaml', system_auth_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = SetCrack_6()
    obj.config_file = '/tmp/SetCrack_6.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 6, 'query': {'form': '^password    requisite     pam_pwquality.so', 'path': system_auth_path}, 'change': {'value': 'password    requisite     pam_pwquality.so difok=3 dcredit=-1 lcredit=-1 ucredit=-1 ocredit=-1'}, 'description': '修改密码相关限制', 'backup_path': backup_path}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 6
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['16', 'status'] == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['16', 'status'] == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)
    assert result is True

def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['16', 'status'] == 0

def test_reset():
    pass

def test_get_des():
    pass
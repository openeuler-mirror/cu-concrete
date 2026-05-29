import os
import pytest
import pandas as pd
from LoginUserLock_7 import LoginUserLock_7
yaml_path = os.path.join(os.path.dirname(__file__), 'LoginUserLock_7.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sshd_path = '/tmp/test_sshd'
backup_path = '/tmp/test_sshd_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/LoginUserLock_7.yaml')
    with open(sshd_path, 'w') as f:
        f.write('auth        required      pam_env.so\nauth        sufficient    pam_unix.so\n')
    with open(backup_path, 'w') as f:
        f.write('auth        required      pam_env.so\nauth        sufficient    pam_unix.so\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/LoginUserLock_7.yaml', sshd_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = LoginUserLock_7()
    obj.config_file = '/tmp/LoginUserLock_7.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 7, 'query': {'form': 'auth        required      pam_faillock.so preauth audit deny=3  unlock_time=180 even_deny_root root_unlock_time=300', 'path': sshd_path}, 'change': {'value': 'auth        required      pam_faillock.so preauth audit deny=3  unlock_time=180 even_deny_root root_unlock_time=300'}, 'recovery': {'value': 'auth        required      pam_faillock.so preauth audit deny=6  unlock_time=180 even_deny_root root_unlock_time=300'}, 'description': '密码输入错误锁定账户的设定', 'backup_path': backup_path}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 7
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['17', 'status'] == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['17', 'status'] == 2

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
    assert status_df.loc['17', 'status'] == 0

def test_reset():
    pass

def test_get_des():
    pass
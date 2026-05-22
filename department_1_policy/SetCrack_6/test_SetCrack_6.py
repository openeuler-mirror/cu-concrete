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
import os
import pytest
import pandas as pd
from ReUserShell_24 import ReUserShell_24
yaml_path = os.path.join(os.path.dirname(__file__), 'ReUserShell_24.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd_shell'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/ReUserShell_24.yaml')
    if os.path.exists('/etc/passwd'):
        os.system(f'cp /etc/passwd {passwd_path}')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/ReUserShell_24.yaml', passwd_path]:
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
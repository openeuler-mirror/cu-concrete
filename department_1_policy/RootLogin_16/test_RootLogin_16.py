import os
import pytest
import pandas as pd
from RootLogin_16 import RootLogin_16
yaml_path = os.path.join(os.path.dirname(__file__), 'RootLogin_16.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sshd_config_path = '/tmp/test_sshd_config'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/RootLogin_16.yaml')
    with open(sshd_config_path, 'w') as f:
        f.write('PermitRootLogin yes\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/RootLogin_16.yaml', sshd_config_path]:
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
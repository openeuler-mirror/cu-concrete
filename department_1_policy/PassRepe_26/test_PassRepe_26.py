import os
import pytest
import pandas as pd
from PassRepe_26 import PassRepe_26
yaml_path = os.path.join(os.path.dirname(__file__), 'PassRepe_26.yaml')
pkl_path = '/tmp/test_data_status.pkl'
system_auth_path = '/tmp/test_system_auth_passrepe'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/PassRepe_26.yaml')
    with open(system_auth_path, 'w') as f:
        f.write('password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/PassRepe_26.yaml', system_auth_path]:
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
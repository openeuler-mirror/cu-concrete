import os
import pytest
import pandas as pd
from LoginTmout_10 import LoginTmout_10
yaml_path = os.path.join(os.path.dirname(__file__), 'LoginTmout_10.yaml')
pkl_path = '/tmp/test_data_status.pkl'
profile_path = '/tmp/test_profile_tmout'
backup_path = '/tmp/test_profile_tmout_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/LoginTmout_10.yaml')
    with open(profile_path, 'w') as f:
        f.write('export PATH\n')
    with open(backup_path, 'w') as f:
        f.write('export PATH\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/LoginTmout_10.yaml', profile_path, backup_path]:
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
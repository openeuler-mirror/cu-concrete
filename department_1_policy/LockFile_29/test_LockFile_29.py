import os
import pytest
import pandas as pd
from LockFile_29 import LockFile_29
yaml_path = os.path.join(os.path.dirname(__file__), 'LockFile_29.yaml')
pkl_path = '/tmp/test_data_status.pkl'
file_paths = ['/tmp/test_passwd', '/tmp/test_shadow', '/tmp/test_group']

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/LockFile_29.yaml')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    for fp in file_paths:
        with open(fp, 'w') as f:
            f.write('test')
    yield
    for fp in file_paths:
        if os.path.exists(fp):
            os.system(f'chattr -i {fp}')
            os.remove(fp)
    for fp in [pkl_path, '/tmp/LockFile_29.yaml']:
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
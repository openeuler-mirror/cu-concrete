import os
import pandas as pd
import pytest
from LockingInvalidAccount_2 import LockingInvalidAccount_2
yaml_path = os.path.join(os.path.dirname(__file__), 'LockingInvalidAccount_2.yaml')
pkl_path = '/tmp/test_data_status.pkl'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/LockingInvalidAccount_2.yaml')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/LockingInvalidAccount_2.yaml']:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = LockingInvalidAccount_2()
    obj.config_file = '/tmp/LockingInvalidAccount_2.yaml'
    obj.pkl_file = pkl_path

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
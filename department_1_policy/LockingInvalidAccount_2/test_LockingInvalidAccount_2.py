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
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 2, 'query': {'value': ['liukun']}, 'change': {}, 'description': '锁定无效账号'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 2
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['12', 'status'] == 2 or status_df.loc['12', 'status'] == '2'

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['12', 'status'] == 2 or status_df.loc['12', 'status'] == '2'

def test_check():
    obj = build_instance()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)

def test_reset():
    pass

def test_get_des():
    pass
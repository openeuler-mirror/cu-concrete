import os
import pandas as pd
import pytest
from UserFilePermission_3 import UserFilePermission_3
yaml_path = os.path.join(os.path.dirname(__file__), 'UserFilePermission_3.yaml')
pkl_path = '/tmp/test_data_status.pkl'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/UserFilePermission_3.yaml')
    with open('/tmp/test_file', 'w') as f:
        f.write('testuser:somecontent\notheruser:othercontent\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/UserFilePermission_3.yaml', '/tmp/test_file']:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = UserFilePermission_3()
    obj.config_file = '/tmp/UserFilePermission_3.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 3, 'query': {'path': '/tmp/test_file', 'form': 'testuser'}, 'change': {'value': 644}, 'description': '用户文件权限检查'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 3
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['13', 'status'] == 2 or status_df.loc['13', 'status'] == '2'

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['13', 'status'] == 2 or status_df.loc['13', 'status'] == '1'

def test_check():
    obj = build_instance()
    result = obj.check()

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
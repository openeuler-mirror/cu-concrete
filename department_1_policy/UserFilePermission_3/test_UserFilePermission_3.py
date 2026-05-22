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
import os
import pytest
import pandas as pd
from CheckRootDir_9 import CheckRootDir_9
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckRootDir_9.yaml')
pkl_path = '/tmp/test_data_status.pkl'
root_path = '/tmp/test_rootdir'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckRootDir_9.yaml')
    if not os.path.exists(root_path):
        os.mkdir(root_path)
    os.chmod(root_path, 360)
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckRootDir_9.yaml']:
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
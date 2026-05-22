import os
import pytest
import pandas as pd
from ShutCAD_28 import ShutCAD_28
yaml_path = os.path.join(os.path.dirname(__file__), 'ShutCAD_28.yaml')
pkl_path = '/tmp/test_data_status.pkl'
service_name = 'ctrl-alt-del.target'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/ShutCAD_28.yaml')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/ShutCAD_28.yaml']:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = ShutCAD_28()

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
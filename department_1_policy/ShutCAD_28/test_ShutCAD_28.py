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
    obj.config_file = '/tmp/ShutCAD_28.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 28, 'query': {'path': service_name}, 'change': {'value': ['mask', 'unmask']}, 'description': '关闭ctrl+alt+del重启功能'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 28
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['128', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['128', 'status']

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
import os
import pytest
import pandas as pd
from HistSize_23 import HistSize_23
yaml_path = os.path.join(os.path.dirname(__file__), 'HistSize_23.yaml')
pkl_path = '/tmp/test_data_status.pkl'
profile_path = '/tmp/test_profile_hist'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/HistSize_23.yaml')
    with open(profile_path, 'w') as f:
        f.write('export PATH\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/HistSize_23.yaml', profile_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = HistSize_23()
    obj.config_file = '/tmp/HistSize_23.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 23, 'query': {'path': profile_path, 'form': '^export HISTSIZE='}, 'change': {'value': 'export HISTSIZE=10'}, 'description': '控制当前bash会话中保留的命令'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

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
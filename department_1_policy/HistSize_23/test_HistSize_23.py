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
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 23
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['123', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['123', 'status']
    assert val == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()

def test_reset():
    pass

def test_get_des():
    pass
import os
import pytest
import pandas as pd
from Resetlsrm_27 import Resetlsrm_27
yaml_path = os.path.join(os.path.dirname(__file__), 'Resetlsrm_27.yaml')
pkl_path = '/tmp/test_data_status.pkl'
bashrc_path = '/tmp/test_bashrc_resetlsrm'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/Resetlsrm_27.yaml')
    with open(bashrc_path, 'w') as f:
        f.write('# .bashrc\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/Resetlsrm_27.yaml', bashrc_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = Resetlsrm_27()
    obj.config_file = '/tmp/Resetlsrm_27.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 27, 'query': {'path': bashrc_path}, 'change': {'value': ["alias ls='ls -alh'", "alias rm='rm -i'"]}, 'description': '修改ls、rm的显示信息'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 27
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['127', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['127', 'status']
    assert val == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['127', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()

def test_get_des():
    pass
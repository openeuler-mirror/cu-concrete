import os
import pytest
import pandas as pd
from LoginTmout_10 import LoginTmout_10
yaml_path = os.path.join(os.path.dirname(__file__), 'LoginTmout_10.yaml')
pkl_path = '/tmp/test_data_status.pkl'
profile_path = '/tmp/test_profile_tmout'
backup_path = '/tmp/test_profile_tmout_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/LoginTmout_10.yaml')
    with open(profile_path, 'w') as f:
        f.write('export PATH\n')
    with open(backup_path, 'w') as f:
        f.write('export PATH\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/LoginTmout_10.yaml', profile_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = LoginTmout_10()
    obj.config_file = '/tmp/LoginTmout_10.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 10, 'change': {'form1': '^TMOUT', 'form2': '^export TMOUT', 'path': profile_path}, 'add': {'form': 'export TMOUT=300'}, 'description': '用户会话无操作时长中断设定', 'backup_path': backup_path}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 10
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['110', 'status'] == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['110', 'status'] == 2

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
    assert status_df.loc['110', 'status'] == 0

def test_reset():
    pass

def test_get_des():
    pass
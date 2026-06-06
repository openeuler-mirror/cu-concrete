import os
import pytest
import pandas as pd
from RootLogin_16 import RootLogin_16
yaml_path = os.path.join(os.path.dirname(__file__), 'RootLogin_16.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sshd_config_path = '/tmp/test_sshd_config'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/RootLogin_16.yaml')
    with open(sshd_config_path, 'w') as f:
        f.write('PermitRootLogin yes\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/RootLogin_16.yaml', sshd_config_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = RootLogin_16()
    obj.config_file = '/tmp/RootLogin_16.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 16, 'query': {'form': '^PermitRootLogin', 'path': sshd_config_path}, 'change': {'value': ['PermitRootLogin no', 'systemctl restart sshd', 'PermitRootLogin yes']}, 'description': '禁止root账户ssh登录'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 16
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['116', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['116', 'status']
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
    val = status_df.loc['116', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['116', 'status']
    assert val == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == '禁止root账户ssh登录'
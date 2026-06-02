import os
import pytest
import pandas as pd
from SSHRoot_22 import SSHRoot_22
yaml_path = os.path.join(os.path.dirname(__file__), 'SSHRoot_22.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sshd_config_path = '/tmp/test_sshd_config'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/SSHRoot_22.yaml')
    with open(sshd_config_path, 'w') as f:
        f.write('Port 22\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/SSHRoot_22.yaml', sshd_config_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = SSHRoot_22()
    obj.config_file = '/tmp/SSHRoot_22.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 22, 'query': {'path': [sshd_config_path], 'form': ['^[[:space:]]*(#)?[[:space:]]*Port', '^SELINUX=']}, 'change': {'set': ['sudo firewall-cmd --zone=public --add-port=1234/tcp --permanent', 'sudo firewall-cmd --reload', 'sudo firewall-cmd --zone=public --add-port=22/tcp --permanent'], 'value': ['Port 1234', 'Port 22']}, 'description': '修改ssh登录端口'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 22
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['122', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['122', 'status']
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
    val = status_df.loc['122', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()

def test_get_des():
    pass
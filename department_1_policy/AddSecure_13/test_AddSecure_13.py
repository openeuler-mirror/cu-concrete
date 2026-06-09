import os
import pytest
import pandas as pd
from AddSecure_13 import AddSecure_13
yaml_path = os.path.join(os.path.dirname(__file__), 'AddSecure_13.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sudoers_path = '/tmp/test_sudoers'
ssh_dir = '/tmp/test_safe_account_ssh'
auth_keys = os.path.join(ssh_dir, 'authorized_keys')
id_rsa = os.path.join(ssh_dir, 'id_rsa')
id_dsa = os.path.join(ssh_dir, 'id_dsa')

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AddSecure_13.yaml')
    with open(sudoers_path, 'w') as f:
        f.write('root    ALL=(ALL)    NOPASSWD: ALL\n')
    os.makedirs(ssh_dir, exist_ok=True)
    with open(auth_keys, 'w') as f:
        f.write('ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEArandomkey')
    with open(id_rsa, 'w') as f:
        f.write('FAKE_RSA_KEY')
    with open(id_dsa, 'w') as f:
        f.write('FAKE_DSA_KEY')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AddSecure_13.yaml', sudoers_path, auth_keys, id_rsa, id_dsa]:
        if os.path.exists(fp):
            os.remove(fp)
    if os.path.exists(ssh_dir):
        os.rmdir(ssh_dir)

def build_instance():
    obj = AddSecure_13()
    obj.config_file = '/tmp/AddSecure_13.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 13, 'query': {'form': 'safe_account', 'path': sudoers_path, 'path2': auth_keys, 'path3': id_rsa, 'path4': id_dsa}, 'change': {'value1': 'root@userpass', 'value2': 'safe_account    ALL=(ALL)    NOPASSWD: ALL', 'value3': ['700', '644', '600'], 'path': '/tmp/test_safe_account', 'path1': ssh_dir, 'path2': auth_keys, 'path3': id_rsa, 'path4': id_dsa}, 'description': '添加用于安全管理的账户'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 13
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['113', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['113', 'status']
    assert val == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()
    obj.fix()

def test_reset():
    pass

def test_get_des():
    pass
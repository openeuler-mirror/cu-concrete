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
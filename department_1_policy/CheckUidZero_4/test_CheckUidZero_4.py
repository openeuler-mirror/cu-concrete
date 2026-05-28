import os
import pandas as pd
import pytest
from CheckUidZero_4 import CheckUidZero_4
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import re
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckUidZero_4.yaml')
pkl_path = '/tmp/test_data_status.pkl'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckUidZero_4.yaml')
    with open('/tmp/test_passwd', 'w') as f:
        f.write('root:x:0:0:root:/root:/bin/bash\nuser1:x:1000:1000:user1:/home/user1:/bin/bash\n')
    with open('/tmp/test_passwd_bak', 'w') as f:
        f.write('root:x:0:0:root:/root:/bin/bash\nuser1:x:1000:1000:user1:/home/user1:/bin/bash\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckUidZero_4.yaml', '/tmp/test_passwd', '/tmp/test_passwd_bak']:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = CheckUidZero_4()
    obj.config_file = '/tmp/CheckUidZero_4.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 4, 'query': [{'path': '/tmp/test_passwd', 'form': '{ print $1 }'}], 'backup_path': '/tmp/test_passwd_bak', 'description': 'UID为0的账户检查'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 4
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['14', 'status'] == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['14', 'status'] == 2

def test_check():
    obj = build_instance()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()

def test_reset():
    pass

def test_get_des():
    pass
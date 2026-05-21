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

def build_instance():
    pass

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
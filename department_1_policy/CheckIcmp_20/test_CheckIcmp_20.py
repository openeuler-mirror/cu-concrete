import os
import pytest
import pandas as pd
from CheckIcmp_20 import CheckIcmp_20
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckIcmp_20.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sysctl_conf_path = '/tmp/test_sysctl.conf'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckIcmp_20.yaml')
    with open(sysctl_conf_path, 'w') as f:
        f.write('net.ipv4.icmp_echo_ignore_all = 0\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckIcmp_20.yaml', sysctl_conf_path]:
        if os.path.exists(fp):
            os.remove(fp)

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
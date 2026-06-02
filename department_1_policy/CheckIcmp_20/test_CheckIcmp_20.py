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
    obj = CheckIcmp_20()
    obj.config_file = '/tmp/CheckIcmp_20.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 20, 'query': {'form': '^net.ipv4.icmp_echo_ignore_all', 'path': sysctl_conf_path}, 'change': {'value': ['net.ipv4.icmp_echo_ignore_all = 1', 'net.ipv4.icmp_echo_ignore_all = 0']}, 'description': '禁止响应ping,避免被扫描发现'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 20
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['120', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['120', 'status']
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
    val = status_df.loc['120', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()

def test_get_des():
    pass
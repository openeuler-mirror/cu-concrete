import os
import pytest
import pandas as pd
from Telent_15 import Telent_15
yaml_path = os.path.join(os.path.dirname(__file__), 'Telent_15.yaml')
pkl_path = '/tmp/test_data_status.pkl'
telnet_conf_path = '/tmp/test_telnet_conf'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/Telent_15.yaml')
    with open(telnet_conf_path, 'w') as f:
        f.write('disable = yes\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/Telent_15.yaml', telnet_conf_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = Telent_15()
    obj.config_file = '/tmp/Telent_15.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 15, 'query': {'form': '^disable', 'path': telnet_conf_path}, 'change': {'value': ['disable = yes', 'openssh*', 'systemctl disable  telnet.socket', 'systemctl stop telnet.socket', 'systemctl enable telnet.socket', 'systemctl start telnet.socket']}, 'description': '关闭telent,使用openssh'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

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
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
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 15
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['115', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['115', 'status']
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
    val = status_df.loc['115', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['115', 'status']
    assert val == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == '关闭telent,使用openssh'
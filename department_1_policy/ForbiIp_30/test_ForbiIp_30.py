import os
import pytest
import pandas as pd
from ForbiIp_30 import ForbiIp_30
yaml_path = os.path.join(os.path.dirname(__file__), 'ForbiIp_30.yaml')
pkl_path = '/tmp/test_data_status.pkl'
conf_path = '/tmp/test_sysctl.conf'
conf_bak_path = '/tmp/test_sysctl.conf_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/ForbiIp_30.yaml')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    with open(conf_path, 'w') as f:
        f.write('')
    with open(conf_bak_path, 'w') as f:
        f.write('')
    yield
    for fp in [pkl_path, '/tmp/ForbiIp_30.yaml', conf_path, conf_bak_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = ForbiIp_30()
    obj.config_file = '/tmp/ForbiIp_30.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 30, 'query': {'path': [conf_path, conf_bak_path]}, 'change': {'set': 'net.ipv4.ip_forward', 'value': 'net.ipv4.ip_forward=0'}, 'description': '禁止ip路由转发'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 30
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['130', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['130', 'status']
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
    val = status_df.loc['130', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()

def test_get_des():
    pass
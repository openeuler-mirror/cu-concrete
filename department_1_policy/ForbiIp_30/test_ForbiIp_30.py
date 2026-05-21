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
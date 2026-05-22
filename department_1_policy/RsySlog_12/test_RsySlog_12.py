import os
import pytest
import pandas as pd
from RsySlog_12 import RsySlog_12
pkl_path = '/tmp/test_data_status_12.pkl'
rsyslog_path = '/tmp/test_rsyslog_12.conf'
yaml_path = os.path.join(os.path.dirname(__file__), 'RsySlog_12.yaml')

@pytest.fixture(autouse=True)
def prepare_files():
    with open(rsyslog_path, 'w') as f:
        f.write('#rsyslog config\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, rsyslog_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = RsySlog_12()

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
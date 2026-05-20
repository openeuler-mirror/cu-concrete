import os
import pytest
import pandas as pd
from DeleteKeyword_17 import DeleteKeyword_17
yaml_path = os.path.join(os.path.dirname(__file__), 'DeleteKeyword_17.yaml')
pkl_path = '/tmp/test_data_status.pkl'
log_path = '/tmp/test_log_messages'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/DeleteKeyword_17.yaml')
    with open(log_path, 'w') as f:
        f.write('virtio\nkvm\nKVM\nCloud\ncloudw\notherlog\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/DeleteKeyword_17.yaml', log_path]:
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
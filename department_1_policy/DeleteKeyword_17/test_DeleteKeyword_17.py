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
    obj = DeleteKeyword_17()
    obj.config_file = '/tmp/DeleteKeyword_17.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 17, 'query': {'path': log_path}, 'change': {'value': ['virtio', 'kvm', 'KVM', 'Cloud', 'cloudw']}, 'description': '删除带有特定记录的log'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 17
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['117', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['117', 'status']

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
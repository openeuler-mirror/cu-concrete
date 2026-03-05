import os
import pytest
import pandas as pd
from CheckRootDir_9 import CheckRootDir_9

yaml_path = os.path.join(os.path.dirname(__file__), 'CheckRootDir_9.yaml')
pkl_path = '/tmp/test_data_status.pkl'
root_path = '/tmp/test_rootdir'

@pytest.fixture(autouse=True)
def prepare_files():
    # 复制 yaml
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckRootDir_9.yaml')
    # 构造 root 目录
    if not os.path.exists(root_path):
        os.mkdir(root_path)
    os.chmod(root_path, 0o550)
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckRootDir_9.yaml']:
        if os.path.exists(fp):
            os.remove(fp)
    if os.path.exists(root_path):
        os.rmdir(root_path)

def build_instance():
    obj = CheckRootDir_9()
    obj.config_file = '/tmp/CheckRootDir_9.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 9,
        'change': {
            'form': 'root:root',
            'path': root_path,
            'value': '700'
        },
        'recovery': {
            'value': '550'
        },
        'description': 'rootdir权限设定'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 9
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['19', 'status'] == 2 
def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['19', 'status'] == 2 

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
    assert status_df.loc['19', 'status'] == 0 

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['19', 'status'] == 2 

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == 'rootdir权限设定'

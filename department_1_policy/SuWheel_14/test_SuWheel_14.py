import os
import pytest
import pandas as pd
from SuWheel_14 import SuWheel_14

yaml_path = os.path.join(os.path.dirname(__file__), 'SuWheel_14.yaml')
pkl_path = '/tmp/test_data_status.pkl'
su_path = '/tmp/test_su'

@pytest.fixture(autouse=True)
def prepare_files():
    # 复制 yaml
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/SuWheel_14.yaml')
    # 构造 su 文件
    with open(su_path, 'w') as f:
        f.write('# su pam config\n')
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/SuWheel_14.yaml', su_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = SuWheel_14()
    obj.config_file = '/tmp/SuWheel_14.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 14,
        'query': {
            'form': [
                'auth            sufficient      pam_rootok.so',
                'auth            required        pam_wheel.so group=wheel'
            ],
            'path': su_path
        },
        'description': 'su权限的设定'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 14
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['114', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['114', 'status']
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
    val = status_df.loc['114', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['114', 'status']
    assert val == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == 'su权限的设定'

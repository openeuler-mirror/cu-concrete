import os
import pytest
import pandas as pd
from RebuildUmask_8 import RebuildUmask_8
yaml_path = os.path.join(os.path.dirname(__file__), 'RebuildUmask_8.yaml')
pkl_path = '/tmp/test_data_status.pkl'
profile_path = '/tmp/test_profile'
backup_path = '/tmp/test_profile_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/RebuildUmask_8.yaml')
    with open(profile_path, 'w') as f:
        f.write('export PATH\numask 022\n')
    with open(backup_path, 'w') as f:
        f.write('export PATH\numask 022\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/RebuildUmask_8.yaml', profile_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = RebuildUmask_8()
    obj.config_file = '/tmp/RebuildUmask_8.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 8, 'query': {'form': '^umask', 'path': profile_path}, 'change': {'value': 'umask 027'}, 'recovery': {'value': 'umask 022'}, 'description': 'umask设置用户文件权限', 'backup_path': backup_path}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 8
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['18', 'status'] == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['18', 'status'] == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)
    assert result is True

def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['18', 'status'] == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['18', 'status'] == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == 'umask设置用户文件权限'
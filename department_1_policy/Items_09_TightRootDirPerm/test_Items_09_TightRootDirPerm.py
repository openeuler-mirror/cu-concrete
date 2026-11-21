import os
import pytest
import pandas as pd
from Items_09_TightRootDirPerm import Items_09_TightRootDirPerm

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_09_TightRootDirPerm.yaml')
pkl_path = '/tmp/test_data_status.pkl'
root_path = '/tmp/test_root_dir'


@pytest.fixture(autouse=True)
def prepare_files():
    if not os.path.isdir(root_path):
        os.makedirs(root_path)
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)
    if os.path.isdir(root_path):
        os.rmdir(root_path)


def build_instance():
    obj = Items_09_TightRootDirPerm()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 9,
        'change': {'form': 'root:root', 'path': root_path, 'value': '700'},
        'recovery': {'value': '550'},
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
    assert pd.read_pickle(pkl_path).loc['19', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['19', 'status'] == 2
    assert os.stat(root_path).st_mode & 0o777 == 0o700


def test_check():
    obj = build_instance()
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['19', 'status'] == 0
    assert os.stat(root_path).st_mode & 0o777 == 0o550


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['19', 'status'] == 2
    assert os.stat(root_path).st_mode & 0o777 == 0o700


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == 'rootdir权限设定'

import os
import pytest
import pandas as pd
from Items_08_SetUmask import Items_08_SetUmask

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_08_SetUmask.yaml')
pkl_path = '/tmp/test_data_status.pkl'
profile_path = '/tmp/test_profile'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(profile_path, 'w') as f:
        f.write('# /etc/profile\n'
                'umask 022\n'
                'export PATH=/usr/bin:/bin\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [profile_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_08_SetUmask()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 8,
        'query': {'form': '^umask', 'path': profile_path},
        'change': {'value': 'umask 027'},
        'recovery': {'value': 'umask 022'},
        'description': 'umask设置用户文件权限'
    }
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
    assert pd.read_pickle(pkl_path).loc['18', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['18', 'status'] == 2
    content = open(profile_path).read()
    assert 'umask 027' in content
    assert 'umask 022' not in content


def test_check():
    obj = build_instance()
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['18', 'status'] == 0
    assert 'umask 022' in open(profile_path).read()


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['18', 'status'] == 2
    assert obj.check() is True


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == 'umask设置用户文件权限'

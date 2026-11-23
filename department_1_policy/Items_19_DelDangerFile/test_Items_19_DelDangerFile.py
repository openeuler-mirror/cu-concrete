import os
import pytest
import pandas as pd
from Items_19_DelDangerFile import Items_19_DelDangerFile

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_19_DelDangerFile.yaml')
pkl_path = '/tmp/test_data_status.pkl'
home_path = '/tmp/test_home'


@pytest.fixture(autouse=True)
def prepare_files():
    if not os.path.isdir(home_path):
        os.makedirs(home_path)
    for name in ('.netrc', '.rhosts'):
        with open(os.path.join(home_path, name), 'w') as f:
            f.write('dangerous content\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    if os.path.exists(pkl_path):
        os.remove(pkl_path)
    if os.path.isdir(home_path):
        for name in os.listdir(home_path):
            os.remove(os.path.join(home_path, name))
        os.rmdir(home_path)


def build_instance():
    obj = Items_19_DelDangerFile()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 19,
        'query': {'path': home_path, 'form': ['.netrc', '.rhosts']},
        'description': '删除.netrc,.rhosts的文件'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 19
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['119', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['119', 'status'] == 2
    # 危险文件被删除, 并留下 _bak 备份
    assert not os.path.exists(os.path.join(home_path, '.netrc'))
    assert os.path.exists(os.path.join(home_path, '.netrc_bak'))
    assert not os.path.exists(os.path.join(home_path, '.rhosts'))
    assert os.path.exists(os.path.join(home_path, '.rhosts_bak'))


def test_check():
    obj = build_instance()
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    # 还原后危险文件重新出现
    assert os.path.exists(os.path.join(home_path, '.netrc'))
    assert os.path.exists(os.path.join(home_path, '.rhosts'))


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['119', 'status'] == 2
    assert obj.check() is True


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '删除.netrc,.rhosts的文件'

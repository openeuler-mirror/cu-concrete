import os
import pytest
import pandas as pd
from Items_24_SetNoLoginShell import Items_24_SetNoLoginShell

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_24_SetNoLoginShell.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(passwd_path, 'w') as f:
        f.write('root:x:0:0:root:/root:/bin/bash\n'
                'testuser:x:1000:1000:test:/home/test:/bin/bash\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [passwd_path, passwd_path + '.bak', pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_24_SetNoLoginShell()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 24,
        'query': {
            'path': passwd_path,
            'form': [
                '{ print $1,$7 }',
                # 虚构用户名(测试用的 passwd 里不存在), 避免真的 usermod 改系统账号
                ['test_nologin_user']
            ]
        },
        'change': {'value': '/sbin/nologin'},
        'description': '修改特定用户的shell域'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 24
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['124', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['124', 'status'] == 2
    # 原文件已备份
    assert os.path.exists(passwd_path + '.bak')


def test_check():
    obj = build_instance()
    # passwd 里没有被要求改 shell 的用户 -> 判已加固
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['124', 'status'] == 0
    # 已从备份还原
    assert 'testuser' in open(passwd_path).read()


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['124', 'status'] == 2
    assert obj.check() is True


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '修改特定用户的shell域'

import os
import pytest
import pandas as pd
from Items_01_SetEmptyAccountPwd import Items_01_SetEmptyAccountPwd

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_01_SetEmptyAccountPwd.yaml')
pkl_path = '/tmp/test_data_status.pkl'
shadow_path = '/tmp/test_shadow'
backup_path = '/tmp/test_shadow_bak'


@pytest.fixture(autouse=True)
def prepare_files():
    # 构造 shadow 文件: user1 空口令(会被加固命中), user2 正常
    with open(shadow_path, 'w') as f:
        f.write('user1::\nuser2:12345\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [shadow_path, backup_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_01_SetEmptyAccountPwd()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 1,
        'query': [{
            'path': shadow_path,
            'form': '( $2 == "" || $2 == "!" || $2 == "*" || $2 == "!*") { print $1 }'
        }],
        'change': [{
            # 真实加固用 chpasswd; 测试里换成 echo, 避免真的改系统账号密码
            'set': 'echo',
            'value': '123@cuos!!'
        }],
        'backup_path': backup_path,
        'description': '空口令检查'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 1
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['11', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['11', 'status'] == 2
    # 原始 shadow 已备份
    assert os.path.exists(backup_path)


def test_check():
    obj = build_instance()
    # 存在空口令用户 -> 判未加固
    assert obj.check() is False


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['11', 'status'] == 0
    # 还原后仍是原始内容(空口令用户还在) -> 判未加固
    assert obj.check() is False


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['11', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '空口令检查'

import os
import pytest
import pandas as pd
from Items_27_SetSafeAlias import Items_27_SetSafeAlias

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_27_SetSafeAlias.yaml')
pkl_path = '/tmp/test_data_status.pkl'
bashrc_path = '/tmp/test_bashrc'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(bashrc_path, 'w') as f:
        f.write('# ~/.bashrc\n'
                'PATH=/usr/bin\n'
                'export HTTP_PORT=8080\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [bashrc_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_27_SetSafeAlias()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 27,
        'query': {'path': bashrc_path},
        'change': {'value': ["alias ls='ls -alh'", "alias rm='rm -i'"]},
        'description': '修改ls、rm的显示信息'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 27
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['127', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['127', 'status'] == 2
    content = open(bashrc_path).read()
    assert "alias ls='ls -alh'" in content
    assert "alias rm='rm -i'" in content


def test_fix_is_idempotent():
    """重复加固不应重复追加 alias"""
    obj = build_instance()
    obj.fix()
    obj.fix()
    content = open(bashrc_path).read()
    assert content.count("alias ls='ls -alh'") == 1
    assert content.count("alias rm='rm -i'") == 1


def test_check():
    obj = build_instance()
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    assert obj.check() is True
    obj.rollback()
    content = open(bashrc_path).read()
    # rollback 精确删除两条 alias
    assert "alias ls='ls -alh'" not in content
    assert "alias rm='rm -i'" not in content
    # 无关内容必须保留: 原实现误用 grep 返回码 result[1], 实际执行 sed '/0/d',
    # 会把 bashrc 中所有含 0 的行一起删掉
    assert 'PATH=/usr/bin' in content
    assert 'export HTTP_PORT=8080' in content
    # 回滚后判定为未加固, 状态归 0
    assert obj.check() is False
    assert pd.read_pickle(pkl_path).loc['127', 'status'] == 0


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['127', 'status'] == 2
    assert obj.check() is True


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '修改ls、rm的显示信息'

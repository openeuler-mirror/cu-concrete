import os
import pytest
import pandas as pd
import Items_02_LockUnusedAccount as mod
from Items_02_LockUnusedAccount import Items_02_LockUnusedAccount

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_02_LockUnusedAccount.yaml')
pkl_path = '/tmp/test_data_status.pkl'
# 虚构的用户名, 测试里用 fake base_shell 拦截, 不会碰真实系统账号
USERS = ['test_invalid_user_1', 'test_invalid_user_2']


@pytest.fixture(autouse=True)
def prepare_files():
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    if os.path.exists(pkl_path):
        os.remove(pkl_path)


def build_instance():
    obj = Items_02_LockUnusedAccount()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 2,
        'query': {'value': USERS},
        'description': '锁定无效用户'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(existing=(), locked=()):
    """替换模块里的 base_shell, 避免真的 id/passwd 操作真实系统账号"""
    def _call(command, **kwargs):
        cmd = list(command)
        if cmd[0] == 'id':
            if cmd[1] in existing:
                return ('uid=1001(test) gid=1001(test) groups=1001(test)', 0)
            return ('', 1)
        if cmd[0] == 'passwd' and cmd[1] == '-S':
            if cmd[2] in locked:
                return ('test LK 01/01/2020 0 99999 7 -1', 0)
            return ("passwd: user '%s' does not exist" % cmd[2], 1)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 2
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['12', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    locked = []

    def fake(command, **kwargs):
        if list(command)[:2] == ['passwd', '-l']:
            locked.append(command[2])
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake)
    obj.fix()
    assert locked == USERS
    assert pd.read_pickle(pkl_path).loc['12', 'status'] == 2


def test_check_locked(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(existing=USERS, locked=USERS))
    assert obj.check() is True


def test_check_not_locked(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(existing=USERS, locked=()))
    assert obj.check() is False


def test_rollback(monkeypatch):
    obj = build_instance()
    unlocked = []

    def fake(command, **kwargs):
        if list(command)[:2] == ['passwd', '-u']:
            unlocked.append(command[2])
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake)
    obj.rollback()
    assert unlocked == USERS
    assert pd.read_pickle(pkl_path).loc['12', 'status'] == 0


def test_reset(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(existing=USERS, locked=USERS))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['12', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '锁定无效用户'

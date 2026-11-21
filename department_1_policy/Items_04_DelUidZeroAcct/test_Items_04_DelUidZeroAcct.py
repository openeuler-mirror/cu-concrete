import os
import pytest
import pandas as pd
import Items_04_DelUidZeroAcct as mod
from Items_04_DelUidZeroAcct import Items_04_DelUidZeroAcct

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_04_DelUidZeroAcct.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd'
backup_path = '/tmp/test_passwd_bak'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(passwd_path, 'w') as f:
        f.write('root:x:0:0:root:/root:/bin/bash\n'
                'ghostuser:x:0:0:ghost:/home/ghost:/bin/bash\n'
                'testuser:x:1000:1000:test:/home/test:/bin/bash\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [passwd_path, backup_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_04_DelUidZeroAcct()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 4,
        'query': [{'path': passwd_path, 'form': '{ print $1 }'}],
        'backup_path': backup_path,
        'description': 'uid为0用户检查'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(uid_zero_users=()):
    """替换模块里的 base_shell: 拦截 id/userdel, 避免真的删除系统账号"""
    def _call(command, **kwargs):
        cmd = list(command)
        if cmd[0] == 'id':
            if cmd[1] in uid_zero_users:
                return ('uid=0(ghost) gid=0(root) groups=0(root)', 0)
            return ('uid=1000(test) gid=1000(test) groups=1000(test)', 0)
        if cmd[0] == 'userdel':
            return ('', 0)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 4
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['14', 'status'] == 2


def test_fix_deletes_uid0_user(monkeypatch):
    obj = build_instance()
    deleted = []

    def fake(command, **kwargs):
        cmd = list(command)
        if cmd[0] == 'id':
            return ('uid=0(ghost) gid=0(root) groups=0(root)', 0)
        if cmd[0] == 'userdel':
            deleted.append(cmd[-1])
            return ('', 0)
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake)
    obj.fix()
    # root 被排除, 只有 uid=0 的普通用户被删除
    assert deleted == ['ghostuser']
    # 原文件已备份
    assert os.path.exists(backup_path)
    assert pd.read_pickle(pkl_path).loc['14', 'status'] == 2


def test_check_uid0_exists(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(uid_zero_users=('ghostuser',)))
    assert obj.check() is False


def test_check_ok(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(uid_zero_users=()))
    assert obj.check() is True


def test_rollback(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(uid_zero_users=('ghostuser',)))
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['14', 'status'] == 0
    # 已从备份还原
    assert 'ghostuser' in open(passwd_path).read()


def test_reset(monkeypatch):
    obj = build_instance()
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(uid_zero_users=('ghostuser',)))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['14', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == 'uid为0用户检查'

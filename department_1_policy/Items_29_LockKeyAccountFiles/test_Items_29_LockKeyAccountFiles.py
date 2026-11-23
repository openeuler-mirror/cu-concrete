import os
import pytest
import pandas as pd
import Items_29_LockKeyAccountFiles as mod
from Items_29_LockKeyAccountFiles import Items_29_LockKeyAccountFiles

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_29_LockKeyAccountFiles.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd'
shadow_path = '/tmp/test_shadow'
group_path = '/tmp/test_group'


@pytest.fixture(autouse=True)
def prepare_files():
    for p in (passwd_path, shadow_path, group_path):
        with open(p, 'w') as f:
            f.write('testuser:x:1000:1000::/home/test:/bin/bash\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [passwd_path, shadow_path, group_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_29_LockKeyAccountFiles()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 29,
        'query': {'path': [passwd_path, shadow_path, group_path]},
        'change': {'value': ['+i', '-i']},
        'description': '锁定关键文件'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(commands):
    """替换模块里的 base_shell: 拦截 chattr/lsattr, 只记录不真改文件属性"""
    def _call(command, **kwargs):
        cmd = list(command)
        commands.append(cmd)
        if cmd[0] == 'lsattr':
            return ('--------------e------- testfile', 0)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 29
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['129', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['129', 'status'] == 2
    # 三个文件都执行了 chattr +i
    lock_cmds = [c for c in cmds if c[0] == 'chattr' and c[1] == '+i']
    assert len(lock_cmds) == 3


def test_check(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    # lsattr 返回值里没有 i -> 判未加固
    assert obj.check() is False


def test_rollback(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    obj.rollback()
    # 还原执行 chattr -i
    unlock_cmds = [c for c in cmds if c[0] == 'chattr' and c[1] == '-i']
    assert len(unlock_cmds) == 3


def test_reset(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['129', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '锁定关键文件'

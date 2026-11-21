import os
import sys
import pytest

item_dir = os.path.dirname(os.path.abspath(__file__))
dep_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(dep_dir)
for _p in (item_dir, dep_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import Panda as pd
import Items_03_TightAccountPerm as mod
from Items_03_TightAccountPerm import Items_03_TightAccountPerm

BEFORE = ['644', '600', '644']
AFTER = ['644', '400', '644']


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 passwd/shadow/group 三个文件与 pkl, 并用 python 模拟 chmod/stat 的权限位"""
    files = [tmp_path / 'passwd', tmp_path / 'shadow', tmp_path / 'group']
    for f in files:
        f.write_text('testuser:x:1000:1000::/home/testuser:/bin/bash\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    # 模拟各文件当前的权限位(与 harden_before 一致)
    modes = {str(f): m for f, m in zip(files, BEFORE)}

    def fake_base_shell(cmd, **kwargs):
        if cmd and cmd[0] == 'chmod':
            modes[cmd[2]] = cmd[1]
            return ('', 0)
        if cmd and cmd[0] == 'stat':
            # stat -c %a <path>
            return (modes.get(cmd[3], ''), 0)
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_03_TightAccountPerm()
    obj.config['query']['path'] = [str(f) for f in files]
    obj.pkl_file = str(pkl)
    return obj, [str(f) for f in files], modes, str(pkl)


def test_init(env):
    obj, files, modes, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 3
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    # shadow 权限为 600, 与期望的 400 不一致 -> 判未加固
    obj, files, modes, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, files, modes, pkl = env
    obj.fix()
    # 三个文件权限均被设置为 harden_after
    assert [modes[f] for f in files] == AFTER
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['13', 'status'] == 2


def test_check_one_file_wrong(env):
    # 任一文件权限不符即视为未加固
    obj, files, modes, pkl = env
    obj.fix()
    modes[files[2]] = '777'
    assert obj.check() is False


def test_rollback(env):
    obj, files, modes, pkl = env
    obj.fix()
    obj.rollback()
    # 还原为 harden_before 的权限
    assert [modes[f] for f in files] == BEFORE
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['13', 'status'] == 0


def test_reset(env):
    obj, files, modes, pkl = env
    obj.reset()
    assert [modes[f] for f in files] == AFTER
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['13', 'status'] == 2

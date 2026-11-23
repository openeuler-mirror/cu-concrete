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
import Items_40_SetLogRotate as mod
from Items_40_SetLogRotate import Items_40_SetLogRotate


def active_lines(path):
    """读取生效的配置行(去掉注释行与空行)"""
    with open(path, encoding='utf-8') as f:
        return [l.strip() for l in f.read().splitlines() if l.strip() and not l.strip().startswith('#')]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备临时 logrotate.conf 与状态文件, 并拦截 shell 命令"""
    cfg = tmp_path / 'logrotate.conf'
    cfg.write_text('# see "man logrotate" for details\nweekly\nrotate 4\ncreate\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_40_SetLogRotate()
    obj.config['path'] = str(cfg)
    obj.pkl_file = str(pkl)
    return obj, str(cfg), str(pkl), cmds


def test_init(env):
    obj, cfg, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 40
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    obj, cfg, pkl, cmds = env
    assert obj.check() is False


def test_check_ignores_comment(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write('#rotate 6\n')
    assert obj.check() is False


def test_fix(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    lines = active_lines(cfg)
    assert 'rotate 6' in lines
    assert 'rotate 4' not in lines
    # 同文件其它配置不受影响
    assert 'weekly' in lines
    assert 'create' in lines
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['140', 'status'] == 2


def test_fix_no_service_restart(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    assert cmds == []


def test_fix_replaces_existing_value(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    lines = active_lines(cfg)
    assert lines.count('rotate 6') == 1
    assert 'rotate 4' not in lines
    assert obj.check() is True


def test_rollback(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    lines = active_lines(cfg)
    assert 'rotate 4' in lines
    assert 'rotate 6' not in lines
    assert 'weekly' in lines
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['140', 'status'] == 0


def test_reset(env):
    obj, cfg, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['140', 'status'] == 2
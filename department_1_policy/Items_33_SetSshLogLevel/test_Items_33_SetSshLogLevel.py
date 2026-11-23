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
import Items_33_SetSshLogLevel as mod
from Items_33_SetSshLogLevel import Items_33_SetSshLogLevel


def active_lines(path):
    """读取生效的配置行(去掉注释行与空行)"""
    with open(path, encoding='utf-8') as f:
        return [l.strip() for l in f.read().splitlines() if l.strip() and not l.strip().startswith('#')]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备临时 sshd_config 与状态文件, 并拦截 systemctl restart sshd"""
    cfg = tmp_path / 'sshd_config'
    cfg.write_text('# sshd 配置\n'
                   'Port 22\n'
                   'SyslogFacility AUTH\n'
                   '#LogLevel INFO\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_33_SetSshLogLevel()
    obj.config['path'] = str(cfg)
    obj.pkl_file = str(pkl)
    return obj, str(cfg), str(pkl), cmds


def test_init(env):
    obj, cfg, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 33
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    obj, cfg, pkl, cmds = env
    assert obj.check() is False


def test_check_ignores_comment(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write('#LogLevel INFO\n')
    assert obj.check() is False


def test_fix(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    lines = active_lines(cfg)
    assert 'LogLevel INFO' in lines
    assert 'SyslogFacility AUTH' in lines
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['133', 'status'] == 2
    assert any(c[:2] == ['systemctl', 'restart'] for c in cmds)


def test_rollback(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    lines = active_lines(cfg)
    # 还原时删除该配置行, 回到 sshd 内置默认值 INFO
    assert 'LogLevel INFO' not in lines
    assert 'SyslogFacility AUTH' in lines
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['133', 'status'] == 0


def test_reset(env):
    obj, cfg, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['133', 'status'] == 2

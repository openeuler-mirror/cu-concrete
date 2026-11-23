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
import Items_38_DisSysrq as mod
from Items_38_DisSysrq import Items_38_DisSysrq


def active_lines(path):
    """读取生效的配置行(去掉注释行与空行)"""
    with open(path, encoding='utf-8') as f:
        return [l.strip() for l in f.read().splitlines() if l.strip() and not l.strip().startswith('#')]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备临时 sysctl.conf 与状态文件, 并拦截 shell 命令"""
    cfg = tmp_path / 'sysctl.conf'
    cfg.write_text('# 内核参数\nkernel.dmesg_restrict = 1\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_38_DisSysrq()
    obj.config['path'] = str(cfg)
    obj.pkl_file = str(pkl)
    return obj, str(cfg), str(pkl), cmds


def test_init(env):
    obj, cfg, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 38
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    obj, cfg, pkl, cmds = env
    assert obj.check() is False


def test_check_ignores_comment(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write('#kernel.sysrq=0\n')
    assert obj.check() is False


def test_fix(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    lines = active_lines(cfg)
    assert 'kernel.sysrq=0' in lines
    assert 'kernel.dmesg_restrict = 1' in lines
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['138', 'status'] == 2


def test_fix_runs_sysctl_p(env):
    # 写入后立即生效
    obj, cfg, pkl, cmds = env
    obj.fix()
    assert ['/sbin/sysctl', '-p', '/etc/sysctl.conf'] in cmds


def test_fix_replaces_existing_value(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'a', encoding='utf-8') as f:
        f.write('kernel.sysrq=1\n')
    obj.fix()
    lines = active_lines(cfg)
    assert lines.count('kernel.sysrq=0') == 1
    assert 'kernel.sysrq=1' not in lines
    assert obj.check() is True


def test_rollback(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    lines = active_lines(cfg)
    # 还原时显式写回 kernel.sysrq=1(不删除该配置行, 避免配置与运行时脱节)
    assert 'kernel.sysrq=0' not in lines
    assert 'kernel.sysrq=1' in lines
    assert 'kernel.dmesg_restrict = 1' in lines
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['138', 'status'] == 0


def test_rollback_keeps_key_in_file(env):
    # 配置项始终保留在配置文件中, 且取值为 1
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    assert 'kernel.sysrq=1' in active_lines(cfg)
    assert obj.check() is False


def test_rollback_runs_sysctl_p(env):
    # 还原后立即生效, 配置层与运行时层同步恢复
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    assert ['/sbin/sysctl', '-p', '/etc/sysctl.conf'] in cmds


def test_reset(env):
    obj, cfg, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['138', 'status'] == 2
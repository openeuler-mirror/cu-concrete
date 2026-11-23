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
import Items_39_DisUnkFailLog as mod
from Items_39_DisUnkFailLog import Items_39_DisUnkFailLog


def active_lines(path):
    """读取生效的配置行(去掉注释行与空行)"""
    with open(path, encoding='utf-8') as f:
        return [l.strip() for l in f.read().splitlines() if l.strip() and not l.strip().startswith('#')]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备临时 login.defs 与状态文件, 并拦截 shell 命令"""
    cfg = tmp_path / 'login.defs'
    cfg.write_text('# 账号密码策略\nPASS_MAX_DAYS 90\n# LOG_UNKFAIL_ENAB yes\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_39_DisUnkFailLog()
    obj.config['path'] = str(cfg)
    obj.pkl_file = str(pkl)
    return obj, str(cfg), str(pkl), cmds


def test_init(env):
    obj, cfg, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 39
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    obj, cfg, pkl, cmds = env
    assert obj.check() is False


def test_check_ignores_comment(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'w', encoding='utf-8') as f:
        f.write('#LOG_UNKFAIL_ENAB no\n')
    assert obj.check() is False


def test_fix(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    lines = active_lines(cfg)
    assert 'LOG_UNKFAIL_ENAB no' in lines
    assert 'LOG_UNKFAIL_ENAB yes' not in lines
    assert 'PASS_MAX_DAYS 90' in lines
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['139', 'status'] == 2


def test_fix_no_service_restart(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    assert cmds == []


def test_fix_replaces_existing_value(env):
    obj, cfg, pkl, cmds = env
    with open(cfg, 'a', encoding='utf-8') as f:
        f.write('LOG_UNKFAIL_ENAB yes\n')
    obj.fix()
    lines = active_lines(cfg)
    assert lines.count('LOG_UNKFAIL_ENAB no') == 1
    assert 'LOG_UNKFAIL_ENAB yes' not in lines
    assert obj.check() is True


def test_rollback(env):
    obj, cfg, pkl, cmds = env
    obj.fix()
    obj.rollback()
    lines = active_lines(cfg)
    # 本项配置项都不设还原值, 还原时统一删除该配置行, 回到系统默认值
    assert 'LOG_UNKFAIL_ENAB no' not in lines
    assert 'LOG_UNKFAIL_ENAB yes' not in lines
    assert 'PASS_MAX_DAYS 90' in lines
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['139', 'status'] == 0


def test_reset(env):
    obj, cfg, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['139', 'status'] == 2
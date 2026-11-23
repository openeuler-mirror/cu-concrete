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
import Items_18_SetLoginBanner as mod
from Items_18_SetLoginBanner import Items_18_SetLoginBanner

BANNER = 'Authorized users only. All activities may be monitored and reported.'


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备三个会话提示文件与备份路径, 并拦截 chown/chmod 命令"""
    paths = [tmp_path / 'issue', tmp_path / 'issue.net', tmp_path / 'motd']
    baks = [tmp_path / 'issue.bak', tmp_path / 'issue.net.bak', tmp_path / 'motd.bak']
    for p, c in zip(paths, ('issue', 'issue.net', 'motd')):
        p.write_text(c + ' original\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_cp(source, dst):
        cmds.append(['cp', source, dst])
        import shutil
        shutil.copy(source, dst)
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'cp_shell', fake_cp)
    monkeypatch.setattr(mod.bsf, 'chown_file', lambda form, path: cmds.append(['chown', form, path]) or ('', 0))
    monkeypatch.setattr(mod.bsf, 'chmod_file', lambda form, path: cmds.append(['chmod', form, path]) or ('', 0))

    obj = Items_18_SetLoginBanner()
    obj.config['query']['path'] = [str(p) for p in paths]
    obj.config['change']['value'] = [str(b) for b in baks]
    obj.config['banner'] = BANNER
    obj.pkl_file = str(pkl)
    return obj, [str(p) for p in paths], [str(b) for b in baks], str(pkl), cmds

def test_init(env):
    obj, paths, baks, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 18
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    # 原文件内容不是警告语, 判定为未加固
    obj, paths, baks, pkl, cmds = env
    assert obj.check() is False


def test_fix(env):
    obj, paths, baks, pkl, cmds = env
    obj.fix()
    # 备份了原文件
    for b, origin in zip(baks, ('issue original', 'issue.net original', 'motd original')):
        assert os.path.isfile(b)
        assert origin in open(b, encoding='utf-8').read()
    # 原文件被删除重建, 并写入警告语
    for p in paths:
        assert os.path.isfile(p)
        assert open(p, encoding='utf-8').read().strip() == BANNER
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['118', 'status'] == 2


def test_fix_sets_owner_and_permission(env):
    obj, paths, baks, pkl, cmds = env
    obj.fix()
    assert ['chown', 'root:root', paths[0]] in cmds
    assert ['chmod', '644', paths[0]] in cmds


def test_rollback(env):
    obj, paths, baks, pkl, cmds = env
    obj.fix()
    obj.rollback()
    # 还原为原文件内容
    for p, origin in zip(paths, ('issue original', 'issue.net original', 'motd original')):
        assert open(p, encoding='utf-8').read().strip() == origin
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['118', 'status'] == 0


def test_rollback_without_backup(env):
    # 原文件本就不存在时, 还原后仍不存在
    obj, paths, baks, pkl, cmds = env
    for p in paths:
        os.remove(p)
    obj.fix()
    obj.rollback()
    assert obj.check() is False


def test_reset(env):
    obj, paths, baks, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['118', 'status'] == 2
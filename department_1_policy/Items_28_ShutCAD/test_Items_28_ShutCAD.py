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
import Items_28_ShutCAD as mod
from Items_28_ShutCAD import Items_28_ShutCAD


def make_link(target, path):
    """创建软链接; Windows 无管理员权限时退化为写普通文件(内容记录链接目标)"""
    try:
        os.symlink(target, path)
    except (OSError, NotImplementedError, AttributeError):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(target)


def make_broken_link(target, path):
    """创建指向不存在目标的软链接; Windows 无权限时退化为普通文件"""
    try:
        os.symlink(target, path)
    except (OSError, NotImplementedError, AttributeError):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(target)


def read_link(path):
    if os.path.islink(path):
        return os.readlink(path)
    with open(path, encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 ctrl-alt-del.target 软链接与 pkl, 并用 python 实现替换 base_shell 的 shell 调用"""
    target = tmp_path / 'reboot.target'
    link = tmp_path / 'ctrl-alt-del.target'
    target.write_text('[Unit]\nDescription=test\n', encoding='utf-8')
    if os.path.lexists(link):
        os.remove(link)
    make_link(str(target), str(link))
    pkl = tmp_path / 'data_status.pkl'

    def fake_base_shell(cmd, **kwargs):
        # ln -sfn <target> <path> -> 重建软链接; systemctl daemon-reload -> 无副作用
        if cmd and cmd[0] == 'ln':
            make_link(cmd[2], cmd[3])
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_28_ShutCAD()
    obj.config['query']['path'] = str(link)
    obj.config['query']['link_target'] = str(target)
    obj.pkl_file = str(pkl)
    return obj, str(link), str(target), str(pkl)


def test_init(env):
    obj, link, target, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 28
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    # 软链接存在 -> 未加固
    obj, link, target, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, link, target, pkl = env
    obj.fix()
    # 加固态: 软链接被删除
    assert not os.path.lexists(link)
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['128', 'status'] == 2


def test_fix_broken_link(env):
    # 断链的软链接也必须被删除(用 lexists 判定, 不能漏删)
    obj, link, target, pkl = env
    os.remove(link)
    make_broken_link(str(target) + '.not-exist', link)
    obj.fix()
    assert not os.path.lexists(link)
    assert obj.check() is True


def test_rollback(env):
    obj, link, target, pkl = env
    obj.fix()
    obj.rollback()
    # 还原: 软链接被重建, 且指向原目标
    assert os.path.lexists(link)
    assert read_link(link) == target
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['128', 'status'] == 0


def test_reset(env):
    obj, link, target, pkl = env
    obj.reset()
    assert pd.read_pickle(pkl).loc['128', 'status'] == 2
    assert not os.path.lexists(link)
    assert obj.check() is True

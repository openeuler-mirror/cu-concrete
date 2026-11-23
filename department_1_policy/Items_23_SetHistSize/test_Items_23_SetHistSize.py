import os
import re
import sys
import pytest

item_dir = os.path.dirname(os.path.abspath(__file__))
dep_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(dep_dir)
for _p in (item_dir, dep_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import Panda as pd
import Items_23_SetHistSize as mod
from Items_23_SetHistSize import Items_23_SetHistSize

HISTSIZE = 'export HISTSIZE=5'


def posix_to_py(form):
    """把 grep -E / sed 的 POSIX 字符类转成 python re 写法"""
    return form.replace('[[:space:]]', '[ \\t]')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 /etc/profile 与 pkl, 并用 python 实现替换 bsf/base_shell 的 shell 调用"""
    profile = tmp_path / 'profile'
    # 初始为未加固形态: export HISTSIZE=1000
    profile.write_text('# /etc/profile\nexport HISTSIZE=1000\nexport PATH=/usr/bin:/bin\n',
                       encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(posix_to_py(form))
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if pattern.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_sed(old, new, path):
        # sed -i s@{old}@{new}@g : old 为 re.escape 后的原文, 当作正则处理
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(old)
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write(pattern.sub(new, l) + '\n')
        return ('', 0)

    def fake_append_line(line, path):
        # sh -c 'echo "$1" >> "$2"' : 追加一行内容(空串则追加一个空行)
        if not os.path.isfile(path):
            return ('', 2)
        with open(path, 'a', encoding='utf-8') as f:
            f.write((line or '') + '\n')
        return ('', 0)

    def fake_remove_line(line, path):
        # sed -i /{line}/d : 删除匹配该正则的行
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(posix_to_py(line))
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if not pattern.search(l):
                    f.write(l + '\n')
        return ('', 0)

    def fake_base_shell(cmd, input=None, **kwargs):
        # sudo tee -a <path> : 把 input 原样追加到文件; bash -c source <path> : 无副作用
        if cmd and cmd[-2] == '-a':
            with open(cmd[-1], 'a', encoding='utf-8') as f:
                f.write(input or '')
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append_line)
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_23_SetHistSize()
    obj.config['query']['path'] = str(profile)
    obj.pkl_file = str(pkl)
    return obj, str(profile), str(pkl)


def test_init(env):
    obj, profile, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 23
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    # export HISTSIZE=1000 -> 判未加固
    obj, profile, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, profile, pkl = env
    obj.fix()
    content = open(profile, encoding='utf-8').read()
    assert HISTSIZE in content
    assert 'export HISTSIZE=1000' not in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['123', 'status'] == 2


def test_fix_rewrites_value_in_place(env):
    """已有配置项时就地把值改为标准值, 位置不变"""
    obj, profile, pkl = env
    obj.fix()
    lines = open(profile, encoding='utf-8').read().splitlines()
    # 原第 2 行(下标 1)仍是 export HISTSIZE=5, 没有被挪到末尾
    assert lines[1] == HISTSIZE
    assert lines.count(HISTSIZE) == 1
    assert obj.check() is True


def test_fix_appends_with_blank_line_when_missing(env):
    """没有配置项时: 文件末尾空一行后追加标准值"""
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\nexport PATH=/usr/bin:/bin\n')
    obj.fix()
    lines = open(profile, encoding='utf-8').read().splitlines()
    assert lines[-2] == ''          # 末尾空一行
    assert lines[-1] == HISTSIZE    # 下一行是标准配置
    assert obj.check() is True


def test_fix_keeps_only_one_histsize_line(env):
    """存在重复配置行时, 加固后只保留一条"""
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\n'
                'export HISTSIZE=1000\n'
                'export HISTSIZE=2000\n'
                'export PATH=/usr/bin:/bin\n')
    obj.fix()
    lines = [l for l in open(profile, encoding='utf-8').read().splitlines() if 'HISTSIZE' in l]
    assert lines == [HISTSIZE]
    assert obj.check() is True


def test_fix_is_idempotent(env):
    obj, profile, pkl = env
    obj.fix()
    before = open(profile, encoding='utf-8').read()
    obj.fix()
    assert open(profile, encoding='utf-8').read() == before
    assert obj.check() is True


def test_fix_appends_when_missing(env):
    # 原来没有 HISTSIZE 行时追加到文件末尾
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\nexport PATH=/usr/bin:/bin\n')
    obj.fix()
    assert HISTSIZE in open(profile, encoding='utf-8').read()
    assert obj.check() is True


def test_fix_keeps_other_lines(env):
    obj, profile, pkl = env
    obj.fix()
    assert 'export PATH=/usr/bin:/bin' in open(profile, encoding='utf-8').read()


def test_rollback(env):
    obj, profile, pkl = env
    obj.fix()
    obj.rollback()
    assert HISTSIZE not in open(profile, encoding='utf-8').read()
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['123', 'status'] == 0


def test_rollback_removes_all_histsize_lines(env):
    """还原要删除所有以 export HISTSIZE 开头的行, 不只是值为 5 的那一行"""
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\n'
                'export HISTSIZE=5\n'
                'export HISTSIZE=1000\n'
                'export  HISTSIZE=2000\n'
                'export PATH=/usr/bin:/bin\n')
    obj.rollback()
    content = open(profile, encoding='utf-8').read()
    assert 'HISTSIZE' not in content
    # 其它配置行不受影响
    assert 'export PATH=/usr/bin:/bin' in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['123', 'status'] == 0


def test_reset(env):
    obj, profile, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['123', 'status'] == 2

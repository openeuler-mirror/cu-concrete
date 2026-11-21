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
import Items_05_SetPasswdExpiry as mod
from Items_05_SetPasswdExpiry import Items_05_SetPasswdExpiry

AFTER = [
    'PASS_MAX_DAYS 90',
    'PASS_MIN_DAYS 7',
    'PASS_MIN_LEN 10',
    'PASS_WARN_AGE 30',
]
BEFORE = [
    'PASS_MAX_DAYS 99999',
    'PASS_MIN_DAYS 0',
    'PASS_MIN_LEN 5',
    'PASS_WARN_AGE 7',
]


def posix_to_py(form):
    """把 grep -E 的 POSIX 字符类转成 python re 写法, 保持匹配语义一致"""
    return form.replace('[[:space:]]', '[ \\t]')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 /etc/login.defs 与 pkl, 并用 python 实现替换 bsf 的 shell 调用"""
    defs = tmp_path / 'login.defs'
    defs.write_text('\n'.join(BEFORE) + '\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(posix_to_py(form))
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if pattern.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_sed(old, new, path):
        if not os.path.isfile(path):
            return ('', 2)
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                f.write((l.replace(old, new) if old in l else l) + '\n')
        return ('', 0)

    def fake_append(line, path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append)

    obj = Items_05_SetPasswdExpiry()
    obj.config['query']['path'] = str(defs)
    obj.pkl_file = str(pkl)
    return obj, str(defs), str(pkl)


def test_init(env):
    obj, defs, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 5
    assert obj.get_des() == obj.config['description']
    # 四个键的加固值与还原值均由 yaml 提供
    assert obj.config['change']['value'] == AFTER
    assert obj.config['recovery']['value'] == BEFORE


def test_check_before_fix(env):
    # 初始为发行版默认值, 判定为未加固
    obj, defs, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, defs, pkl = env
    obj.fix()
    content = open(defs, encoding='utf-8').read()
    for want in AFTER:
        assert want in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['15', 'status'] == 2


def test_fix_appends_when_missing(env):
    # 目标键缺失时追加到文件末尾
    obj, defs, pkl = env
    content = open(defs, encoding='utf-8').read()
    content = content.replace(BEFORE[2] + '\n', '')
    open(defs, 'w', encoding='utf-8').write(content)
    obj.fix()
    assert AFTER[2] in open(defs, encoding='utf-8').read()
    assert obj.check() is True


def test_check_partial_value(env):
    # 只满足部分键值时不算已加固
    obj, defs, pkl = env
    content = open(defs, encoding='utf-8').read().replace(BEFORE[1], AFTER[1])
    open(defs, 'w', encoding='utf-8').write(content)
    assert obj.check() is False


def test_check_one_key_missing(env):
    # 缺少任何一个键都不算已加固
    obj, defs, pkl = env
    obj.fix()
    content = open(defs, encoding='utf-8').read().replace(AFTER[3] + '\n', '')
    open(defs, 'w', encoding='utf-8').write(content)
    assert obj.check() is False


def test_rollback(env):
    obj, defs, pkl = env
    obj.fix()
    obj.rollback()
    content = open(defs, encoding='utf-8').read()
    for want in BEFORE:
        assert want in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['15', 'status'] == 0


def test_reset(env):
    obj, defs, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['15', 'status'] == 2

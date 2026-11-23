import os
import re
import shutil
import sys
import pytest

item_dir = os.path.dirname(os.path.abspath(__file__))
dep_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(dep_dir)
for _p in (item_dir, dep_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import Panda as pd
import Items_26_LimitPasswdReuse as mod
from Items_26_LimitPasswdReuse import Items_26_LimitPasswdReuse

TARGET = 'password sufficient pam_unix.so sha512 shadow nullok try_first_pass use_authtok remember=5'
ORIGINAL = 'password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok\n'


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 system-auth / password-auth 两个文件, 并用 python 实现替换 bsf 的 shell 调用"""
    files = [tmp_path / 'system-auth', tmp_path / 'password-auth']
    for f in files:
        f.write_text('auth        required      pam_env.so\n'
                     + ORIGINAL
                     + 'password    required      pam_deny.so\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(form)
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if pattern.search(l)]
        return ('\n'.join(out), 0)

    def fake_sed(old, new, path):
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

    obj = Items_26_LimitPasswdReuse()
    obj.config['query']['path'] = [str(f) for f in files]
    obj.pkl_file = str(pkl)
    return obj, [str(f) for f in files], str(pkl)

def test_init(env):
    obj, files, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 26
    assert obj.get_des() == obj.config['description']


def test_fix(env):
    obj, files, pkl = env
    obj.fix()
    # 两个文件都写入带 remember=5 的标准行
    for f in files:
        assert TARGET in open(f, encoding='utf-8').read()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['126', 'status'] == 2


def test_fix_appends_when_missing(env):
    obj, files, pkl = env
    for f in files:
        content = open(f, encoding='utf-8').read().replace(ORIGINAL, '')
        open(f, 'w', encoding='utf-8').write(content)
    obj.fix()
    for f in files:
        assert TARGET in open(f, encoding='utf-8').read()
    assert obj.check() is True


def test_check_before_fix(env):
    obj, files, pkl = env
    assert obj.check() is False


def test_check_only_remember(env):
    # 只带 remember=5, 缺少其余参数时不算已加固
    obj, files, pkl = env
    for f in files:
        content = open(f, encoding='utf-8').read().replace(
            ORIGINAL, 'password    sufficient    pam_unix.so remember=5\n')
        open(f, 'w', encoding='utf-8').write(content)
    assert obj.check() is False


def test_check_one_file_missing(env):
    obj, files, pkl = env
    obj.fix()
    os.remove(files[1])
    assert obj.check() is False


def test_rollback(env):
    obj, files, pkl = env
    obj.fix()
    obj.rollback()
    # 还原为不含 remember=5 的标准行
    for f in files:
        content = open(f, encoding='utf-8').read()
        assert 'remember=' not in content
        assert 'pam_unix.so' in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['126', 'status'] == 0


def test_reset(env):
    obj, files, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['126', 'status'] == 2
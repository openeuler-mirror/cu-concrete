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
import Items_07_SetLoginFailLock as mod
from Items_07_SetLoginFailLock import Items_07_SetLoginFailLock

AFTER = [
    'deny=5 even_deny_root unlock_time=900',
    'auth required pam_faillock.so preauth audit deny=5 even_deny_root unlock_time=900',
    'auth [default=die] pam_faillock.so authfail audit deny=5 even_deny_root unlock_time=900',
    'auth sufficient pam_faillock.so authsucc audit deny=5 even_deny_root unlock_time=900',
]
BEFORE = [
    'deny=3 even_deny_root unlock_time=60',
    'auth required pam_faillock.so preauth audit deny=3 even_deny_root unlock_time=60',
    'auth [default=die] pam_faillock.so authfail audit deny=3 even_deny_root unlock_time=60',
    'auth sufficient pam_faillock.so authsucc audit deny=3 even_deny_root unlock_time=60',
]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 system-auth / password-auth 两个文件, 并用 python 实现替换 shell 调用"""
    files = [tmp_path / 'system-auth', tmp_path / 'password-auth']
    for f in files:
        f.write_text('auth        required      pam_env.so\n'
                     + BEFORE[1] + '\n'
                     + BEFORE[2] + '\n'
                     + BEFORE[3] + '\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(form)
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if pattern.search(l)]
        return ('\n'.join(out), 0)

    def fake_sed(old, new, path):
        lines = open(path, encoding='utf-8').read().splitlines()
        pattern = re.compile(old)
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if old in l:
                    l = l.replace(old, new)
                elif pattern.search(l):
                    l = pattern.sub(new.replace('\\', '\\\\'), l)
                f.write(l + '\n')
        return ('', 0)

    def fake_append(line, path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
        return ('', 0)

    def fake_base_shell(cmd, **kwargs):
        # check() 使用 grep -F -x 整行完全匹配
        if cmd and cmd[0] == 'grep':
            expect, path = cmd[3], cmd[4]
            if not os.path.isfile(path):
                return ('', 2)
            hit = [l for l in open(path, encoding='utf-8').read().splitlines() if l == expect]
            return ('\n'.join(hit), 0 if hit else 1)
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append)
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_07_SetLoginFailLock()
    obj.config['query']['path'] = [str(f) for f in files]
    obj.pkl_file = str(pkl)
    return obj, [str(f) for f in files], str(pkl)

def test_init(env):
    obj, files, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 7
    assert obj.get_des() == obj.config['description']


def test_check_before_fix(env):
    # 初始为 deny=3/unlock_time=60, 判定为未加固
    obj, files, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, files, pkl = env
    obj.fix()
    # 两个文件的三条行都升级为 deny=5/unlock_time=900
    for f in files:
        content = open(f, encoding='utf-8').read()
        for idx in (1, 2, 3):
            assert AFTER[idx] in content
            assert BEFORE[idx] not in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['17', 'status'] == 2


def test_fix_appends_when_missing(env):
    # 缺少某条控制位时补齐标准行
    obj, files, pkl = env
    for f in files:
        content = open(f, encoding='utf-8').read().replace(BEFORE[3] + '\n', '')
        open(f, 'w', encoding='utf-8').write(content)
    obj.fix()
    for f in files:
        assert AFTER[3] in open(f, encoding='utf-8').read()
    assert obj.check() is True


def test_check_one_file_missing(env):
    # 两个文件都满足才算已加固
    obj, files, pkl = env
    obj.fix()
    os.remove(files[1])
    assert obj.check() is False


def test_rollback(env):
    obj, files, pkl = env
    obj.fix()
    obj.rollback()
    # 两个文件都还原为 deny=3/unlock_time=60
    for f in files:
        content = open(f, encoding='utf-8').read()
        for idx in (1, 2, 3):
            assert BEFORE[idx] in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['17', 'status'] == 0


def test_reset(env):
    obj, files, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['17', 'status'] == 2
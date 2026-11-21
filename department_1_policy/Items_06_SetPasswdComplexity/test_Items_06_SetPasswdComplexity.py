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
import Items_06_SetPasswdComplexity as mod
from Items_06_SetPasswdComplexity import Items_06_SetPasswdComplexity

PWQUALITY = ('password requisite pam_pwquality.so minlen=10 minclass=4 difok=3 enforce_for_root '
             'try_first_pass local_users_only retry=3 dcredit=-1 ucredit=-1 lcredit=-1 ocredit=-1')
RECOVERY = 'password requisite pam_pwquality.so try_first_pass local_users_only'
ORIGINAL = ('password    requisite     pam_pwquality.so try_first_pass local_users_only retry=3\n')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 system-auth / password-auth 两个文件, 并用 python 实现替换 bsf 的 shell 调用"""
    files = [tmp_path / 'system-auth', tmp_path / 'password-auth']
    baks = [tmp_path / 'system-auth_bak', tmp_path / 'password-auth_bak']
    for f in files:
        f.write_text('auth        required      pam_env.so\n'
                     + ORIGINAL
                     + 'password    sufficient    pam_unix.so sha512 shadow nullok try_first_pass use_authtok\n',
                     encoding='utf-8')
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

    def fake_cp(src, dst):
        if not os.path.isfile(src):
            return ('', 1)
        shutil.copy(src, dst)
        return ('', 0)

    def fake_touch(path):
        open(path, 'a').close()
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append)
    monkeypatch.setattr(mod.bsf, 'cp_shell', fake_cp)
    monkeypatch.setattr(mod.bsf, 'touch_shell', fake_touch)

    obj = Items_06_SetPasswdComplexity()
    obj.config['query']['path'] = [str(f) for f in files]
    obj.pkl_file = str(pkl)
    return obj, [str(f) for f in files], [str(b) for b in baks], str(pkl)

def test_init(env):
    obj, files, baks, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 6
    assert obj.get_des() == obj.config['description']
    # 两个文件使用同一个还原值
    assert obj.config['change']['recovery'] == RECOVERY


def test_fix(env):
    obj, files, baks, pkl = env
    obj.fix()
    # 两个文件都写入完整的基线参数行
    for f in files:
        assert PWQUALITY in open(f, encoding='utf-8').read()
    # 本项不做备份, 不应生成 *_bak 文件
    for b in baks:
        assert not os.path.isfile(b)
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['16', 'status'] == 2


def test_fix_appends_when_missing(env):
    # 目标行不存在时追加到文件末尾
    obj, files, baks, pkl = env
    for f in files:
        content = open(f, encoding='utf-8').read().replace(ORIGINAL, '')
        open(f, 'w', encoding='utf-8').write(content)
    obj.fix()
    for f in files:
        assert PWQUALITY in open(f, encoding='utf-8').read()
    assert obj.check() is True


def test_check_before_fix(env):
    obj, files, baks, pkl = env
    assert obj.check() is False


def test_check_partial_params(env):
    # 只满足 minlen/minclass 时不算已加固
    obj, files, baks, pkl = env
    for f in files:
        content = open(f, encoding='utf-8').read().replace(
            ORIGINAL, 'password    requisite     pam_pwquality.so minlen=10 minclass=4\n')
        open(f, 'w', encoding='utf-8').write(content)
    assert obj.check() is False


def test_check_one_file_missing(env):
    # 两个文件都满足才算已加固
    obj, files, baks, pkl = env
    obj.fix()
    os.remove(files[1])
    assert obj.check() is False


def test_rollback(env):
    obj, files, baks, pkl = env
    obj.fix()
    obj.rollback()
    # 用还原值替换 pam_pwquality 行, 加固参数全部去掉
    for f in files:
        content = open(f, encoding='utf-8').read()
        assert RECOVERY + '\n' in content
        assert 'minlen=10' not in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['16', 'status'] == 0


def test_no_backup_file_generated(env):
    # 本项不做备份: 反复加固也不会生成 *_bak 文件
    obj, files, baks, pkl = env
    obj.fix()
    for f in files:
        with open(f, 'a', encoding='utf-8') as fh:
            fh.write('# manual change\n')
    obj.fix()
    for b in baks:
        assert not os.path.isfile(b)
    # 还原按 change.recovery 改写配置行, 不依赖备份文件
    obj.rollback()
    for f in files:
        content = open(f, encoding='utf-8').read()
        assert RECOVERY + '\n' in content
        assert 'minlen=10' not in content


def test_reset(env):
    obj, files, baks, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['16', 'status'] == 2
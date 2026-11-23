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
import Items_14_RestrictSuWheel as mod
from Items_14_RestrictSuWheel import Items_14_RestrictSuWheel

WHEEL = 'auth required pam_wheel.so use_uid'
ROOTOK = 'auth sufficient pam_rootok.so'
ONLY = 'SU_WHEEL_ONLY yes'


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 /etc/pam.d/su 与 /etc/login.defs 两个文件, 并用 python 实现替换 bsf 的 shell 调用"""
    su = tmp_path / 'su'
    defs = tmp_path / 'login.defs'
    su.write_text('# su pam config\n', encoding='utf-8')
    defs.write_text('UMASK 022\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(form)
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

    def fake_cp(src, dst):
        if not os.path.isfile(src):
            return ('', 1)
        shutil.copy(src, dst)
        return ('', 0)

    def fake_remove_line(line, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(line)
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if not pattern.search(l):
                    f.write(l + '\n')
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append)
    monkeypatch.setattr(mod.bsf, 'cp_shell', fake_cp)
    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)

    obj = Items_14_RestrictSuWheel()
    obj.config['query']['path'] = [str(su), str(defs), str(su)]
    obj.pkl_file = str(pkl)
    return obj, str(su), str(defs), str(pkl)


def test_init(env):
    obj, su, defs, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 14
    assert obj.get_des() == obj.config['description']
    # 三项配置: pam_wheel / SU_WHEEL_ONLY / pam_rootok
    assert len(obj.config['query']['value']) == 3
    assert obj.config['query']['value'][2] == ROOTOK


def test_check_before_fix(env):
    obj, su, defs, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, su, defs, pkl = env
    obj.fix()
    su_text = open(su, encoding='utf-8').read()
    defs_text = open(defs, encoding='utf-8').read()
    # pam_wheel 限制行 + pam_rootok 豁免行都写入 /etc/pam.d/su
    assert WHEEL in su_text
    assert ROOTOK in su_text
    # SU_WHEEL_ONLY 写入 /etc/login.defs
    assert ONLY in defs_text
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['114', 'status'] == 2


def test_fix_appends_rootok_when_missing(env):
    # 原始文件里没有 pam_rootok 行时补齐(缺失会导致 root 也无法 su)
    obj, su, defs, pkl = env
    obj.fix()
    with open(su, 'w', encoding='utf-8') as f:
        f.write('# su pam config\n' + WHEEL + '\n')
    obj.fix()
    assert ROOTOK in open(su, encoding='utf-8').read()
    assert obj.check() is True


def test_check_commented_rootok(env):
    # pam_rootok 被注释时视为未加固
    obj, su, defs, pkl = env
    obj.fix()
    with open(su, 'w', encoding='utf-8') as f:
        f.write('# su pam config\n' + WHEEL + '\n' + '#' + ROOTOK + '\n')
    assert obj.check() is False


def test_check_missing_rootok(env):
    # 完全没有 pam_rootok 行时视为未加固
    obj, su, defs, pkl = env
    obj.fix()
    with open(su, 'w', encoding='utf-8') as f:
        f.write('# su pam config\n' + WHEEL + '\n')
    assert obj.check() is False


def test_check_commented_su_wheel_only(env):
    # SU_WHEEL_ONLY 被注释时视为未加固(注释行不生效)
    obj, su, defs, pkl = env
    obj.fix()
    with open(defs, 'w', encoding='utf-8') as f:
        f.write('UMASK 022\n#' + ONLY + '\n')
    assert obj.check() is False


def test_check_wrong_su_wheel_only_value(env):
    # SU_WHEEL_ONLY 值不是 yes 时视为未加固
    obj, su, defs, pkl = env
    obj.fix()
    with open(defs, 'w', encoding='utf-8') as f:
        f.write('UMASK 022\nSU_WHEEL_ONLY no\n')
    assert obj.check() is False


def test_check_missing_su_wheel_only(env):
    # 完全没有 SU_WHEEL_ONLY 行时视为未加固
    obj, su, defs, pkl = env
    obj.fix()
    with open(defs, 'w', encoding='utf-8') as f:
        f.write('UMASK 022\n')
    assert obj.check() is False


def test_fix_normalizes_commented_su_wheel_only(env):
    # 注释掉的 SU_WHEEL_ONLY 会被规范为标准行(不再是注释)
    obj, su, defs, pkl = env
    with open(defs, 'w', encoding='utf-8') as f:
        f.write('UMASK 022\n#' + ONLY + '\n')
    obj.fix()
    defs_text = open(defs, encoding='utf-8').read()
    assert ONLY + '\n' in defs_text
    assert '#' + ONLY not in defs_text
    assert obj.check() is True


def test_fix_normalizes_wrong_su_wheel_only_value(env):
    # 值不对的 SU_WHEEL_ONLY 会被替换为标准行
    obj, su, defs, pkl = env
    with open(defs, 'w', encoding='utf-8') as f:
        f.write('UMASK 022\nSU_WHEEL_ONLY no\n')
    obj.fix()
    defs_text = open(defs, encoding='utf-8').read()
    assert ONLY + '\n' in defs_text
    assert 'SU_WHEEL_ONLY no' not in defs_text
    assert obj.check() is True


def test_rollback(env):
    obj, su, defs, pkl = env
    obj.fix()
    obj.rollback()
    su_text = open(su, encoding='utf-8').read()
    defs_text = open(defs, encoding='utf-8').read()
    # pam_wheel 行被注释(撤销仅wheel组可su的限制)
    assert '#' + WHEEL in su_text
    assert '\n' + WHEEL not in su_text
    # SU_WHEEL_ONLY 被删除
    assert ONLY not in defs_text
    # pam_rootok 行保留, 维持 root 的 su 豁免
    assert ROOTOK in su_text
    assert '#' + ROOTOK not in su_text
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['114', 'status'] == 0


def test_reset(env):
    obj, su, defs, pkl = env
    obj.reset()
    su_text = open(su, encoding='utf-8').read()
    assert WHEEL in su_text
    assert ROOTOK in su_text
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['114', 'status'] == 2

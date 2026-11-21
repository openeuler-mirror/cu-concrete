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
import Items_10_SetSessionTimeout as mod
from Items_10_SetSessionTimeout import Items_10_SetSessionTimeout

STANDARD = 'export TMOUT=300'


def posix_to_py(form):
    """把 grep -E / sed 的 POSIX 字符类转成 python re 写法"""
    return form.replace('[[:space:]]', '[ \\t]').replace('\\+', '+')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 /etc/profile 与 pkl, 并用 python 实现替换 bsf 的 shell 调用"""
    profile = tmp_path / 'profile'
    profile.write_text('# /etc/profile\n'
                       'export PATH=/usr/bin:/bin\n'
                       'TMOUT=600\n'
                       '#export TMOUT=1200\n'
                       'alias ll="ls -l"\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(posix_to_py(form))
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if pattern.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_remove_line(form, path):
        # sed -i /{form}/d
        if not os.path.isfile(path):
            return ('', 2)
        pattern = re.compile(posix_to_py(form))
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if not pattern.search(l):
                    f.write(l + '\n')
        return ('', 0)

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
    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)
    monkeypatch.setattr(mod.bsf, 'sed_shell', fake_sed)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append)

    obj = Items_10_SetSessionTimeout()
    obj.config['change']['path'] = str(profile)
    obj.pkl_file = str(pkl)
    return obj, str(profile), str(pkl)


def test_init(env):
    obj, profile, pkl = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 10
    assert obj.get_des() == obj.config['description']
    assert obj.config['change']['value'] == STANDARD


def test_check_before_fix(env):
    # 只有 TMOUT=600, 没有 TMOUT=300 -> 未加固
    obj, profile, pkl = env
    assert obj.check() is False


def test_fix(env):
    obj, profile, pkl = env
    obj.fix()
    content = open(profile, encoding='utf-8').read()
    # 在文件末尾追加标准行
    assert STANDARD + '\n' in content
    # 不带 export 前缀的旧写法不在识别范围内, 保持原样
    assert 'TMOUT=600' in content
    # 注释行保留, 其它配置不受影响
    assert '#export TMOUT=1200' in content
    assert 'export PATH=/usr/bin:/bin' in content
    assert 'alias ll="ls -l"' in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['110', 'status'] == 2


def test_fix_appends_on_new_line_when_no_trailing_newline(env):
    # 文件末尾没有换行时, 追加的配置另起一行, 不会粘到上一行末尾
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\nexport PATH=/usr/bin:/bin')
    obj.fix()
    content = open(profile, encoding='utf-8').read()
    assert content.endswith(STANDARD + '\n')
    assert 'export PATH=/usr/bin:/bin\n' + STANDARD in content
    assert obj.check() is True


def test_fix_appends_when_no_tmout(env):
    # 完全没有 TMOUT 行时追加标准行
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\nexport PATH=/usr/bin:/bin\n')
    obj.fix()
    content = open(profile, encoding='utf-8').read()
    assert STANDARD + '\n' in content
    assert obj.check() is True


def test_fix_is_idempotent(env):
    # 二次加固不重复写入, 文件内容保持不变
    obj, profile, pkl = env
    obj.fix()
    before = open(profile, encoding='utf-8').read()
    obj.fix()
    after = open(profile, encoding='utf-8').read()
    assert before == after
    assert after.count('TMOUT=300') == 1


def test_check_commented_line_only(env):
    # 只有注释行时不算已加固
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('#export TMOUT=300\n')
    assert obj.check() is False


def test_check_wrong_value(env):
    # 值为 600 时不算已加固
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('export TMOUT=600\n')
    assert obj.check() is False


def test_check_value_prefix_not_matched(env):
    # TMOUT=3000 的值不是 300, 不算已加固
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('export TMOUT=3000\n')
    assert obj.check() is False


def test_check_accepts_plain_form(env):
    # 只认 export TMOUT= 开头的配置, 不带 export 前缀的不算已加固
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('TMOUT=300\n')
    assert obj.check() is False


def test_rollback(env):
    obj, profile, pkl = env
    obj.fix()
    obj.rollback()
    content = open(profile, encoding='utf-8').read()
    # TMOUT 行被删除, 注释行不受影响
    assert 'TMOUT=300' not in content
    assert '#export TMOUT=1200' in content
    assert 'export PATH=/usr/bin:/bin' in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['110', 'status'] == 0


def test_rollback_removes_all_tmout_forms(env):
    # 还原时删除所有 export TMOUT= 配置行, 彻底回到未设置状态
    obj, profile, pkl = env
    with open(profile, 'w', encoding='utf-8') as f:
        f.write('# /etc/profile\nexport TMOUT=300\nexport TMOUT=600\n')
    obj.rollback()
    content = open(profile, encoding='utf-8').read()
    assert 'TMOUT' not in content
    assert '# /etc/profile' in content
    assert obj.check() is False


def test_reset(env):
    obj, profile, pkl = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['110', 'status'] == 2
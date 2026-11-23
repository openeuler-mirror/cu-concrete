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
import Items_20_DisIcmpEcho as mod
from Items_20_DisIcmpEcho import Items_20_DisIcmpEcho

yaml_path = os.path.join(item_dir, 'Items_20_DisIcmpEcho.yaml')
STANDARD = 'net.ipv4.icmp_echo_ignore_all=1'
RECOVERY = 'net.ipv4.icmp_echo_ignore_all=0'


def posix_to_py(form):
    """把 grep -E / sed 的 POSIX 字符类转成 python re 写法"""
    return form.replace('[[:space:]]', '[ \\t]').replace('\\+', '+')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 sysctl.conf 与 pkl, 并用 python 实现替换 bsf/base_shell 的 shell 调用"""
    conf = tmp_path / 'sysctl.conf'
    # 初始为未加固形态: 值为 0(等号两侧带空格的旧写法)
    conf.write_text('# /etc/sysctl.conf\n'
                    'net.ipv4.icmp_echo_ignore_all = 0\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    pd.DataFrame(columns=['status', 'module_name', 'module_path']).to_pickle(pkl)
    cmds = []

    def fake_grep(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(posix_to_py(form))
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if regex.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_remove_line(form, path):
        # sed -i /{form}/d
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(posix_to_py(form))
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if not regex.search(l):
                    f.write(l + '\n')
        return ('', 0)

    def fake_append_line(line, path):
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
        return ('', 0)

    def fake_base_shell(command, **kwargs):
        # 拦截 sysctl -p, 不会真的改内核参数
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append_line)
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_20_DisIcmpEcho()
    obj.config['query']['path'] = str(conf)
    obj.pkl_file = str(pkl)
    return obj, str(conf), str(pkl), cmds


def test_init(env):
    obj, conf, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 20
    assert obj.config['change']['value'] == STANDARD
    assert obj.config['change']['recovery'] == RECOVERY


def test_check_before_fix(env):
    # 值为 0 -> 判未加固
    obj, conf, pkl, cmds = env
    assert obj.check() is False


def test_check_accepts_spaced_form(env):
    # 等号两侧带空格的写法同样识别, 取值是 1 即为已加固
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('net.ipv4.icmp_echo_ignore_all = 1\n')
    assert obj.check() is True


def test_fix(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    content = open(conf, encoding='utf-8').read()
    # 在文件末尾追加标准行, 旧写法被清理
    assert STANDARD + '\n' in content
    assert 'net.ipv4.icmp_echo_ignore_all = 0' not in content
    # 注释行与其它配置不受影响
    assert '# /etc/sysctl.conf' in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['120', 'status'] == 2
    # 配置立即生效
    assert ['sysctl', '-p'] in cmds


def test_fix_is_idempotent(env):
    # 二次加固内容不变, 配置项仍然只有一行
    obj, conf, pkl, cmds = env
    obj.fix()
    before = open(conf, encoding='utf-8').read()
    obj.fix()
    after = open(conf, encoding='utf-8').read()
    assert before == after
    assert after.count('icmp_echo_ignore_all') == 1
    assert obj.check() is True


def test_fix_appends_on_new_line_when_no_trailing_newline(env):
    # 文件末尾没有换行时, 追加的配置另起一行, 不会粘到上一行末尾
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# /etc/sysctl.conf')
    obj.fix()
    content = open(conf, encoding='utf-8').read()
    assert content.endswith(STANDARD + '\n')
    assert '# /etc/sysctl.conf\n' + STANDARD in content


def test_rollback(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    content = open(conf, encoding='utf-8').read()
    # 还原不是删除配置行, 而是显式写回 0, 配置项始终保留在配置文件中
    assert RECOVERY + '\n' in content
    assert 'icmp_echo_ignore_all = 0' not in content
    # 取值为 0 -> 判未加固
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['120', 'status'] == 0
    # sysctl -p 刷新, 内核运行时值与配置文件一致(能响应 ping)
    assert ['sysctl', '-p'] in cmds


def test_rollback_keeps_single_config_line(env):
    """反复加固/还原后, 配置项始终只有一行, 且不残留旧写法"""
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    obj.fix()
    obj.rollback()
    content = open(conf, encoding='utf-8').read()
    assert content.count('icmp_echo_ignore_all') == 1
    assert RECOVERY + '\n' in content
    assert obj.check() is False


def test_reset(env):
    obj, conf, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['120', 'status'] == 2


def test_get_des(env):
    obj, conf, pkl, cmds = env
    assert obj.get_des() == obj.config['description']

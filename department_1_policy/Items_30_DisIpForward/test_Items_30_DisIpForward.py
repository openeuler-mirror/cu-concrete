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
import Items_30_DisIpForward as mod
from Items_30_DisIpForward import Items_30_DisIpForward

yaml_path = os.path.join(item_dir, 'Items_30_DisIpForward.yaml')
STANDARD = 'net.ipv4.ip_forward=0'
RECOVERY = 'net.ipv4.ip_forward=1'


def posix_to_py(form):
    """把 grep -E / sed 的 POSIX 字符类转成 python re 写法"""
    return form.replace('[[:space:]]', '[ \\t]').replace('\\+', '+')


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 sysctl.conf 与 pkl, 并用 python 实现替换 bsf 的 shell 调用"""
    conf = tmp_path / 'sysctl.conf'
    conf.write_text('# /etc/sysctl.conf\n'
                    'net.ipv4.ip_forward=1\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    pd.DataFrame(columns=['status', 'module_name', 'module_path']).to_pickle(pkl)
    cmds = []

    def fake_remove_line(pattern, path):
        # sed -i /{pattern}/d
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(posix_to_py(pattern))
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

    def fake_grep_shell(form, path):
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(posix_to_py(form))
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if regex.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)
    monkeypatch.setattr(mod.bsf, 'append_line', fake_append_line)
    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep_shell)
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_30_DisIpForward()
    obj.config_file = yaml_path
    obj.pkl_file = str(pkl)
    obj.current_dir = str(tmp_path)
    obj.config['query']['path'] = str(conf)
    obj.status_form = pd.read_pickle(pkl)
    return obj, str(conf), str(pkl), cmds


def read_conf(conf):
    return open(conf, encoding='utf-8').read()


def test_init(env):
    obj, conf, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 30
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix(env):
    obj, conf, pkl, cmds = env
    obj.finalfix()
    assert pd.read_pickle(pkl).loc['130', 'status'] == 2


def test_check_before_fix(env):
    # 原值是 =1, 判定为未加固
    obj, conf, pkl, cmds = env
    assert obj.check() is False


def test_fix(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    content = read_conf(conf)
    assert STANDARD in content
    assert 'net.ipv4.ip_forward=1' not in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['130', 'status'] == 2
    # 配置立即生效
    assert ['sysctl', '-p'] in cmds


def test_fix_no_backup_file(env):
    # 不再生成备份文件
    obj, conf, pkl, cmds = env
    obj.fix()
    assert not os.path.exists(conf + '_bak')
    assert not os.path.exists(conf + '.bak')


def test_fix_is_idempotent(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.fix()
    lines = [l for l in read_conf(conf).splitlines() if 'ip_forward' in l]
    assert lines == [STANDARD]
    assert obj.check() is True


def test_fix_appends_on_new_line_when_no_trailing_newline(env):
    # 文件末尾没有换行时, 追加的配置另起一行, 不会粘到上一行末尾
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# /etc/sysctl.conf')
    obj.fix()
    content = read_conf(conf)
    assert content.endswith(STANDARD + '\n')
    assert '# /etc/sysctl.conf\n' + STANDARD in content
    assert obj.check() is True


def test_fix_keeps_commented_line(env):
    # 注释行不参与匹配, 不会被清理掉
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# /etc/sysctl.conf\n#net.ipv4.ip_forward=1\n')
    obj.fix()
    content = read_conf(conf)
    assert '#net.ipv4.ip_forward=1' in content
    assert STANDARD in content
    assert obj.check() is True


def test_check_value_not_zero(env):
    # 存在 ip_forward 配置但值不为 0 -> 未加固
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('net.ipv4.ip_forward=1\n')
    assert obj.check() is False


def test_check_no_config(env):
    # 完全没有 ip_forward 配置 -> 未加固
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# /etc/sysctl.conf\n')
    assert obj.check() is False


def test_check_commented_line(env):
    # 注释行不算有效配置 -> 未加固
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('#net.ipv4.ip_forward=0\n')
    assert obj.check() is False


def test_check_value_with_spaces(env):
    # 带空格的写法也能识别出值
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('net.ipv4.ip_forward = 0\n')
    assert obj.check() is True


def test_rollback(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    content = read_conf(conf)
    # 还原不是删除配置行, 而是显式写回 1, 配置项始终保留在配置文件中
    assert RECOVERY + '\n' in content
    assert 'net.ipv4.ip_forward=0' not in content
    # 取值为 1 -> 判未加固
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['130', 'status'] == 0
    # sysctl -p 刷新, 内核运行时值与配置文件一致(恢复 IP 转发)
    assert ['sysctl', '-p'] in cmds


def test_rollback_keeps_single_config_line(env):
    """反复加固/还原后, 配置项始终只有一行"""
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    obj.fix()
    obj.rollback()
    lines = [l for l in read_conf(conf).splitlines() if 'ip_forward' in l]
    assert lines == [RECOVERY]
    assert obj.check() is False


def test_reset(env):
    obj, conf, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['130', 'status'] == 2


def test_get_des(env):
    obj, conf, pkl, cmds = env
    assert obj.get_des() == obj.config['description']

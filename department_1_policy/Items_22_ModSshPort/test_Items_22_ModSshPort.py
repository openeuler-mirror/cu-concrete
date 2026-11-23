import os
import re
import sys
import pytest
import yaml

item_dir = os.path.dirname(os.path.abspath(__file__))
dep_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(dep_dir)
for _p in (item_dir, dep_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import Panda as pd
import Items_22_ModSshPort as mod
from Items_22_ModSshPort import Items_22_ModSshPort

yaml_path = os.path.join(item_dir, 'Items_22_ModSshPort.yaml')
STANDARD = 'Port 10022'
ORIGINAL = 'Port 22'


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 sshd_config 与 pkl, 并拦截 base_shell(防火墙/systemctl 命令)"""
    conf = tmp_path / 'sshd_config'
    conf.write_text('# sshd 配置\n'
                    'Port 22\n'
                    'PermitRootLogin no\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    pd.DataFrame(columns=['status', 'module_name', 'module_path']).to_pickle(pkl)
    cmds = []

    def fake_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_22_ModSshPort()
    obj.config_file = yaml_path
    with open(yaml_path, encoding='utf-8') as f:
        obj.config = yaml.safe_load(f)
    obj.config['query']['path'] = [str(conf)]
    obj.pkl_file = str(pkl)
    obj.current_dir = str(tmp_path)
    obj.status_form = pd.read_pickle(pkl)
    return obj, str(conf), str(pkl), cmds


def active_ports(content):
    """取出内容中所有未注释的 Port 指令行"""
    return [l for l in content.splitlines() if re.match(r'^[ \t]*Port[ \t]+[0-9]+', l)]


def test_init(env):
    obj, conf, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 22
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix(env):
    obj, conf, pkl, cmds = env
    obj.finalfix()
    assert pd.read_pickle(pkl).loc['122', 'status'] == 2


def test_check_before_fix(env):
    obj, conf, pkl, cmds = env
    assert obj.check() is False


def test_fix(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    content = open(conf, encoding='utf-8').read()
    assert STANDARD in content
    assert 'Port 22\n' not in content
    # 只保留一行有效的 Port 声明
    assert active_ports(content) == [STANDARD]
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['122', 'status'] == 2


def test_fix_appends_when_no_port_line(env):
    """改进2: 文件里没有 Port 声明时追加标准行, 且不清空原有内容"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# sshd 配置\nPermitRootLogin no\n')
    obj.fix()
    lines = open(conf, encoding='utf-8').read().splitlines()
    assert STANDARD in lines
    assert '# sshd 配置' in lines
    assert 'PermitRootLogin no' in lines
    assert len(lines) == 3
    assert obj.check() is True


def test_fix_activates_commented_port(env):
    """注释形式的 Port 声明(RHEL 默认)不生效, 加固后追加一行标准行"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('#Port 22\nPermitRootLogin no\n')
    obj.fix()
    lines = open(conf, encoding='utf-8').read().splitlines()
    assert STANDARD in lines
    assert '#Port 22' in lines
    # 生效中的端口声明只有一行
    assert active_ports('\n'.join(lines)) == [STANDARD]
    assert obj.check() is True


def test_fix_comments_out_extra_active_ports(env):
    """多条有效 Port 声明时只保留一行有效, 其余注释掉"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('Port 22\nPort 2222\nPermitRootLogin no\n')
    obj.fix()
    lines = open(conf, encoding='utf-8').read().splitlines()
    assert active_ports('\n'.join(lines)) == [STANDARD]
    assert '#Port 2222' in lines
    assert obj.check() is True


def test_fix_keeps_commented_extra_port(env):
    """有效行与注释行同时存在时: 有效行被改写, 注释行保持原样"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('Port 22\n#Port 22\nPermitRootLogin no\n')
    obj.fix()
    lines = open(conf, encoding='utf-8').read().splitlines()
    assert active_ports('\n'.join(lines)) == [STANDARD]
    assert '#Port 22' in lines
    assert obj.check() is True


def test_fix_opens_firewall_port(env):
    """改进1: 加固时防火墙放行 10022"""
    obj, conf, pkl, cmds = env
    obj.fix()
    flat = [' '.join(c) for c in cmds]
    assert any('--add-port=10022/tcp' in c for c in flat)
    assert any('--reload' in c for c in flat)
    assert any(c.startswith('systemctl restart') for c in flat)


def test_fix_closes_old_firewall_port(env):
    """加固时放行 10022 的同时关闭 22 端口"""
    obj, conf, pkl, cmds = env
    obj.fix()
    flat = [' '.join(c) for c in cmds]
    assert any('--add-port=10022/tcp' in c for c in flat)
    assert any('--remove-port=22/tcp' in c for c in flat)
    # 不再放行旧端口, 也不关闭新端口
    assert not any('--add-port=22/tcp' in c for c in flat)
    assert not any('--remove-port=10022/tcp' in c for c in flat)


def test_fix_closes_old_port_after_sshd_restart(env):
    """关闭原端口必须在 sshd 重启生效之后执行, 避免重启失败时断连"""
    obj, conf, pkl, cmds = env
    obj.fix()
    idx_restart = next(i for i, c in enumerate(cmds) if c[:2] == ['systemctl', 'restart'])
    idx_close = next(i for i, c in enumerate(cmds) if '--remove-port=22/tcp' in ' '.join(c))
    assert idx_close > idx_restart


def test_fix_keeps_old_port_when_sshd_restart_failed(env, monkeypatch):
    """sshd 重启失败时不关闭原端口, 避免远程无法连接"""
    obj, conf, pkl, cmds = env

    def failed_base_shell(command, **kwargs):
        cmds.append(list(command))
        return ('', 1)

    monkeypatch.setattr(mod, 'base_shell', failed_base_shell)
    obj.fix()
    flat = [' '.join(c) for c in cmds]
    assert not any('--remove-port=22/tcp' in c for c in flat)


def test_fix_appends_on_new_line_when_no_trailing_newline(env):
    """文件末尾没有换行时, 改写/追加的配置另起一行, 不会粘到上一行末尾"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# sshd 配置\nPort 22')          # 末尾无换行
    obj.fix()
    content = open(conf, encoding='utf-8').read()
    assert content == '# sshd 配置\nPort 10022\n'


def test_fix_appends_new_line_when_no_port_and_no_trailing_newline(env):
    """没有 Port 声明且末尾无换行时, 追加的配置另起一行"""
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('# sshd 配置\nPermitRootLogin no')  # 末尾无换行, 也没有 Port 声明
    obj.fix()
    content = open(conf, encoding='utf-8').read()
    assert content == '# sshd 配置\nPermitRootLogin no\nPort 10022\n'
    assert obj.check() is True


def test_check_after_fix(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    assert obj.check() is True


def test_check_false_when_extra_port_active(env):
    """除目标端口外还有其它生效端口时, 判未加固"""
    obj, conf, pkl, cmds = env
    obj.fix()
    with open(conf, 'a', encoding='utf-8') as f:
        f.write('Port 22\n')
    assert obj.check() is False


def test_rollback(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    content = open(conf, encoding='utf-8').read()
    assert ORIGINAL in content
    assert STANDARD not in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['122', 'status'] == 0


def test_rollback_opens_original_firewall_port(env):
    """还原时放行 22 端口, 同时关闭 10022 端口"""
    obj, conf, pkl, cmds = env
    obj.fix()
    cmds.clear()
    obj.rollback()
    flat = [' '.join(c) for c in cmds]
    assert any('--add-port=22/tcp' in c for c in flat)
    assert any('--remove-port=10022/tcp' in c for c in flat)
    assert any('--reload' in c for c in flat)
    # 不再放行新端口, 也不关闭原端口
    assert not any('--add-port=10022/tcp' in c for c in flat)
    assert not any('--remove-port=22/tcp' in c for c in flat)


def test_rollback_closes_new_port_after_sshd_restart(env):
    """关闭新端口必须在 sshd 重启生效之后执行"""
    obj, conf, pkl, cmds = env
    obj.fix()
    cmds.clear()
    obj.rollback()
    idx_restart = next(i for i, c in enumerate(cmds) if c[:2] == ['systemctl', 'restart'])
    idx_close = next(i for i, c in enumerate(cmds) if '--remove-port=10022/tcp' in ' '.join(c))
    assert idx_close > idx_restart


def test_reset(env):
    obj, conf, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['122', 'status'] == 2


def test_get_des(env):
    obj, conf, pkl, cmds = env
    assert obj.get_des() == obj.config['description']

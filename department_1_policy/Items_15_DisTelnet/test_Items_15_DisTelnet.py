import os
import pytest
import pandas as pd
import Items_15_DisTelnet as mod
from Items_15_DisTelnet import Items_15_DisTelnet

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_15_DisTelnet.yaml')
pkl_path = '/tmp/test_data_status.pkl'
telnet_conf_path = '/tmp/test_telnet'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(telnet_conf_path, 'w') as f:
        f.write('# telnet xinetd 配置\n'
                'disable = no\n'
                'server_args = -debug\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [telnet_conf_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_15_DisTelnet()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 15,
        'query': {'form': '^disable', 'path': telnet_conf_path},
        'change': {
            'value': [
                'disable = yes',
                'openssh*',
                # 真实加固用 systemctl; 测试里换成 echo, 避免真的启停 telnet/sshd 服务
                'echo systemctl disable telnet.socket',
                'echo systemctl stop telnet.socket',
                'echo systemctl enable telnet.socket',
                'echo systemctl start telnet.socket',
                'echo systemctl enable sshd',
                'echo systemctl start sshd',
                'echo systemctl disable sshd',
                'echo systemctl stop sshd'
            ]
        },
        'description': '关闭telent,使用openssh'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(commands):
    """替换模块里的 base_shell: 记录命令但不真的执行 systemctl / yum"""
    def _call(command, **kwargs):
        commands.append(list(command))
        cmd = list(command)
        if cmd[0] == 'systemctl' and 'is-active' in cmd:
            return ('inactive', 0)
        if cmd[0] == 'rpm':
            return ('openssh-server-8.0p1', 0)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 15
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['115', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['115', 'status'] == 2
    # telnet 服务被禁用
    content = open(telnet_conf_path).read()
    assert 'disable = yes' in content
    assert 'disable = no' not in content
    # systemctl 命令已下发(被 echo 替换, 不会真的动服务)
    assert cmds


def test_check(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['115', 'status'] == 0
    assert 'disable = no' in open(telnet_conf_path).read()


def test_reset(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['115', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '关闭telent,使用openssh'

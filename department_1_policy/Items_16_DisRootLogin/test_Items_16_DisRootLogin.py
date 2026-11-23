import os
import pytest
import pandas as pd
import Items_16_DisRootLogin as mod
from Items_16_DisRootLogin import Items_16_DisRootLogin

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_16_DisRootLogin.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sshd_config_path = '/tmp/test_sshd_config'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(sshd_config_path, 'w') as f:
        f.write('# sshd 配置\n'
                'PermitRootLogin yes\n'
                'Port 22\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [sshd_config_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_16_DisRootLogin()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 16,
        'query': {'form': '^PermitRootLogin', 'path': sshd_config_path},
        'change': {
            'value': [
                'PermitRootLogin no',
                # 真实加固用 systemctl restart sshd; 测试里换成 echo, 避免真的重启 sshd
                'echo restart sshd',
                'PermitRootLogin yes'
            ]
        },
        'description': '禁止root账户ssh登录'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(commands):
    """替换模块里的 base_shell: 记录命令但不真的重启 sshd"""
    def _call(command, **kwargs):
        commands.append(list(command))
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 16
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['116', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['116', 'status'] == 2
    content = open(sshd_config_path).read()
    assert 'PermitRootLogin no' in content
    assert 'PermitRootLogin yes' not in content
    # 重启命令已下发(被 echo 替换)
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
    assert pd.read_pickle(pkl_path).loc['116', 'status'] == 0
    assert 'PermitRootLogin yes' in open(sshd_config_path).read()


def test_reset(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['116', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '禁止root账户ssh登录'

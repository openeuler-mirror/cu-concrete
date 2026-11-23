import os
import pytest
import pandas as pd
import Items_25_DelBashHistory as mod
from Items_25_DelBashHistory import Items_25_DelBashHistory

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_25_DelBashHistory.yaml')
pkl_path = '/tmp/test_data_status.pkl'
history_path = '/tmp/test_bash_history'
history_bak_path = '/tmp/test_bash_history_bak'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(history_path, 'w') as f:
        f.write('ls -al\nrm -rf /tmp/x\nwhoami\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [history_path, history_bak_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_25_DelBashHistory()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 25,
        'query': {'path': history_path, 'path1': history_bak_path},
        'description': '删除历史命令行记录'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def fake_base_shell(commands):
    """替换模块里的 base_shell:
    - wc: 返回真实字节数, 格式与 GNU wc 一致("<字节数> <文件>")
    - rm / touch: 只允许操作 /tmp 下的假文件, 使 fix 的"清空历史"效果可被断言
    - bash -c history -c: 拦截不执行
    """
    def _call(command, **kwargs):
        cmd = list(command)
        commands.append(cmd)
        if cmd[0] == 'wc':
            path = cmd[-1]
            size = os.path.getsize(path) if os.path.exists(path) else 0
            return ('%d %s' % (size, path), 0)
        if cmd[0] == 'rm':
            target = cmd[-1]
            if target.startswith('/tmp/') and os.path.exists(target):
                os.remove(target)
            return ('', 0)
        if cmd[0] == 'touch':
            target = cmd[-1]
            if target.startswith('/tmp/'):
                open(target, 'a').close()
            return ('', 0)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 25
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['125', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['125', 'status'] == 2
    # 备份已生成, 清空命令已下发
    assert os.path.exists(history_bak_path)
    assert any(c[0] == 'rm' for c in cmds)
    assert any(c[0] == 'touch' for c in cmds)
    # 历史文件已被清空
    assert os.path.getsize(history_path) == 0


def test_fix_keeps_original_backup(monkeypatch):
    """重复加固不应覆盖原始备份, 否则 rollback 还原不回原始历史记录"""
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    obj.fix()
    assert 'ls -al' in open(history_bak_path).read()


def test_check(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    # 未加固: 历史文件仍有内容 -> 判定为不合规
    assert obj.check() is False
    # 加固后历史文件被清空 -> 判定为合规
    obj.fix()
    assert obj.check() is True


def test_check_follows_config_path(monkeypatch):
    """check 只比较字节数, 不再硬编码 /root/.bash_history"""
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    other_path = '/tmp/test_bash_history_other'
    try:
        obj.config['query']['path'] = other_path
        with open(other_path, 'w') as f:
            f.write('some history\n')
        # 目标文件非空 -> 不合规
        assert obj.check() is False
        with open(other_path, 'w') as f:
            f.write('')
        # 目标文件为空 -> 合规, 与具体路径无关
        assert obj.check() is True
    finally:
        if os.path.exists(other_path):
            os.remove(other_path)


def test_rollback(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['125', 'status'] == 0
    # 还原后历史记录重新出现
    assert 'ls -al' in open(history_path).read()


def test_reset(monkeypatch):
    obj = build_instance()
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', fake_base_shell(cmds))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['125', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '删除历史命令行记录'

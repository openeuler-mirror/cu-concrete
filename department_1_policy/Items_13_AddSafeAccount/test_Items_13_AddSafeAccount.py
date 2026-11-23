import os
import pytest
import pandas as pd
import Items_13_AddSafeAccount as mod
from Items_13_AddSafeAccount import Items_13_AddSafeAccount

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_13_AddSafeAccount.yaml')
pkl_path = '/tmp/test_data_status.pkl'
sudoers_path = '/tmp/test_sudoers'
home_path = '/tmp/test_safe_account'
ssh_dir = '/tmp/test_safe_account/.ssh'
auth_keys_src = '/tmp/test_authorized_keys'
auth_keys_dst = '/tmp/test_safe_account/.ssh/authorized_keys'
id_rsa_src = '/tmp/test_id_rsa'
id_rsa_dst = '/tmp/test_safe_account/.ssh/id_rsa'
id_dsa_src = '/tmp/test_id_dsa'
id_dsa_dst = '/tmp/test_safe_account/.ssh/id_dsa'
# 虚构账号名, 测试里用 fake base_shell 拦截, 不会真的创建/删除系统账号
ACCOUNT = 'test_safe_account'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(sudoers_path, 'w') as f:
        f.write('root ALL=(ALL) ALL\n')
    for p in (auth_keys_src, id_rsa_src, id_dsa_src):
        with open(p, 'w') as f:
            f.write('dummy key content\n')
    if not os.path.isdir(ssh_dir):
        os.makedirs(ssh_dir)
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [sudoers_path, auth_keys_src, id_rsa_src, id_dsa_src, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)
    if os.path.isdir(home_path):
        for root, dirs, files in os.walk(home_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(home_path)


def build_instance():
    obj = Items_13_AddSafeAccount()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 13,
        'query': {
            'form': ACCOUNT,
            'path': sudoers_path,
            'path2': auth_keys_src,
            'path3': id_rsa_src,
            'path4': id_dsa_src
        },
        'change': {
            'value1': 'root@userpass',
            'value2': '%s    ALL=(ALL)    NOPASSWD: ALL' % ACCOUNT,
            'value3': ['700', '644', '600'],
            'path': home_path,
            'path1': ssh_dir,
            'path2': auth_keys_dst,
            'path3': id_rsa_dst,
            'path4': id_dsa_dst
        },
        'description': '添加用于安全管理的账户'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def make_fake(state, commands):
    """替换模块里的 base_shell: 拦截 useradd/userdel/chown/chattr/rm,
    避免真的创建删除系统账号; mkdir 放行(只作用于 /tmp 假目录)"""
    def _call(command, **kwargs):
        cmd = list(command)
        commands.append(cmd)
        if cmd[0] == 'id':
            return ('uid=1001(test) gid=1001(test) groups=1001(test)', 0) \
                if state['user_exists'] else ('', 1)
        if cmd[0] == 'lsattr':
            return ('--------------e------- /etc/passwd', 0)
        if cmd[0] == 'mkdir':
            if not os.path.isdir(cmd[-1]):
                os.makedirs(cmd[-1])
            return ('', 0)
        if cmd[0] in ('useradd', 'userdel', 'chown', 'chattr', 'rm'):
            return ('', 0)
        return ('', 0)
    return _call


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 13
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['113', 'status'] == 2


def test_fix(monkeypatch):
    obj = build_instance()
    state = {'user_exists': True}
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', make_fake(state, cmds))
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['113', 'status'] == 2
    # sudoers 里追加了授权规则
    assert ACCOUNT in open(sudoers_path).read()
    # 密钥文件被复制到 .ssh 下
    assert os.path.exists(auth_keys_dst)
    assert os.path.exists(id_rsa_dst)
    assert os.path.exists(id_dsa_dst)
    # 账号已存在, 不会执行 useradd
    assert not any(c[0] == 'useradd' for c in cmds)


def test_check(monkeypatch):
    obj = build_instance()
    state = {'user_exists': True}
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', make_fake(state, cmds))
    assert obj.check() is True
    state['user_exists'] = False
    assert obj.check() is False


def test_rollback(monkeypatch):
    obj = build_instance()
    state = {'user_exists': True}
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', make_fake(state, cmds))
    obj.fix()
    state['user_exists'] = False
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['113', 'status'] == 0
    # 账号被删除(被 fake 拦截, 不会真删系统账号)
    assert any(c[0] == 'userdel' for c in cmds)
    # sudoers 里的授权规则被移除
    assert ACCOUNT not in open(sudoers_path).read()


def test_reset(monkeypatch):
    obj = build_instance()
    state = {'user_exists': True}
    cmds = []
    monkeypatch.setattr(mod, 'base_shell', make_fake(state, cmds))
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['113', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '添加用于安全管理的账户'

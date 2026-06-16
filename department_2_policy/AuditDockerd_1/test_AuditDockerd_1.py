import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import Panda as pd
import pytest
import importlib.util

# helper to load the module from its file location so we can monkeypatch its `bsf`
def load_module():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    module_path = os.path.join(base_dir, 'AuditDockerd_1.py')
    spec = importlib.util.spec_from_file_location('AuditDockerd_1_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

yaml_path = os.path.join(os.path.dirname(__file__), 'AuditDockerd_1.yaml')
pkl_path = '/tmp/test_data_status_auditdockerd.pkl'
file_dockerd = '/tmp/test_usr_bin_dockerd'
rule_file = '/tmp/test_01-docker.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_usr_bin_dockerd_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    # 复制真实 yaml 文件到 /tmp 以便模块或测试可访问（如果存在）
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditDockerd_1.yaml')
    # 创建占位文件，避免操作真实系统路径
    for fp in [file_dockerd, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    # 清理
    for fp in [pkl_path, '/tmp/AuditDockerd_1.yaml', file_dockerd, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    mod = load_module()
    cls = mod.AuditDockerd_1
    obj = cls()
    # 将实例的文件路径和配置替换为测试用临时文件，避免真实系统调用
    obj.config_file = '/tmp/AuditDockerd_1.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    # 构造测试配置（与原 YAML 结构一致）
    obj.config = {
        'dep': 2,
        'id': 1,
        'query': {
            'path': [file_dockerd, rule_file, auditctl],
            'form': '-w /usr/bin/dockerd -k docker'
        },
        'change': {
            'set': 'auditctl',
            'value': "'^[^#;]'"
        },
        'backup_path': backup_path,
        'description': '确保为 Docker 守护进程配置审计功能（自动）'
    }
    # 加载或初始化 status_form
    obj.status_form = pd.read_pickle(pkl_path)
    return mod, obj


def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 1
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    # key 为 dep+id，例如 '21'
    assert status_df.loc['21', 'status'] == 2


def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    # monkeypatch reload_audit_rules to be a no-op
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.fix()
    # 检查规则文件已被写入正确内容
    with open(rule_file, 'r') as f:
        content = f.read()
    assert content == obj.config['query']['form']
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['21', 'status'] == 2


def test_check_command_search_branch(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            # simulate non-empty result matching form
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            # simulate search returning (None, 0)
            return (None, 0)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is True


def test_check_pipe_grep_branch(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            return (form, 0)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is True


def test_rollback_updates_status_when_check_fails(monkeypatch):
    mod, obj = build_instance()
    # ensure the rule file exists so remove_file can remove it
    with open(obj.config['query']['path'][1], 'w') as f:
        f.write(obj.config['query']['form'])

    # Fake remove_file to actually remove the test file
    def fake_remove(path):
        if os.path.exists(path):
            os.remove(path)

    # fake reload and make check return False afterwards
    class FakeBSF:
        @staticmethod
        def remove_file(path):
            fake_remove(path)

        @staticmethod
        def reload_audit_rules():
            return None

        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            # simulate not found -> non-zero exit code
            return ('', 1)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)

    # set status to 1 then call rollback
    obj.status_form.loc['21', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)

    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['21', 'status'] == 0


def test_reset(monkeypatch):
    mod, obj = build_instance()
    # make reload a no-op to avoid external side-effects
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['21', 'status'] == 2


def test_get_des():
    _, obj = build_instance()
    des = obj.get_des()
    assert des == '确保为 Docker 守护进程配置审计功能（自动）'

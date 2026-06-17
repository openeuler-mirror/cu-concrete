import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import Panda as pd
import yaml
import pytest
import importlib.util

# helper to load the module from its file location so we can monkeypatch its `bsf`
def load_module():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    module_path = os.path.join(base_dir, 'AuditEtc_4.py')
    spec = importlib.util.spec_from_file_location('AuditEtc_4_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

yaml_path = os.path.join(os.path.dirname(__file__), 'AuditEtc_4.yaml')
pkl_path = '/tmp/test_data_status_auditetc.pkl'
file_etc = '/tmp/test_etc_file'
rule_file = '/tmp/test_04-etc.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_etc_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    # 复制真实 yaml 文件到 /tmp（如果存在）以便模块或测试可访问
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditEtc_4.yaml')
    # 创建占位文件，避免操作真实系统路径
    for fp in [file_etc, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    # 清理
    for fp in [pkl_path, '/tmp/AuditEtc_4.yaml', file_etc, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    mod = load_module()
    # 源文件中类名为 AuditDockerd_1（不一致），测试中按该名字获取
    cls = getattr(mod, 'AuditDockerd_1')
    obj = cls()
    # 将实例的文件路径和配置替换为测试用临时文件，避免真实系统调用
    obj.config_file = '/tmp/AuditEtc_4.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    # 优先使用真实 yaml 中的配置（如果存在），否则使用测试虚拟配置
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_cfg = yaml.load(f, Loader=yaml.Loader)
        # 使用 yaml 的配置，但把路径替换为测试用的 /tmp 占位路径以避免修改系统文件
        # 保持 yaml 中的 form 与 change/description 等字段
        obj.config = yaml_cfg
        # 如果 yaml 中存在 query.path，用测试路径替换其中的条目以保证可写性
        if 'query' in obj.config and 'path' in obj.config['query']:
            # 尽量保留原 path 的长度并替换为测试文件路径
            orig_paths = obj.config['query']['path']
            new_paths = []
            for i, _ in enumerate(orig_paths):
                if i == 0:
                    new_paths.append(file_etc)
                elif i == 1:
                    new_paths.append(rule_file)
                elif i == 2:
                    new_paths.append(auditctl)
                else:
                    new_paths.append(orig_paths[i])
            obj.config['query']['path'] = new_paths
        # 替换 backup_path 为测试路径
        obj.config['backup_path'] = backup_path
    else:
        # 构造测试配置（与模块期望的结构一致）
        obj.config = {
            'dep': 2,
            'id': 4,
            'query': {
                'path': [file_etc, rule_file, auditctl],
                'form': '-w /etc -k etc'
            },
            'change': {
                'set': 'auditctl',
                'value': "'^[^#;]'"
            },
            'backup_path': backup_path,
            'description': '确保为 /etc 配置审计功能（自动)'
        }
    # 加载或初始化 status_form
    obj.status_form = pd.read_pickle(pkl_path)
    return mod, obj


def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 4
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    # key 为 dep+id，例如 '24'
    assert status_df.loc['24', 'status'] == 2

# 测试 fix 方法是否正确写入规则文件并更新状态,用mock把reload_audit_rules替换掉，不更新规则.
def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.fix()
    with open(rule_file, 'r') as f:
        content = f.read()
    assert content == obj.config['query']['form']
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['24', 'status'] == 2

# 测试check方法是否能够满足正常的输入输出,但替换掉command_search和search_audit_rule方法.
def test_check_command_search_branch(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            return (None, 0)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is True


def test_check_command_search_branch_not_present(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            return (None, 1)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is False


def test_check_pipe_grep_branch(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            return ('', 0)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is True


def test_check_pipe_grep_branch_not_found(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:
        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            return ('', 2)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    assert obj.check() is False


def test_rollback_updates_status_when_check_fails(monkeypatch):
    mod, obj = build_instance()
    # ensure the rule file exists so remove_file can remove it
    with open(obj.config['query']['path'][1], 'w') as f:
        f.write(obj.config['query']['form'])

    def fake_remove(path):
        if os.path.exists(path):
            os.remove(path)

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
            return ('', 1)

    monkeypatch.setattr(mod, 'bsf', FakeBSF)

    obj.status_form.loc['24', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)

    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['24', 'status'] == 0


def test_reset(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['24', 'status'] == 2


def test_get_des():
    _, obj = build_instance()
    des = obj.get_des()
    # use the instance config description so tests follow the YAML (if present) or the test config
    assert des == obj.config['description']

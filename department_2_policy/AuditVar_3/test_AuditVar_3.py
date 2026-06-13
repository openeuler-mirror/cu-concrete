import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import Panda as pd
import pytest
import importlib.util

def load_module():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    module_path = os.path.join(base_dir, 'AuditVar_3.py')
    spec = importlib.util.spec_from_file_location('AuditVar_3_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'AuditVar_3.yaml')
pkl_path = '/tmp/test_data_status_auditvar.pkl'
file_var = '/tmp/test_var_file'
rule_file = '/tmp/test_03-var.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_var_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditVar_3.yaml')
    for fp in [file_var, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditVar_3.yaml', file_var, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'AuditDockerd_1')
    obj = cls()
    obj.config_file = '/tmp/AuditVar_3.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 2, 'id': 3, 'query': {'path': [file_var, rule_file, auditctl], 'form': '-w /var -k var'}, 'change': {'set': 'auditctl', 'value': "'^[^#;]'"}, 'backup_path': backup_path, 'description': '确保审计可变数据（自动）'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 3
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['23', 'status'] == 2

def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.fix()
    with open(rule_file, 'r') as f:
        content = f.read()
    assert content == obj.config['query']['form']
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['23', 'status'] == 2

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

    class FakeBSF:

        @staticmethod
        def command_search(arg):
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            return (None, 1)
    form = obj.config['query']['form']
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
    with open(obj.config['query']['path'][1], 'w') as f:
        f.write(obj.config['query']['form'])

    def fake_remove(path):
        pass

    class FakeBSF:

        @staticmethod
        def remove_file(path):
            pass

        @staticmethod
        def reload_audit_rules():
            pass

        @staticmethod
        def command_search(arg):
            pass

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            pass
    monkeypatch.setattr(mod, 'bsf', FakeBSF)

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
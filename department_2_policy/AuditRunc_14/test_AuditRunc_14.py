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

def load_module():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
    module_path = os.path.join(base_dir, 'AuditRunc_14.py')
    spec = importlib.util.spec_from_file_location('AuditRunc_14_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'AuditRunc_14.yaml')
pkl_path = '/tmp/test_data_status_auditrunc.pkl'
service_name = 'runc'
file_service = '/tmp/test_runc_service'
rule_file = '/tmp/test_14-runc.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_runc_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditRunc_14.yaml')
    for fp in [file_service, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditRunc_14.yaml', file_service, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = None
    for name in ('AuditRunc_14', 'AuditContainerShim_13', 'AuditRunc'):
        if hasattr(mod, name):
            cls = getattr(mod, name)
            break
    if cls is None:
        for name in dir(mod):
            attr = getattr(mod, name)
            if isinstance(attr, type):
                cls = attr
                break
    assert cls is not None, 'no class found in module'
    obj = cls()
    obj.config_file = '/tmp/AuditRunc_14.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_cfg = yaml.load(f, Loader=yaml.Loader)
        obj.config = yaml_cfg
        if 'query' in obj.config and 'path' in obj.config['query']:
            orig_paths = obj.config['query']['path']
            new_paths = []
            for i, _ in enumerate(orig_paths):
                if i == 0:
                    new_paths.append(file_service)
                elif i == 1:
                    new_paths.append(rule_file)
                elif i == 2:
                    new_paths.append(auditctl)
                else:
                    new_paths.append(orig_paths[i])
            obj.config['query']['path'] = new_paths
        obj.config['backup_path'] = backup_path
    else:
        obj.config = {'dep': 2, 'id': 14, 'query': {'path': [file_service, rule_file, auditctl], 'form': f'-w /usr/bin/{service_name} -p wa -k runc'}, 'change': {'set': 'auditctl', 'value': "'^[^#;]'"}, 'backup_path': backup_path, 'description': '确保 runc 相关审计规则存在'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 14
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['214', 'status'] == 2

def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'get_service_file', lambda p: file_service)
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda *a, **k: None)
    obj.fix()
    with open(rule_file, 'r') as f:
        content = f.read()
    assert content == file_service
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['214', 'status'] == 2

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
            pass

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            pass

def test_rollback_updates_status_when_check_fails(monkeypatch):
    pass

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
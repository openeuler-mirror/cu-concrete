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
    module_path = os.path.join(base_dir, 'AuditService_5.py')
    spec = importlib.util.spec_from_file_location('AuditService_5_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'AuditService_5.yaml')
pkl_path = '/tmp/test_data_status_auditservice.pkl'
service_name = 'docker'
file_service = '/tmp/test_service_file'
rule_file = '/tmp/test_05-service.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_service_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditService_5.yaml')
    for fp in [file_service, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditService_5.yaml', file_service, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'AuditService_5')
    obj = cls()
    obj.config_file = '/tmp/AuditService_5.yaml'
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
                else:
                    new_paths.append(orig_paths[i])
            obj.config['query']['path'] = new_paths
        obj.config['backup_path'] = backup_path
    else:
        obj.config = {'dep': 2, 'id': 5, 'query': {'path': [service_name, rule_file], 'form': f'-w /usr/bin/{service_name} -p wa -k docker'}, 'change': {'set': 'auditctl', 'value': "'^[^#;]'"}, 'backup_path': backup_path, 'description': '为 Docker 相关文件进程配置审计功能- docker.service'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 5
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['25', 'status'] == 2

def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'get_service_file', lambda p: file_service)
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.fix()
    with open(rule_file, 'r') as f:
        content = f.read()
    assert f'-w {file_service}' in content
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['25', 'status'] == 2

def test_check_and_rollback(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:

        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            return ('', 1)

        @staticmethod
        def get_service_file(p):
            return file_service

        @staticmethod
        def remove_file(path):
            if os.path.exists(path):
                os.remove(path)

        @staticmethod
        def reload_audit_rules():
            return None
    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    with open(obj.config['query']['path'][1], 'w') as f:
        f.write(obj.config['query']['form'])
    obj.status_form.loc['25', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['25', 'status'] == 0

def test_check_command_search_branch(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF2:

        @staticmethod
        def command_search(arg):
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            return (None, 0)
    monkeypatch.setattr(mod, 'bsf', FakeBSF2)
    assert obj.check() is True

def test_check_command_search_branch_not_present(monkeypatch):
    mod, obj = build_instance()
    form = obj.config['query']['form']

    class FakeBSF3:

        @staticmethod
        def command_search(arg):
            return (form,)

        @staticmethod
        def search_audit_rule(path):
            return (None, 1)
    monkeypatch.setattr(mod, 'bsf', FakeBSF3)
    assert obj.check() is False

def test_check_pipe_grep_branch(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF4:

        @staticmethod
        def command_search(arg):
            return ('',)

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            return ('', 0)
    monkeypatch.setattr(mod, 'bsf', FakeBSF4)
    assert obj.check() is True

def test_check_pipe_grep_branch_not_found(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF5:

        @staticmethod
        def command_search(arg):
            pass

        @staticmethod
        def pipe_grep_shell(form_arg, path, value):
            pass
    monkeypatch.setattr(mod, 'bsf', FakeBSF5)

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
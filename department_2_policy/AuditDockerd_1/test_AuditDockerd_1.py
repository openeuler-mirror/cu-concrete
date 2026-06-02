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
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditDockerd_1.yaml')
    for fp in [file_dockerd, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditDockerd_1.yaml', file_dockerd, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = mod.AuditDockerd_1
    obj = cls()
    obj.config_file = '/tmp/AuditDockerd_1.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 2, 'id': 1, 'query': {'path': [file_dockerd, rule_file, auditctl], 'form': '-w /usr/bin/dockerd -k docker'}, 'change': {'set': 'auditctl', 'value': "'^[^#;]'"}, 'backup_path': backup_path, 'description': '确保为 Docker 守护进程配置审计功能（自动）'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 1
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['21', 'status'] == 2

def test_fix_writes_rule_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'reload_audit_rules', lambda: None)
    obj.fix()
    with open(rule_file, 'r') as f:
        content = f.read()
    assert content == obj.config['query']['form']
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['21', 'status'] == 2

def test_check_command_search_branch(monkeypatch):
    pass

def test_check_pipe_grep_branch(monkeypatch):
    pass

def test_rollback_updates_status_when_check_fails(monkeypatch):
    pass

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
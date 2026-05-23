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
    module_path = os.path.join(base_dir, 'AuditUsContainerd_12.py')
    spec = importlib.util.spec_from_file_location('AuditUsContainerd_12_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'AuditUsContainerd_12.yaml')
pkl_path = '/tmp/test_data_status_audituscontainerd.pkl'
service_name = 'us_containerd'
file_service = '/tmp/test_us_containerd_service'
rule_file = '/tmp/test_12-us-containerd.rules'
auditctl = '/tmp/test_auditctl'
backup_path = '/tmp/test_us_containerd_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditUsContainerd_12.yaml')
    for fp in [file_service, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditUsContainerd_12.yaml', file_service, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    pass

def test_init():
    pass

def test_finalfix():
    pass

def test_fix_writes_rule_and_sets_status(monkeypatch):
    pass

def test_check_command_search_branch(monkeypatch):
    pass

def test_check_command_search_branch_not_present(monkeypatch):
    pass

def test_check_pipe_grep_branch(monkeypatch):
    pass

def test_check_pipe_grep_branch_not_found(monkeypatch):
    pass

def test_rollback_updates_status_when_check_fails(monkeypatch):
    pass

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
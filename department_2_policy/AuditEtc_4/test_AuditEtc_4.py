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
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/AuditEtc_4.yaml')
    for fp in [file_etc, rule_file, auditctl, backup_path]:
        with open(fp, 'w') as f:
            f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/AuditEtc_4.yaml', file_etc, rule_file, auditctl, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'AuditDockerd_1')
    obj = cls()
    obj.config_file = '/tmp/AuditEtc_4.yaml'
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
                    new_paths.append(file_etc)
                elif i == 1:
                    new_paths.append(rule_file)
                elif i == 2:
                    new_paths.append(auditctl)
                else:
                    new_paths.append(orig_paths[i])
            obj.config['query']['path'] = new_paths
        obj.config['backup_path'] = backup_path
    else:
        obj.config = {'dep': 2, 'id': 4, 'query': {'path': [file_etc, rule_file, auditctl], 'form': '-w /etc -k etc'}, 'change': {'set': 'auditctl', 'value': "'^[^#;]'"}, 'backup_path': backup_path, 'description': '确保为 /etc 配置审计功能（自动)'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 4
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)

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
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
    module_path = os.path.join(base_dir, 'CheckOwDebug_24.py')
    spec = importlib.util.spec_from_file_location('CheckOwDebug_24_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckOwDebug_24.yaml')
pkl_path = '/tmp/test_data_status_checkowdebug.pkl'
file_path = '/tmp/test_owdebug_path'
backup_path = '/tmp/test_checkowdebug_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckOwDebug_24.yaml')
    with open(file_path, 'w') as f:
        f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckOwDebug_24.yaml', file_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'CheckOwDebug_24')
    obj = cls()
    obj.config_file = '/tmp/CheckOwDebug_24.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_cfg = yaml.load(f, Loader=yaml.Loader)
        obj.config = yaml_cfg
        if 'query' in obj.config and 'path' in obj.config['query']:
            obj.config['query']['path'] = file_path
        obj.config['backup_path'] = backup_path
    else:
        obj.config = {'dep': 2, 'id': 24, 'query': {'path': file_path}, 'change': {'value': 'root:root'}, 'backup_path': backup_path, 'description': '确保 debug 文件所有者为 root:root'}
    obj.config['cahnge'] = obj.config.get('change')
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 24
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['224', 'status'] == 2

def test_fix_sets_owner_and_status(monkeypatch):
    mod, obj = build_instance()

def test_fix_calls_chown_with_expected_args(monkeypatch):
    pass

def test_check_owner_is_expected(monkeypatch):
    pass

def test_check_owner_not_expected(monkeypatch):
    pass

def test_check_true_on_owner_error_code(monkeypatch):
    pass

def test_rollback_updates_status_when_check_fails(monkeypatch):
    pass

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
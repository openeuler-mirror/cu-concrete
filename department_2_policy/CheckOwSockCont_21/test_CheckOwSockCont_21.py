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
    module_path = os.path.join(base_dir, 'CheckOwSockCont_21.py')
    spec = importlib.util.spec_from_file_location('CheckOwSockCont_21_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckOwSockCont_21.yaml')
pkl_path = '/tmp/test_data_status_checkowsockcont.pkl'
file_path = '/tmp/test_owsockcont_path'
backup_path = '/tmp/test_checkowsockcont_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckOwSockCont_21.yaml')
    with open(file_path, 'w') as f:
        f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckOwSockCont_21.yaml', file_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'CheckOwSockCont_21')
    obj = cls()
    obj.config_file = '/tmp/CheckOwSockCont_21.yaml'
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
        obj.config = {'dep': 2, 'id': 21, 'query': {'path': file_path}, 'change': {'value': 'root:root'}, 'backup_path': backup_path, 'description': '确保容器相关 socket/file 归属为 root:root'}
    obj.config['change'] = obj.config.get('change')
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 21
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['221', 'status'] == 2

def test_fix_sets_owner_and_status(monkeypatch):
    mod, obj = build_instance()
    called = {'chown': False}

    def fake_chown(owner, path):
        called['chown'] = True
    monkeypatch.setattr(mod.bsf, 'chown_file', fake_chown)
    expected_owner = obj.config['change']['value']
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: (expected_owner, 0))
    obj.fix()
    assert called['chown'] is True
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['221', 'status'] == 2

def test_check_owner_is_expected(monkeypatch):
    mod, obj = build_instance()
    expected_owner = obj.config['change']['value']
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: (expected_owner, 0))
    assert obj.check() is True

def test_check_owner_not_expected(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: ('nobody:nogroup', 0))
    assert obj.check() is False

def test_rollback_updates_status_when_check_fails(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:

        @staticmethod
        def chown_file(owner, path):
            pass

        @staticmethod
        def file_owner(*args):
            pass
    monkeypatch.setattr(mod, 'bsf', FakeBSF)
    obj.status_form.loc['221', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)

def test_reset(monkeypatch):
    pass

def test_get_des():
    pass
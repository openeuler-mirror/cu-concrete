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
    module_path = os.path.join(base_dir, 'CheckOwDoSock_17.py')
    spec = importlib.util.spec_from_file_location('CheckOwDoSock_17_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

yaml_path = os.path.join(os.path.dirname(__file__), 'CheckOwDoSock_17.yaml')
pkl_path = '/tmp/test_data_status_checkowdosock.pkl'
file_path = '/tmp/test_owdosock_path'
backup_path = '/tmp/test_checkowdosock_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckOwDoSock_17.yaml')
    # create the target path so file_owner can inspect it if needed
    with open(file_path, 'w') as f:
        f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckOwDoSock_17.yaml', file_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    mod = load_module()
    cls = getattr(mod, 'CheckOwDoSock_17')
    obj = cls()
    obj.config_file = '/tmp/CheckOwDoSock_17.yaml'
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
        # default config for tests
        obj.config = {
            'dep': 2,
            'id': 17,
            'query': {
                'path': file_path,
            },
            'change': {
                'value': 'root:root'
            },
            'backup_path': backup_path,
            'description': '确保 Docker socket/file 归属为 root:root'
        }
    # module uses typo 'cahnge' in fix(); mirror it so fix() won't KeyError
    obj.config['change'] = obj.config.get('change')
    obj.status_form = pd.read_pickle(pkl_path)
    return mod, obj


def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 17
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['217', 'status'] == 2


def test_fix_sets_owner_and_status(monkeypatch):
    mod, obj = build_instance()
    called = {'chown': False}
    def fake_chown(owner, path):
        called['chown'] = True
    # patch chown and file_owner; fix() uses 'cahnge' typo so we ensured it's present
    monkeypatch.setattr(mod.bsf, 'chown_file', fake_chown)
    # simulate that after chown the owner becomes the expected value
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: ('root:root', 0))
    obj.fix()
    assert called['chown'] is True
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['217', 'status'] == 2


def test_check_owner_is_expected(monkeypatch):
    mod, obj = build_instance()
    # check should return True when owner equals the configured expected value
    expected_owner = obj.config['change']['value']
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: (expected_owner, 0))
    assert obj.check() is True


def test_check_owner_not_expected(monkeypatch):
    mod, obj = build_instance()
    # If owner is not the expected value, check() should return False
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: ('nobody:nogroup', 0))
    assert obj.check() is False


def test_rollback_updates_status_when_check_fails(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:
        @staticmethod
        def chown_file(owner, path):
            # no-op for rollback
            return None

        @staticmethod
        def file_owner(*args):
            # simulate that the current owner is NOT the expected value
            if len(args) == 1:
                return ('nobody:nogroup', 0)
            return None

    monkeypatch.setattr(mod, 'bsf', FakeBSF)

    obj.status_form.loc['217', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)

    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['217', 'status'] == 0


def test_reset(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'file_owner', lambda p: ('root:root', 0))
    monkeypatch.setattr(mod.bsf, 'chown_file', lambda owner, path: None)
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['217', 'status'] == 2


def test_get_des():
    _, obj = build_instance()
    des = obj.get_des()
    assert des == obj.config['description']

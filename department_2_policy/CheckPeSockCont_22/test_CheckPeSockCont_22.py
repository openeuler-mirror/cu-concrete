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
    module_path = os.path.join(base_dir, 'CheckPeSockCont_22.py')
    spec = importlib.util.spec_from_file_location('CheckPeSockCont_22_module', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

yaml_path = os.path.join(os.path.dirname(__file__), 'CheckPeSockCont_22.yaml')
pkl_path = '/tmp/test_data_status_checkpesockcont.pkl'
file_path = '/tmp/test_pesockcont_path'
backup_path = '/tmp/test_checkpesockcont_bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/CheckPeSockCont_22.yaml')
    # create the target path so file_permission can inspect it if needed
    with open(file_path, 'w') as f:
        f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/CheckPeSockCont_22.yaml', file_path, backup_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    mod = load_module()
    cls = getattr(mod, 'CheckPeSockCont_22')
    obj = cls()
    obj.config_file = '/tmp/CheckPeSockCont_22.yaml'
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
            'id': 22,
            'query': {
                'path': file_path,
            },
            'change': {
                'value': '755'
            },
            'backup_path': backup_path,
            'description': '确保 容器 socket/file 权限为 660'
        }
    # defensive: some modules have 'cahnge' typo
    obj.config['cahnge'] = obj.config.get('change')
    obj.status_form = pd.read_pickle(pkl_path)
    return mod, obj


def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 22
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['222', 'status'] == 2


def test_fix_sets_mode_and_status(monkeypatch):
    mod, obj = build_instance()
    called = {'chmod': False}
    def fake_chmod(mode, path):
        called['chmod'] = True
    monkeypatch.setattr(mod.bsf, 'chmod_file', fake_chmod)
    # simulate that after chmod the permission becomes the expected value
    monkeypatch.setattr(mod.bsf, 'file_permission', lambda p: ('660', 0))
    obj.fix()
    assert called['chmod'] is True
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['222', 'status'] == 2


def test_check_permission_is_expected(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'file_permission', lambda p: ('660', 0))
    assert obj.check() is True


def test_check_permission_not_expected(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'file_permission', lambda p: ('755', 0))
    assert obj.check() is False


def test_rollback_updates_status_when_check_fails(monkeypatch):
    mod, obj = build_instance()

    class FakeBSF:
        @staticmethod
        def chown_file(owner, path):
            # module calls chown_file in rollback (though change is a mode); no-op
            return None

        @staticmethod
        def file_permission(*args):
            # simulate current permission is NOT the expected value
            if len(args) == 1:
                return ('644', 0)
            return None

    monkeypatch.setattr(mod, 'bsf', FakeBSF)

    obj.status_form.loc['222', 'status'] = 1
    obj.status_form.to_pickle(pkl_path)

    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['222', 'status'] == 0


def test_reset(monkeypatch):
    mod, obj = build_instance()
    monkeypatch.setattr(mod.bsf, 'file_permission', lambda p: ('755', 0))
    monkeypatch.setattr(mod.bsf, 'chmod_file', lambda mode, path: None)
    monkeypatch.setattr(mod.bsf, 'chown_file', lambda owner, path: None)
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['222', 'status'] == 2


def test_get_des():
    _, obj = build_instance()
    des = obj.get_des()
    assert des == obj.config['description']

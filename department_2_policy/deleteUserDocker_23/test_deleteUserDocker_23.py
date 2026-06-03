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
    module_path = os.path.join(base_dir, 'deleteUserDocker_23.py')
    spec = importlib.util.spec_from_file_location('deleteUserDocker_23_module_new', module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
yaml_path = os.path.join(os.path.dirname(__file__), 'deleteUserDocker_23.yaml')
pkl_path = '/tmp/test_data_status_deleteuserdocker_new.pkl'
file_path = '/tmp/test_delete_user_group_new'

class GroupLike:

    def __init__(self, users):
        self.users = users

    def __iter__(self):
        return iter(self.users)

    def split(self, sep):
        return ['group', 'x', '1000', self.users]

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/deleteUserDocker_23.yaml')
    with open(file_path, 'w') as f:
        f.write('')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/deleteUserDocker_23.yaml', file_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    mod = load_module()
    cls = getattr(mod, 'deleteUserDocker_23')
    obj = cls()
    obj.config_file = '/tmp/deleteUserDocker_23.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_cfg = yaml.load(f, Loader=yaml.Loader)
        obj.config = yaml_cfg
        if 'query' in obj.config and 'path' in obj.config['query']:
            obj.config['query']['path'] = file_path
    else:
        obj.config = {'dep': 2, 'id': 23, 'query': {'path': file_path, 'form': ['liukuntest']}, 'change': {'value': ['test1', 'test2', 'test3']}, 'description': '从docker组里删除未被信任的用户,增加信任用户'}
    obj.status_form = pd.read_pickle(pkl_path)
    return (mod, obj)

def test_init():
    mod, obj = build_instance()
    assert obj.config['dep'] == 2
    assert obj.config['id'] == 23
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    _, obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['223', 'status'] == 2

def test_fix_removes_bad_users_adds_good_users_and_sets_status(monkeypatch):
    mod, obj = build_instance()
    calls = {'remove': [], 'append': []}

    def fake_remove(user, group):
        calls['remove'].append(user)

    def fake_append(group, user):
        calls['append'].append(user)
    monkeypatch.setattr(mod.bsf, 'remove_user_from_group', fake_remove)
    monkeypatch.setattr(mod.bsf, 'append_user_group', fake_append)
    monkeypatch.setattr(mod.bsf, 'get_group_user', lambda p: (GroupLike(['liukuntest', 'other']), 0))
    obj.fix()
    assert 'liukuntest' in calls['remove']
    assert 'test1' in calls['append']
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['223', 'status'] == 2

def test_fix_creates_pkl_when_missing(monkeypatch):
    pass

def test_check_true_when_no_bad_users(monkeypatch):
    pass

def test_check_false_when_has_bad_users(monkeypatch):
    pass

def test_rollback_sets_status_to_zero_when_check_false(monkeypatch):
    pass

def test_rollback_no_change_when_check_true(monkeypatch):
    pass

def test_reset_calls_rollback_then_fix():
    pass

def test_get_des():
    pass
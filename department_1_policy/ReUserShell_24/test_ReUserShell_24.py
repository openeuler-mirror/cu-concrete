import os
import pytest
import pandas as pd
from ReUserShell_24 import ReUserShell_24
yaml_path = os.path.join(os.path.dirname(__file__), 'ReUserShell_24.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd_shell'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/ReUserShell_24.yaml')
    if os.path.exists('/etc/passwd'):
        os.system(f'cp /etc/passwd {passwd_path}')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/ReUserShell_24.yaml', passwd_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = ReUserShell_24()
    obj.config_file = '/tmp/ReUserShell_24.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 24, 'query': {'path': passwd_path, 'form': ['{ print $1,$7 }', ['lp', 'sync', 'halt', 'news', 'uucp', 'operator', 'games', 'gopher', 'smmsp', 'nfsnobody', 'nobody']]}, 'change': {'value': '/sbin/nologin'}, 'description': '修改特定用户的shell域'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 24
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['124', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['124', 'status']

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
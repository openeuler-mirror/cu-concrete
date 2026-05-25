import os
import pytest
import pandas as pd
from DelDangeFile_19 import DelDangeFile_19
yaml_path = os.path.join(os.path.dirname(__file__), 'DelDangeFile_19.yaml')
pkl_path = '/tmp/test_data_status.pkl'
netrc_path = '/tmp/test_netrc'
rhosts_path = '/tmp/test_rhosts'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/DelDangeFile_19.yaml')
    with open(netrc_path, 'w') as f:
        f.write('netrc content')
    with open(rhosts_path, 'w') as f:
        f.write('rhosts content')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/DelDangeFile_19.yaml', netrc_path, rhosts_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = DelDangeFile_19()
    obj.config_file = '/tmp/DelDangeFile_19.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 19, 'query': {'form': ['test_netrc', 'test_rhosts']}, 'description': '删除对.netrc,.rhosts的文件'}
    obj.status_form = pd.read_pickle(pkl_path)

def test_init():
    pass

def test_finalfix():
    pass

def test_fix():
    pass

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
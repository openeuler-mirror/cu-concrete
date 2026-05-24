import os
import pytest
import pandas as pd
from Resetlsrm_27 import Resetlsrm_27
yaml_path = os.path.join(os.path.dirname(__file__), 'Resetlsrm_27.yaml')
pkl_path = '/tmp/test_data_status.pkl'
bashrc_path = '/tmp/test_bashrc_resetlsrm'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/Resetlsrm_27.yaml')
    with open(bashrc_path, 'w') as f:
        f.write('# .bashrc\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/Resetlsrm_27.yaml', bashrc_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    pass

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
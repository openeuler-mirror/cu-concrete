import os
import pytest
import pandas as pd
from Delbanner_18 import Delbanner_18
yaml_path = os.path.join(os.path.dirname(__file__), 'Delbanner_18.yaml')
pkl_path = '/tmp/test_data_status.pkl'
issue_path = '/tmp/test_issue'
issue_net_path = '/tmp/test_issue.net'
motd_path = '/tmp/test_motd'
issue_bak = '/tmp/test_issue.bak'
issue_net_bak = '/tmp/test_issue.net.bak'
motd_bak = '/tmp/test_motd.bak'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/Delbanner_18.yaml')
    with open(issue_path, 'w') as f:
        f.write('banner1')
    with open(issue_net_path, 'w') as f:
        f.write('banner2')
    with open(motd_path, 'w') as f:
        f.write('banner3')
    with open(issue_bak, 'w') as f:
        f.write('banner1')
    with open(issue_net_bak, 'w') as f:
        f.write('banner2')
    with open(motd_bak, 'w') as f:
        f.write('banner3')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/Delbanner_18.yaml', issue_path, issue_net_path, motd_path, issue_bak, issue_net_bak, motd_bak]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = Delbanner_18()

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
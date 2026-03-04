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
    # 复制 yaml
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/Delbanner_18.yaml')
    # 构造原始文件
    with open(issue_path, 'w') as f:
        f.write('banner1')
    with open(issue_net_path, 'w') as f:
        f.write('banner2')
    with open(motd_path, 'w') as f:
        f.write('banner3')
    # 构造备份文件
    with open(issue_bak, 'w') as f:
        f.write('banner1')
    with open(issue_net_bak, 'w') as f:
        f.write('banner2')
    with open(motd_bak, 'w') as f:
        f.write('banner3')
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/Delbanner_18.yaml', issue_path, issue_net_path, motd_path, issue_bak, issue_net_bak, motd_bak]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = Delbanner_18()
    obj.config_file = '/tmp/Delbanner_18.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 18,
        'query': {
            'path': [issue_path, issue_net_path, motd_path]
        },
        'change': {
            'value': [issue_bak, issue_net_bak, motd_bak]
        },
        'description': '会话界面的提醒字符段备份并删除'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 18
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['118', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['118', 'status']
    assert val == 2

def test_check():
    obj = build_instance()
    obj.fix()
    result = obj.check()
    assert isinstance(result, bool)

def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['118', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['118', 'status']
    assert val == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == '会话界面的提醒字符段备份并删除'

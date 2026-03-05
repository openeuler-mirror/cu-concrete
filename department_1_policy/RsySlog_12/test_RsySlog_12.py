import os
import pytest
import pandas as pd
from RsySlog_12 import RsySlog_12

pkl_path = '/tmp/test_data_status_12.pkl'
rsyslog_path = '/tmp/test_rsyslog_12.conf'
yaml_path = os.path.join(os.path.dirname(__file__), 'RsySlog_12.yaml')

@pytest.fixture(autouse=True)
def prepare_files():
    # 构造 rsyslog.conf 文件
    with open(rsyslog_path, 'w') as f:
        f.write('#rsyslog config\n')
    # 构造 data_status.pkl
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, rsyslog_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = RsySlog_12()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 12,
        'query': {
            'form': '^*.*',
            'path': rsyslog_path
        },
        'change': {
            'value': '*.* /var/log/all.log'
        },
        'description': '远程系统日志设定'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 12
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['112', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['112', 'status']
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
    val = status_df.loc['112', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['112', 'status']
    assert val == 2

def test_get_des():
    obj = build_instance()
    des = obj.get_des()
    assert des == '远程系统日志设定'

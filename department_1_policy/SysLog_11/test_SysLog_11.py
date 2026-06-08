import os
import pytest
import pandas as pd
from SysLog_11 import SysLog_11
yaml_path = os.path.join(os.path.dirname(__file__), 'SysLog_11.yaml')
pkl_path = '/tmp/test_data_status.pkl'
rsyslog_path = '/tmp/test_rsyslog.conf'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/SysLog_11.yaml')
    with open(rsyslog_path, 'w') as f:
        f.write('*.* /var/log/all.log\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/SysLog_11.yaml', rsyslog_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = SysLog_11()
    obj.config_file = '/tmp/SysLog_11.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 11, 'query': {'form1': '^*.err;kern.debug;daemon.notice', 'form2': '^cron.*', 'form3': '^authpriv.*', 'path': rsyslog_path}, 'change': {'value1': '*.err;kern.debug;daemon.notice;        /var/log/messages', 'value2': 'cron.*                                 /var/log/cron', 'value3': 'authpriv.*                             /var/log/secure'}, 'description': '本地系统日志设定'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 11
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['111', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['111', 'status']
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
    val = status_df.loc['111', 'status']
    assert val == 0

def test_reset():
    obj = build_instance()
    obj.reset()

def test_get_des():
    pass
import os
import pytest
import pandas as pd
from Items_12_SetRemoteLog import Items_12_SetRemoteLog

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_12_SetRemoteLog.yaml')
pkl_path = '/tmp/test_data_status.pkl'
rsyslog_path = '/tmp/test_rsyslog.conf'


@pytest.fixture(autouse=True)
def prepare_files():
    with open(rsyslog_path, 'w') as f:
        f.write('*.*    /var/log/all.log\n'
                '*.*    @192.168.0.1\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [rsyslog_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_12_SetRemoteLog()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 12,
        'query': {'form': '@192.168.0.1', 'path': rsyslog_path},
        'change': {'value': '*.*    @192.168.0.1'},
        'description': '设置远程log的存放'
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
    assert pd.read_pickle(pkl_path).loc['112', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['112', 'status'] == 2
    content = open(rsyslog_path).read()
    assert '@192.168.0.1' in content
    # 旧行被移除, 只保留一条远程日志配置
    assert content.count('@192.168.0.1') == 1


def test_check():
    obj = build_instance()
    assert obj.check() is True
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['112', 'status'] == 0


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['112', 'status'] == 2


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '设置远程log的存放'

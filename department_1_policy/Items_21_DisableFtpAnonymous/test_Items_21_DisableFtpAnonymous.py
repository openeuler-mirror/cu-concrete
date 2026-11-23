import os
import pytest
import pandas as pd
from Items_21_DisableFtpAnonymous import Items_21_DisableFtpAnonymous

yaml_path = os.path.join(os.path.dirname(__file__), 'Items_21_DisableFtpAnonymous.yaml')
pkl_path = '/tmp/test_data_status.pkl'
vsftpd_conf_path = '/tmp/test_vsftpd.conf'


@pytest.fixture(autouse=True)
def prepare_files():
    # 发行版默认: 该行是注释状态
    with open(vsftpd_conf_path, 'w') as f:
        f.write('# Uncomment and set to NO to disable anonymous access\n'
                '#anonymous_enable=YES\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [vsftpd_conf_path, pkl_path]:
        if os.path.exists(fp):
            os.remove(fp)


def build_instance():
    obj = Items_21_DisableFtpAnonymous()
    obj.config_file = yaml_path
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {
        'dep': 1,
        'id': 21,
        'query': {'path': [vsftpd_conf_path]},
        'harden_before': {'value': 'anonymous_enable=YES'},
        'harden_after': {'value': 'anonymous_enable=NO'},
        'description': '禁止匿名账户登录ftp'
    }
    obj.status_form = pd.read_pickle(pkl_path)
    return obj


def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 21
    assert isinstance(obj.status_form, pd.DataFrame)


def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    assert pd.read_pickle(pkl_path).loc['121', 'status'] == 2


def test_fix():
    obj = build_instance()
    obj.fix()
    assert pd.read_pickle(pkl_path).loc['121', 'status'] == 2
    lines = [l for l in open(vsftpd_conf_path).read().splitlines() if l.strip()]
    # 注释被取消, 值改为 NO
    assert 'anonymous_enable=NO' in lines


def test_check():
    obj = build_instance()
    # 注释状态 -> 判未加固
    assert obj.check() is False
    obj.fix()
    assert obj.check() is True


def test_rollback():
    obj = build_instance()
    obj.fix()
    obj.rollback()
    assert pd.read_pickle(pkl_path).loc['121', 'status'] == 0
    assert 'anonymous_enable=YES' in open(vsftpd_conf_path).read()


def test_reset():
    obj = build_instance()
    obj.reset()
    assert pd.read_pickle(pkl_path).loc['121', 'status'] == 2
    assert obj.check() is True


def test_get_des():
    obj = build_instance()
    assert obj.get_des() == '禁止匿名账户登录ftp'

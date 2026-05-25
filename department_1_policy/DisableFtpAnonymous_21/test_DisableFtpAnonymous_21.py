import os
import pytest
import pandas as pd
from DisableFtpAnonymous_21 import DisableFtpAnonymous_21
yaml_path = os.path.join(os.path.dirname(__file__), 'DisableFtpAnonymous_21.yaml')
pkl_path = '/tmp/test_data_status.pkl'
passwd_path = '/tmp/test_passwd'
vsftpd_conf_path = '/tmp/test_vsftpd.conf'
vsftpd_conf2_path = '/tmp/test_vsftpd_conf2.conf'
ftpusers_path = '/tmp/test_ftpusers'

@pytest.fixture(autouse=True)
def prepare_files():
    if os.path.exists(yaml_path):
        os.system(f'cp {yaml_path} /tmp/DisableFtpAnonymous_21.yaml')
    with open(passwd_path, 'w') as f:
        f.write('ftp:x:1001:1001:ftp user:/var/ftp:/sbin/nologin\n#ftp:x:1001:1001:ftp user:/var/ftp:/sbin/nologin\n')
    with open(vsftpd_conf_path, 'w') as f:
        f.write('anonymous_enabl = YES\n')
    with open(vsftpd_conf2_path, 'w') as f:
        f.write('anonymous_enabl = YES\n')
    with open(ftpusers_path, 'w') as f:
        f.write('root\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    for fp in [pkl_path, '/tmp/DisableFtpAnonymous_21.yaml', passwd_path, vsftpd_conf_path, vsftpd_conf2_path, ftpusers_path]:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = DisableFtpAnonymous_21()
    obj.config_file = '/tmp/DisableFtpAnonymous_21.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 21, 'query': {'path': [passwd_path, vsftpd_conf_path, vsftpd_conf2_path, ftpusers_path], 'form': ['^ftp:x', 'anonymous_enabl = YES', '^#ftp:x']}, 'change': {'value': ['anonymous_enabl = NO', 'root']}, 'description': '禁止匿名账户登录ftp'}
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
    status_df = pd.read_pickle(pkl_path)
    val = status_df.loc['121', 'status']
    assert val == 2

def test_fix():
    obj = build_instance()
    obj.fix()

def test_check():
    pass

def test_rollback():
    pass

def test_reset():
    pass

def test_get_des():
    pass
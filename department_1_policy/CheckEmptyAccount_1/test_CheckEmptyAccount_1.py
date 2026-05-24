import os
import shutil
import pandas as pd
import pytest
from CheckEmptyAccount_1 import CheckEmptyAccount_1
yaml_path = os.path.join(os.path.dirname(__file__), 'CheckEmptyAccount_1.yaml')
shadow_path = '/tmp/test_shadow'
backup_path = '/tmp/test_shadow_bak'
pkl_path = '/tmp/test_data_status.pkl'

@pytest.fixture(autouse=True)
def prepare_files():
    shutil.copy(yaml_path, '/tmp/CheckEmptyAccount_1.yaml')
    with open(shadow_path, 'w') as f:
        f.write('user1::\nuser2:12345\nuser3::\n')
    df = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
    df.to_pickle(pkl_path)
    yield
    '\n    这段代码是 pytest 的 fixture 清理机制，用于测试前后自动准备和清理测试环境。\n\n    解释如下：\n\n    yield 前面的代码会在每个测试用例运行前执行（准备测试环境，比如复制文件、创建测试数据）。\n    yield 后面的代码会在每个测试用例运行后自动执行（清理环境，比如删除临时文件）。\n    具体流程：\n\n    测试开始前，创建 shadow、yaml、pkl 等临时文件。\n    yield 暂停,pytest 执行你的测试函数。\n    测试结束后，继续执行 yield 后的清理代码，把所有临时文件删除，保证环境干净。\n    这样可以避免测试间相互影响，保证每次测试都是独立的。\n    \n    执行方式:pytest test_CheckEmptyAccount_1.py,这样框架会执行每一个测试项。如果全部通过就会显示PASS\n    否则会显示失败的测试项\n    \n    其余加固项的代码也是如此逻辑\n    '
    for fp in [shadow_path, backup_path, pkl_path, '/tmp/CheckEmptyAccount_1.yaml']:
        if os.path.exists(fp):
            os.remove(fp)

def build_instance():
    obj = CheckEmptyAccount_1()
    obj.config_file = '/tmp/CheckEmptyAccount_1.yaml'
    obj.pkl_file = pkl_path
    obj.current_dir = '/tmp'
    obj.config = {'dep': 1, 'id': 1, 'query': [{'path': shadow_path, 'form': '( $2 == "" ) { print $1 }'}], 'change': [{'set': 'chpasswd', 'value': '123@123!'}], 'backup_path': backup_path, 'description': '空口令检查'}
    obj.status_form = pd.read_pickle(pkl_path)
    return obj

def test_init():
    obj = build_instance()
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 1
    assert isinstance(obj.status_form, pd.DataFrame)

def test_finalfix():
    obj = build_instance()
    obj.finalfix()
    status_df = pd.read_pickle(pkl_path)
    assert status_df.loc['11', 'status'] == 2 or status_df.loc['11', 'status'] == '2'

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
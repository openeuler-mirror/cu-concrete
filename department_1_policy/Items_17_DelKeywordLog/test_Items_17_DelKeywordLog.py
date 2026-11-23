import os
import re
import sys
import pytest

item_dir = os.path.dirname(os.path.abspath(__file__))
dep_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(dep_dir)
for _p in (item_dir, dep_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import Panda as pd
import yaml
import Items_17_DelKeywordLog as mod
from Items_17_DelKeywordLog import Items_17_DelKeywordLog

yaml_path = os.path.join(item_dir, 'Items_17_DelKeywordLog.yaml')
KEYWORDS = ['virtio', 'kvm', 'KVM', 'Cloud', 'cloudw']


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备日志文件与 pkl, 并用 python 实现替换 bsf 的 shell 调用"""
    log = tmp_path / 'messages'
    log.write_text('Jan  1 00:00:00 host kernel: normal message\n'
                   'Jan  1 00:00:01 host qemu: virtio-net device\n'
                   'Jan  1 00:00:02 host kvm: kvm guest detected\n'
                   'Jan  1 00:00:03 host cloud: Cloud platform\n',
                   encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    pd.DataFrame(columns=['status', 'module_name', 'module_path']).to_pickle(pkl)
    copies = []

    def fake_grep(form, path):
        # grep -E {form} {path}
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(form)
        out = [l for l in open(path, encoding='utf-8').read().splitlines() if regex.search(l)]
        return ('\n'.join(out), 0 if out else 1)

    def fake_remove_line(form, path):
        # sed -i /{form}/d {path}
        if not os.path.isfile(path):
            return ('', 2)
        regex = re.compile(form)
        lines = open(path, encoding='utf-8').read().splitlines()
        with open(path, 'w', encoding='utf-8') as f:
            for l in lines:
                if not regex.search(l):
                    f.write(l + '\n')
        return ('', 0)

    def fake_cp_shell(source_path, new_path):
        # 本项不应再有任何备份动作, 这里只记录调用
        copies.append((source_path, new_path))
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'grep_shell', fake_grep)
    monkeypatch.setattr(mod.bsf, 'remove_line', fake_remove_line)
    monkeypatch.setattr(mod.bsf, 'cp_shell', fake_cp_shell)

    obj = Items_17_DelKeywordLog()
    obj.config['query']['path'] = str(log)
    obj.pkl_file = str(pkl)
    obj.status_form = pd.read_pickle(str(pkl))
    return obj, str(log), str(pkl), copies


def test_init(env):
    obj, log, pkl, copies = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 17
    assert obj.config['change']['value'] == KEYWORDS
    # 本项不再有备份路径配置: 加固后即为彻底删除
    assert 'path1' not in obj.config['query']


def test_yaml_config():
    with open(yaml_path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    # 备份路径已移除
    assert 'path1' not in cfg['query']
    # description 明确说明是不可逆的彻底删除
    assert '彻底删除' in cfg['description']
    assert '不可还原' in cfg['description']


def test_finalfix(env):
    obj, log, pkl, copies = env
    obj.finalfix()
    assert pd.read_pickle(pkl).loc['117', 'status'] == 2


def test_check_before_fix(env):
    obj, log, pkl, copies = env
    assert obj.check() is False


def test_fix(env):
    obj, log, pkl, copies = env
    obj.fix()
    content = open(log, encoding='utf-8').read()
    for kw in KEYWORDS:
        assert kw not in content
    # 无关日志保留
    assert 'normal message' in content
    # 彻底删除: 不产生备份文件, 也不做 cp 动作
    assert copies == []
    assert pd.read_pickle(pkl).loc['117', 'status'] == 2
    assert obj.check() is True


def test_fix_is_idempotent(env):
    obj, log, pkl, copies = env
    obj.fix()
    before = open(log, encoding='utf-8').read()
    obj.fix()
    assert open(log, encoding='utf-8').read() == before
    assert pd.read_pickle(pkl).loc['117', 'status'] == 2


def test_rollback_is_irreversible(env):
    obj, log, pkl, copies = env
    obj.fix()
    pkl_before = open(pkl, 'rb').read()
    obj.rollback()
    content = open(log, encoding='utf-8').read()
    # 不可还原: 日志内容不会恢复, 命中的关键字记录已永久消失
    for kw in KEYWORDS:
        assert kw not in content
    assert 'normal message' in content
    # rollback 直接 pass: 不动日志, 也不动 pkl
    assert open(pkl, 'rb').read() == pkl_before
    assert copies == []
    # 状态仍是 fix() 写入的已加固(2): 日志中已无关键字, check() 恒为 True
    assert pd.read_pickle(pkl).loc['117', 'status'] == 2
    assert obj.check() is True


def test_reset(env):
    obj, log, pkl, copies = env
    obj.reset()
    assert pd.read_pickle(pkl).loc['117', 'status'] == 2
    assert obj.check() is True


def test_get_des(env):
    obj, log, pkl, copies = env
    assert obj.get_des() == obj.config['description']
    assert '不可还原' in obj.get_des()

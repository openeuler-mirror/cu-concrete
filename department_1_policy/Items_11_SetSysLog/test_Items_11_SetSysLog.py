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
import Items_11_SetSysLog as mod
from Items_11_SetSysLog import Items_11_SetSysLog

AFTER = [
    'cron.* /var/log/cron',
    'authpriv.* /var/log/secure',
]
BEFORE = [
    'cron.*',
    'authpriv.*',
]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """准备 /etc/rsyslog.conf 与 pkl, 并拦截 base_shell(服务操作)"""
    conf = tmp_path / 'rsyslog.conf'
    # 初始为未加固形态: 只有 selector, 没有输出文件
    conf.write_text('*.* /var/log/all.log\n' + '\n'.join(BEFORE) + '\n', encoding='utf-8')
    pkl = tmp_path / 'data_status.pkl'
    cmds = []

    def fake_base_shell(cmd, **kwargs):
        # 记录 yaml 中配置的服务操作
        cmds.append(cmd)
        return ('', 0)

    monkeypatch.setattr(mod, 'base_shell', fake_base_shell)

    obj = Items_11_SetSysLog()
    obj.config['path'] = str(conf)
    obj.pkl_file = str(pkl)
    return obj, str(conf), str(pkl), cmds


def read(conf):
    with open(conf, encoding='utf-8') as f:
        return f.read()


def test_init(env):
    obj, conf, pkl, cmds = env
    assert obj.config['dep'] == 1
    assert obj.config['id'] == 11
    assert obj.get_des() == obj.config['description']
    assert [e['value'] for e in obj.config['entries']] == [
        '/var/log/cron', '/var/log/secure']


def test_check_before_fix(env):
    # 裸 selector 形态 -> 判未加固
    obj, conf, pkl, cmds = env
    assert obj.check() is False


def test_fix(env):
    obj, conf, pkl, cmds = env
    obj.fix()
    content = read(conf)
    for want in AFTER:
        assert want + '\n' in content
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['111', 'status'] == 2


def test_fix_keeps_other_lines(env):
    # 其它日志配置行不受影响
    obj, conf, pkl, cmds = env
    obj.fix()
    assert '*.* /var/log/all.log' in read(conf)


def test_fix_keeps_other_selectors(env):
    # 其它 selector 不被误改
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('*.info /var/log/messages\ncron.*\n')
    obj.fix()
    content = read(conf)
    assert '*.info /var/log/messages\n' in content
    assert 'cron.* /var/log/cron\n' in content


def test_fix_idempotent(env):
    # 已是加固形态时不再重复改写, 文件字节保持不变
    obj, conf, pkl, cmds = env
    obj.fix()
    before = read(conf)
    obj.fix()
    assert read(conf) == before
    assert obj.check() is True


def test_fix_removes_duplicate_lines(env):
    # 同一 selector 有多行时只保留一行标准写法, 不产生重复规则
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('cron.* /var/log/old\ncron.* /var/log/cron\n')
    obj.fix()
    lines = read(conf).splitlines()
    assert lines.count(AFTER[0]) == 1
    assert 'cron.* /var/log/old' not in read(conf)


def test_check_one_missing(env):
    # 缺少任意一条都不算已加固
    obj, conf, pkl, cmds = env
    obj.fix()
    content = read(conf).replace(AFTER[1] + '\n', '')
    with open(conf, 'w', encoding='utf-8') as f:
        f.write(content)
    assert obj.check() is False


def test_fix_appends_when_missing(env):
    # 文件中没有这两行配置 -> 在文件末尾另起一行追加
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('*.* /var/log/all.log\n')
    obj.fix()
    assert read(conf) == ('*.* /var/log/all.log\n'
                           + AFTER[0] + '\n'
                           + AFTER[1] + '\n')
    assert obj.check() is True


def test_fix_appends_after_no_trailing_newline(env):
    # 文件末尾没有换行时, 追加的配置另起一行, 不会粘到上一行末尾
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('*.* /var/log/all.log')
    obj.fix()
    assert read(conf) == ('*.* /var/log/all.log\n'
                           + AFTER[0] + '\n'
                           + AFTER[1] + '\n')
    assert obj.check() is True


def test_rollback(env):
    # 还原: 直接删除这两行配置, 而不是改回裸 selector
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    content = read(conf)
    for want in AFTER:
        assert want not in content
    for want in BEFORE:
        assert want not in content
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['111', 'status'] == 0


def test_rollback_keeps_other_lines(env):
    # 还原只删这两行, 其它日志规则保留
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    assert read(conf) == '*.* /var/log/all.log\n'


def test_rollback_keeps_commented_line(env):
    # 注释行保留, 不参与删除
    obj, conf, pkl, cmds = env
    with open(conf, 'w', encoding='utf-8') as f:
        f.write('#cron.* /var/log/cron\ncron.* /var/log/cron\n')
    obj.rollback()
    lines = read(conf).splitlines()
    assert '#cron.* /var/log/cron' in lines
    assert 'cron.* /var/log/cron' not in lines


def test_rollback_idempotent(env):
    # 反复还原不会报错, 文件保持不变
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    before = read(conf)
    obj.rollback()
    assert read(conf) == before
    assert obj.check() is False


def test_fix_rollback_fix_cycle(env):
    # 还原之后再加固: 走末尾追加分支, 内容正确
    obj, conf, pkl, cmds = env
    obj.fix()
    obj.rollback()
    obj.fix()
    content = read(conf)
    assert content == ('*.* /var/log/all.log\n'
                       + AFTER[0] + '\n'
                       + AFTER[1] + '\n')
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['111', 'status'] == 2


def test_repeated_fix_rollback_stable(env):
    # 反复加固/还原后不产生重复行, 也不残留配置
    obj, conf, pkl, cmds = env
    for _ in range(3):
        obj.fix()
        obj.rollback()
    content = read(conf)
    assert content == '*.* /var/log/all.log\n'
    for want in AFTER:
        assert want not in content


def test_reset(env):
    obj, conf, pkl, cmds = env
    obj.reset()
    assert obj.check() is True
    assert pd.read_pickle(pkl).loc['111', 'status'] == 2


def test_commands_in_yaml():
    # 服务操作写在 yaml 里, 不硬编码在 fix 方法中
    obj = Items_11_SetSysLog()
    commands = obj.config['commands']
    assert 'sudo systemctl restart rsyslog.service' in commands['fix']
    assert 'sudo systemctl enable rsyslog.service' in commands['fix']
    assert commands['rollback'] == ['sudo systemctl restart rsyslog.service']


def test_fix_runs_yaml_commands(env):
    # 加固时执行 yaml 中 fix 阶段的服务操作: 重启 rsyslog + 开机自启
    obj, conf, pkl, cmds = env
    obj.fix()
    assert ['sudo', 'systemctl', 'restart', 'rsyslog.service'] in cmds
    assert ['sudo', 'systemctl', 'enable', 'rsyslog.service'] in cmds


def test_rollback_runs_only_restart(env):
    # 还原时只重启 rsyslog, 不再执行 enable
    obj, conf, pkl, cmds = env
    obj.fix()
    cmds.clear()
    obj.rollback()
    assert ['sudo', 'systemctl', 'restart', 'rsyslog.service'] in cmds
    assert ['sudo', 'systemctl', 'enable', 'rsyslog.service'] not in cmds


def test_check_false_when_file_missing(env):
    # 配置文件不存在 -> 判未加固, 不抛异常
    obj, conf, pkl, cmds = env
    os.remove(conf)
    assert obj.check() is False


def test_fix_when_file_missing(env):
    # 配置文件不存在 -> 不抛异常, 状态置为未加固
    obj, conf, pkl, cmds = env
    os.remove(conf)
    obj.fix()
    assert obj.check() is False
    assert pd.read_pickle(pkl).loc['111', 'status'] == 0

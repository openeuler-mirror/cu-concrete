import os
import re
import sys
import pytest

item_dir = os.path.dirname(os.path.abspath(__file__))
policy_dir = os.path.dirname(item_dir)
project_dir = os.path.dirname(policy_dir)
for _p in (item_dir, policy_dir, project_dir):
    if _p not in sys.path:
        sys.path.append(_p)

import yaml
import Items_01_Baseline as mod
from Items_01_Baseline import Items_01_Baseline

TOTAL_STEPS = 60          # 合并后的细项总数(kv + 权限 + 计划任务 + 安全对象)
YAML_FILE = os.path.join(item_dir, 'Items_01_Baseline.yaml')
CATEGORY_NAMES = [
    'SSH 服务加固', '内核与网络参数', 'PAM 与登录认证', '账户与密码策略', 'Shell 会话与用户环境',
    '计划任务权限', '关键文件与启动目录权限', '日志文件权限', '系统安全对象修复',
]


def load_yaml():
    with open(YAML_FILE, encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture
def env(tmp_path, monkeypatch):
    """构造一个与真实 yaml 同结构、但路径全部指向 tmp 的测试配置"""
    conf = tmp_path / 'sshd_config'
    conf.write_text('# sshd_config\n', encoding='utf-8')
    missing = tmp_path / 'not_exist'
    logfile = tmp_path / 'messages'
    logfile.write_text('x\n', encoding='utf-8')
    cron_dir = tmp_path / 'cron.d'
    cron_dir.mkdir()
    deny = tmp_path / 'cron.deny'
    deny.write_text('x\n', encoding='utf-8')
    allow = tmp_path / 'cron.allow'
    pem = tmp_path / 'email-ca-bundle.pem'
    pem.write_text('x\n', encoding='utf-8')
    dbus = tmp_path / 'dbus-daemon-launch-helper'
    dbus.write_text('x\n', encoding='utf-8')

    categories = [
        {
            'name': 'kv',
            'desc': 'kv 配置',
            'entries': [{'path': str(conf), 'key': 'Protocol', 'value': '2'}],
        },
        {
            'name': 'kv-skip',
            'desc': '目标文件不存在时跳过',
            'skip_missing': True,
            'entries': [{'path': str(missing), 'key': 'umask', 'value': '077'}],
        },
        {
            'name': 'perm',
            'desc': '权限收紧',
            'chmod_entries': [{'path': str(logfile), 'mode': '600'}],
        },
        {
            'name': 'cron',
            'desc': '计划任务权限',
            'cron_paths': [str(cron_dir)],
            'deny_files': [str(deny)],
            'allow_files': [str(allow)],
        },
        {
            'name': 'obj',
            'desc': '安全对象修复',
            'remove_files': [str(pem)],
            'dbus_helper': str(dbus),
        },
    ]

    cmds = []
    # 模拟权限位: Windows 的 os.chmod 不支持 setuid/精确权限, 故用字典模拟
    modes = {}

    def fake_chmod_file(form, path):
        cur = modes.get(path, 0o644)
        if re.fullmatch(r'[0-7]+', str(form)):
            modes[path] = int(str(form), 8)
        elif 'rwx' in str(form):
            modes[path] = cur & ~0o077        # og-rwx
        else:
            modes[path] = cur
        return ('', 0)

    def fake_chown_file(form, path):
        return ('', 0)

    monkeypatch.setattr(mod.bsf, 'chmod_file', fake_chmod_file)
    monkeypatch.setattr(mod.bsf, 'chown_file', fake_chown_file)

    obj = Items_01_Baseline()
    obj.categories = categories
    obj.config = {'description': 'test', 'categories': categories}
    monkeypatch.setattr(obj, '_mode_of', lambda p: modes.get(p, 0o644))
    files = {
        'conf': conf, 'missing': missing, 'logfile': logfile, 'cron_dir': cron_dir,
        'deny': deny, 'allow': allow, 'pem': pem, 'dbus': dbus,
    }
    return obj, categories, cmds, files, modes


# ---------------- 真实 yaml 结构 ----------------

def test_real_yaml_categories():
    cfg = load_yaml()
    names = [c['name'] for c in cfg['categories']]
    assert names == CATEGORY_NAMES
    assert cfg['id'] == 1


def test_real_yaml_entries_are_valid():
    cfg = load_yaml()
    seen = set()
    for cat in cfg['categories']:
        for e in cat.get('entries') or []:
            assert 'path' in e and 'key' in e and 'value' in e
            key = (e['path'], e['key'])
            assert key not in seen, '重复配置: {}'.format(key)
            seen.add(key)
        for e in cat.get('chmod_entries') or []:
            assert 'path' in e and 'mode' in e
            int(str(e['mode']), 8)      # 权限必须是合法八进制


def test_real_yaml_step_count():
    obj = Items_01_Baseline()
    steps = obj.describe_steps()
    assert len(steps) == TOTAL_STEPS
    assert all(d for d, _ in steps)


def test_real_yaml_describe_config_grouped():
    obj = Items_01_Baseline()
    lines = obj.describe_config()
    for name in CATEGORY_NAMES:
        assert any(line.startswith('[{}]'.format(name)) for line in lines)


# ---------------- 合并逻辑行为 ----------------

def test_fix_writes_kv_entries(env):
    obj, cats, cmds, files, modes = env
    obj.fix()
    assert 'Protocol 2' in files['conf'].read_text(encoding='utf-8')
    assert obj.check() is True


def test_fix_chmod_entries(env):
    obj, cats, cmds, files, modes = env
    obj.fix()
    assert modes[str(files['logfile'])] == 0o600


def test_fix_cron_paths_and_lists(env):
    obj, cats, cmds, files, modes = env
    obj.fix()
    # deny 文件被删除
    assert not files['deny'].exists()
    # allow 白名单被建立且属组/其他无权限
    assert files['allow'].exists()
    assert not (modes[str(files['allow'])] & 0o077)
    # cron 路径属组/其他无权限
    assert not (modes[str(files['cron_dir'])] & 0o077)


def test_fix_remove_files_and_dbus(env):
    obj, cats, cmds, files, modes = env
    obj.fix()
    assert not files['pem'].exists()
    assert modes[str(files['dbus'])] == 0o4750


def test_check_before_fix(env):
    obj, cats, cmds, files, modes = env
    assert obj.check() is False


def test_skip_missing_treated_as_ok(env):
    # skip_missing 分类中目标文件不存在 -> 视为无需加固, 不影响整体判定
    obj, cats, cmds, files, modes = env
    obj.fix()
    assert obj.check() is True
    steps = obj.describe_steps()
    matched = [(d, f) for d, f in steps if str(files['missing']) in d]
    assert matched and all(f() is True for d, f in matched)


def test_no_commands_in_config():
    # 本项只写配置文件, 配置中不再包含任何生效命令
    cfg = load_yaml()
    for cat in cfg['categories']:
        assert 'commands' not in cat


def test_describe_steps_cover_all_types(env):
    obj, cats, cmds, files, modes = env
    steps = obj.describe_steps()
    descs = [d for d, _ in steps]
    assert any(d.startswith('配置 ') for d in descs)
    assert any(d.startswith('设置权限 ') for d in descs)
    assert any(d.startswith('收紧权限 ') for d in descs)
    assert any(d.startswith('删除 ') for d in descs)
    assert any(d.startswith('建立白名单 ') for d in descs)
    assert any(d.startswith('修复属主权限 ') for d in descs)

"""
default_0_policy 公共基类

安装期一次性加固专用:
- 仅提供 fix/check/get_des 三个抽象方法, 不提供 rollback/reset/finalfix
- 系统安装时通过 `cu-concrete default_harden` 全部执行一次, 之后不再使用
- ensure_kv 复刻 cuos-harden.conf 中 'm' 操作语义:
  文件中已存在以 key 开头的行 -> 整行替换为 key<sep>value
  不存在 -> 追加到文件末尾
"""
import os
import re
import time
import shutil
import logging
from abc import ABC, abstractmethod

from base_shell import base_shell, base_pipe_shell


class base_default_fix(ABC):

    # 同一次运行内所有加固项共用同一备份时间戳
    _backup_suffix = ".cubak." + time.strftime("%Y%m%d%H%M%S")

    def __init__(self):
        pass

    @abstractmethod
    def fix(self):
        pass

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def get_des(self):
        pass

    # ---------------- 通用工具 ----------------

    def check_entries(self, entries):
        """批量检查 yaml 中的 kv 条目, 全部满足才返回 True"""
        return all(
            self.check_kv(e['path'], e['key'], e.get('value', ''), e.get('sep', ' '))
            for e in entries or []
        )
    
    def ensure_entries(self, entries):
        """批量执行 yaml 中的 kv 条目: {path, key, value, sep?}"""
        for e in entries or []:
            self.ensure_kv(e['path'], e['key'], e.get('value', ''), e.get('sep', ' '))

    @staticmethod
    def _key_pattern(key):
        """把 key 转为行首匹配正则: 空白字符宽松匹配, 其余字符转义"""
        return r"[ \t]+".join(re.escape(p) for p in str(key).split())

    @classmethod
    def backup_file(cls, path):
        """修改前备份为 <file>.cubak.<时间戳>, 每个文件同一次运行只备份一次"""
        if not os.path.isfile(path):
            return
        dst = path + cls._backup_suffix
        if not os.path.exists(dst):
            try:
                shutil.copy2(path, dst)
            except OSError as e:
                logging.warning("backup %s failed: %s", path, e)

    @classmethod
    def ensure_kv(cls, path, key, value, sep=" "):
        """等价于 conf 中的 'm' 操作。文件不存在/不可写 -> 告警跳过"""
        key = str(key)
        value = str(value)
        if not os.path.isfile(path) or not os.access(path, os.W_OK):
            logging.warning("file [%s] not existed or writable, skipped: %s", path, key)
            return False
        cls.backup_file(path)
        pattern = re.compile(r"^[ \t]*" + cls._key_pattern(key))
        new_line = key + sep + value
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        matched = False
        for i, line in enumerate(lines):
            if pattern.match(line):
                lines[i] = new_line + "\n"
                matched = True
        if not matched:
            lines.append(new_line + "\n")
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True

    @classmethod
    def check_kv(cls, path, key, value, sep=" "):
        """检查文件中是否存在以 key 开头且整行等于 key<sep>value 的行"""
        key = str(key)
        value = str(value)
        if not os.path.isfile(path):
            return False
        pattern = re.compile(r"^[ \t]*" + cls._key_pattern(key))
        expect = (key + sep + value).strip()
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if pattern.match(line) and line.strip() == expect:
                    return True
        return False

    # ---------------- 细项描述（供 --list 展示与执行日志收集） ----------------

    def describe_steps(self):
        """返回该项所有细项及其检查函数: [(描述, check_fn), ...]
        check_fn() 返回 True 表示该细项已满足(无需加固)。
        默认按 yaml entries 逐条拆分; 含非 kv 操作的项应重写扩展。"""
        config = getattr(self, 'config', {}) or {}
        steps = []
        for e in config.get('entries') or []:
            desc = "配置 {}: {}{}{}".format(e['path'], e['key'], e.get('sep', ' '), e.get('value', ''))
            steps.append((desc, lambda e=e: self.check_kv(
                e['path'], e['key'], e.get('value', ''), e.get('sep', ' '))))
        return steps

    def describe_config(self):
        """把 yaml 配置格式化为可读的加固明细行（供 --list 展示）"""
        config = getattr(self, 'config', {}) or {}
        lines = []
        for e in config.get('entries') or []:
            lines.append("配置 {}: {}{}{}".format(e['path'], e['key'], e.get('sep', ' '), e.get('value', '')))
        if config.get('banner'):
            lines.append('写入警告语: "{}"'.format(config['banner']))
        label_map = [
            ('files', '目标文件'),
            ('cron_paths', '收紧权限 root:root+og-rwx'),
            ('deny_files', '删除文件'),
            ('allow_files', '建立白名单 root:root+og-rwx'),
            ('remove_files', '删除文件'),
            ('rebuild_files', '删除后重建文件'),
        ]
        for key, label in label_map:
            for p in config.get(key) or []:
                lines.append("{}: {}".format(label, p))
        for e in config.get('chmod_entries') or []:
            lines.append("设置权限 {}: {}".format(e['mode'], e['path']))
        if config.get('ctrl_alt_del'):
            lines.append("禁用Ctrl+Alt+Del(删除 {})".format(config['ctrl_alt_del']))
        if config.get('dbus_helper'):
            lines.append("修复属主权限 root:dbus 4750: {}".format(config['dbus_helper']))
        for op in config.get('service_ops') or []:
            lines.append("服务操作: {}".format(op))
        return lines



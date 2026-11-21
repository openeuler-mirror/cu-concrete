"""
department_1_policy 公共基类

- 定义 fix/check/rollback/reset/finalfix/get_des 六个抽象方法, 由各加固项自行实现
- 同时提供 kv 型配置文件的通用工具(与 default_0_policy/base_default_fix.py 同构):

  以 "关键字 + 取值" 型配置文件为例:
    空格分隔格式  sshd_config 等,  如 "LogLevel INFO"
    等号分隔格式  sysconfig 等,    如 "PROMPT=no"

  写入语义: 文件中已存在 key 的生效行 -> 整行替换为 key + sep + value
            不存在 -> 追加到文件末尾
  还原语义: 指定了还原值的写回该值; 未指定的删除该配置行, 回到程序内置默认值
"""
import os
import re
import time
import shutil
import logging
from abc import ABC, abstractmethod


class base_fix(ABC):
    # 同一次运行内所有加固项共用同一备份时间戳
    _backup_suffix = ".cubak." + time.strftime("%Y%m%d%H%M%S")

    def __init__(self):
        pass
    
    @abstractmethod
    def finalfix(self):
        pass

    @abstractmethod
    def fix(self):
        pass

    @abstractmethod
    def check(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
    
    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_des(self):
        pass

    # ---------------- 通用工具 ----------------

    @staticmethod
    def norm(line):
        """归一化一行: 去掉首尾空白, 中间连续空白压成单个空格, 并去掉等号两侧空格"""
        text = ' '.join(str(line).split())
        return re.sub(r'\s*=\s*', '=', text)

    @staticmethod
    def match_key(line, key, sep=' '):
        """判断一行是否为 key 对应的生效配置行(非注释, 关键字大小写不敏感)

        空格分隔格式按空白切分取关键字; 等号等分隔格式取分隔符左侧部分作为关键字。
        """
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            return False
        words = str(key).split()
        if sep and sep != ' ':
            left = stripped.split(sep, 1)[0] if sep in stripped else stripped
            tokens = left.split()
        else:
            tokens = stripped.split()
        if len(tokens) < len(words):
            return False
        for i, word in enumerate(words):
            if tokens[i].lower() != word.lower():
                return False
        return True

    @classmethod
    def backup_file(cls, path):
        """修改前备份为 file.cubak.时间戳, 同一文件同一次运行只备份一次"""
        if not os.path.isfile(path):
            return
        dst = path + cls._backup_suffix
        if not os.path.exists(dst):
            try:
                shutil.copy2(path, dst)
            except OSError as e:
                logging.warning("backup %s failed: %s", path, e)

    @classmethod
    def ensure_file(cls, path):
        """确保文件存在, 不存在则创建(对应 cuos-harden.conf 的 touch 操作)"""
        if os.path.isfile(path):
            return True
        try:
            parent = os.path.dirname(path)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            with open(path, 'a', encoding='utf-8'):
                pass
            return True
        except OSError as e:
            logging.warning("create %s failed: %s", path, e)
            return False

    @classmethod
    def get_kv(cls, path, key, sep=' '):
        """返回 key 的第一个生效配置行(归一化后), 不存在返回 None"""
        if not os.path.isfile(path):
            return None
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if cls.match_key(line, key, sep):
                    return cls.norm(line)
        return None

    @classmethod
    def set_kv(cls, path, key, value, sep=' '):
        """把 key 的所有生效配置行替换为 key + sep + value; 不存在则追加到文件末尾"""
        if not os.path.isfile(path):
            logging.warning("file [%s] not existed, skipped: %s", path, key)
            return False
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        new_lines = []
        matched = False
        for line in lines:
            if cls.match_key(line, key, sep):
                matched = True
                new_lines.append('{}{}{}\n'.format(key, sep, value))
            else:
                new_lines.append(line)
        if not matched:
            new_lines.append('{}{}{}\n'.format(key, sep, value))
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True

    @classmethod
    def remove_kv(cls, path, key, sep=' '):
        """删除 key 的所有生效配置行(注释行保留)"""
        if not os.path.isfile(path):
            logging.warning("file [%s] not existed, skipped: %s", path, key)
            return False
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        new_lines = [line for line in lines if not cls.match_key(line, key, sep)]
        if len(new_lines) == len(lines):
            return False
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True

    @classmethod
    def restore_kv(cls, path, key, value, sep=' '):
        """还原配置项: value 为空则删除该配置行, 回到程序内置默认值; 否则写回该值"""
        if value is None or str(value).strip() == '':
            return cls.remove_kv(path, key, sep)
        return cls.set_kv(path, key, value, sep)

    @classmethod
    def is_hardened(cls, path, key, value, sep=' '):
        """判断文件中 key 的生效值是否已达到期望值"""
        expect = cls.norm('{}{}{}'.format(key, sep, value))
        return cls.get_kv(path, key, sep) == expect

    
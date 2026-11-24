import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import yaml
from base_default_fix import base_default_fix
from base_shell_function import base_shell_function as bsf


class Items_01_Baseline(base_default_fix):
    """安装期安全基线加固(合并项)

    由原 11 个安装期加固项合并而来, 配置在 yaml 中按安全域分类(categories):
      SSH 服务加固            (原 Items_01_SshHarden)
      内核与网络参数          (原 Items_04_SysctlNetwork + Items_05_SysctlKernel)
      PAM 与登录认证          (原 Items_07_PamLockPolicy)
      账户与密码策略          (原 Items_08_PasswordAging)
      Shell 会话与用户环境    (原 Items_11_ShellSession)
      计划任务权限            (原 Items_03_CronAtPerm)
      日志审计                (原 Items_10_LogAudit)
      关键文件与启动目录权限  (原 Items_12_CriticalFilePerm)
      日志文件权限            (原 Items_13_LogFilePerm)
      系统安全对象修复        (原 Items_14_SysObjectFix)

    语义与原各单项保持一致:
      - kv 条目: 文件不存在时判定为未加固; skip_missing=true 的分类视为无需加固
      - 权限类: 路径不存在时跳过(视为无需加固)
      - allow 白名单: 必须存在且属组/其他无权限
      - deny / remove_files: 必须不存在
    说明: 本项只写配置文件, 不执行 systemctl/sysctl 等生效命令,
          配置改写后需由安装流程或管理员重启对应服务使其生效
    """

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_01_Baseline.yaml")
        with open(self.config_file, mode='r', encoding='utf-8') as f:
            self.config = yaml.load(f, Loader=yaml.Loader)
        self.categories = self.config.get('categories') or []

    # ---------------- 内部工具 ----------------

    def _entries(self, cat):
        """返回该分类需要判定的 kv 条目; skip_missing 时跳过不存在的文件"""
        entries = cat.get('entries') or []
        if cat.get('skip_missing'):
            return [e for e in entries if os.path.exists(e['path'])]
        return entries

    @staticmethod
    def _mode_of(path):
        return os.stat(path).st_mode & 0o7777

    # ---------------- 加固 / 检查 ----------------

    def fix(self):
        for cat in self.categories:
            # 1) kv 型配置
            self.ensure_entries(cat.get('entries'))
            # 2) 文件/目录权限收紧
            for e in cat.get('chmod_entries') or []:
                if os.path.exists(e['path']):
                    bsf.chmod_file(str(e['mode']), e['path'])
            # 3) 计划任务路径: root:root + og-rwx
            for path in cat.get('cron_paths') or []:
                if os.path.exists(path):
                    bsf.chown_file('root:root', path)
                    bsf.chmod_file('og-rwx', path)
            # 4) 删除 deny 文件
            for path in cat.get('deny_files') or []:
                if os.path.exists(path):
                    os.remove(path)
            # 5) 建立 allow 白名单
            for path in cat.get('allow_files') or []:
                if not os.path.exists(path):
                    open(path, 'a').close()
                bsf.chown_file('root:root', path)
                bsf.chmod_file('og-rwx', path)
            # 6) 删除指定文件
            for path in cat.get('remove_files') or []:
                if os.path.exists(path):
                    os.remove(path)
            # 7) 修复 setuid 程序的属主与权限位
            dbus = cat.get('dbus_helper')
            if dbus and os.path.exists(dbus):
                bsf.chown_file('root:dbus', dbus)
                bsf.chmod_file('4750', dbus)

    def check(self):
        for cat in self.categories:
            # 1) kv 型配置
            if not self.check_entries(self._entries(cat)):
                return False
            # 2) 文件/目录权限收紧
            for e in cat.get('chmod_entries') or []:
                if os.path.exists(e['path']):
                    if self._mode_of(e['path']) != int(str(e['mode']), 8):
                        return False
            # 3) 计划任务路径: 属组/其他无权限
            for path in cat.get('cron_paths') or []:
                if os.path.exists(path) and (self._mode_of(path) & 0o077):
                    return False
            # 4) deny 文件必须不存在
            for path in cat.get('deny_files') or []:
                if os.path.exists(path):
                    return False
            # 5) allow 白名单必须存在且属组/其他无权限
            for path in cat.get('allow_files') or []:
                if not os.path.exists(path):
                    return False
                if self._mode_of(path) & 0o077:
                    return False
            # 6) remove_files 必须不存在
            for path in cat.get('remove_files') or []:
                if os.path.exists(path):
                    return False
            # 7) dbus helper 权限位必须为 4750
            dbus = cat.get('dbus_helper')
            if dbus and os.path.exists(dbus):
                if self._mode_of(dbus) != 0o4750:
                    return False
        return True

    # ---------------- 明细展示 ----------------

    def describe_steps(self):
        """返回每个细项及其检查函数: [(描述, check_fn), ...]"""
        steps = []
        for cat in self.categories:
            for e in cat.get('entries') or []:
                desc = "配置 {}: {}{}{}".format(e['path'], e['key'], e.get('sep', ' '), e.get('value', ''))
                skip = bool(cat.get('skip_missing'))

                def fn(e=e, skip=skip):
                    # 目标文件不存在时: skip_missing 分类视为无需加固, 其余视为未加固
                    if not os.path.exists(e['path']):
                        return skip
                    return self.check_kv(e['path'], e['key'], e.get('value', ''), e.get('sep', ' '))

                steps.append((desc, fn))
            for e in cat.get('chmod_entries') or []:
                desc = "设置权限 {}: {}".format(e['mode'], e['path'])

                def fn(e=e):
                    if not os.path.exists(e['path']):
                        return True
                    return self._mode_of(e['path']) == int(str(e['mode']), 8)

                steps.append((desc, fn))
            for path in cat.get('cron_paths') or []:
                steps.append(("收紧权限 {}(root:root, og-rwx)".format(path),
                              lambda p=path: not os.path.exists(p) or not (self._mode_of(p) & 0o077)))
            for path in cat.get('deny_files') or []:
                steps.append(("删除 {}".format(path), lambda p=path: not os.path.exists(p)))
            for path in cat.get('allow_files') or []:
                steps.append(("建立白名单 {}(root:root, og-rwx)".format(path),
                              lambda p=path: os.path.exists(p) and not (self._mode_of(p) & 0o077)))
            for path in cat.get('remove_files') or []:
                steps.append(("删除 {}".format(path), lambda p=path: not os.path.exists(p)))
            dbus = cat.get('dbus_helper')
            if dbus:
                steps.append(("修复属主权限 root:dbus 4750: {}".format(dbus),
                              lambda p=dbus: not os.path.exists(p) or self._mode_of(p) == 0o4750))
        return steps

    def describe_config(self):
        """按安全域分类输出加固明细(供 --list 展示)"""
        lines = []
        for cat in self.categories:
            lines.append("[{}] {}".format(cat.get('name', ''), cat.get('desc', '')).rstrip())
            for e in cat.get('entries') or []:
                lines.append("  配置 {}: {}{}{}".format(e['path'], e['key'], e.get('sep', ' '),
                                                       e.get('value', '')))
            for e in cat.get('chmod_entries') or []:
                lines.append("  设置权限 {}: {}".format(e['mode'], e['path']))
            for path in cat.get('cron_paths') or []:
                lines.append("  收紧权限 {}(root:root, og-rwx)".format(path))
            for path in cat.get('deny_files') or []:
                lines.append("  删除 {}".format(path))
            for path in cat.get('allow_files') or []:
                lines.append("  建立白名单 {}(root:root, og-rwx)".format(path))
            for path in cat.get('remove_files') or []:
                lines.append("  删除 {}".format(path))
            dbus = cat.get('dbus_helper')
            if dbus:
                lines.append("  修复属主权限 root:dbus 4750: {}".format(dbus))
        return lines

    def get_des(self):
        return self.config['description']

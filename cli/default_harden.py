"""
default_0_policy 安装期加固加载器/执行器

- 遍历 default_0_policy 下的加固项目录（文件夹名 = .py 文件名，
  如 Items_01_Baseline 或 01_Baseline，两种命名均可识别）
- 按文件路径动态加载模块, 实例化其中的 base_default_fix 子类
- 幂等: check() 为 False 才执行 fix()
- 不弹 whiptail、不写 data_status.pkl（基线加固自身不产生部门状态文件）
- 仅供系统安装时一次性使用, 与 department_*_policy 的 restore/repair 流程完全隔离

命令:
  cu-concrete default_harden --list   列出安装期基线各配置项的加固状态
                                    (用基线项自身的 check 方法逐细项检测, 只读不修改)
  cu-concrete default_harden --all    执行安装期加固(基线 + 部门指定加固项)

安装期加固总流程(cu-concrete default_harden --all):
  步骤1: 执行 default_0_policy/Items_01_Baseline 的 fix 加固
  步骤2: 执行 "cu-concrete harden --list" (扫描全部部门加固项, 生成各部门 data_status.pkl)
  步骤3: 执行 "cu-concrete harden items <安装期指定项>" (等价于 > /dev/null 2>&1)
  步骤4: 删除 flag.txt 与各部门的 data_status.pkl, 让后续手动加固重新走完整扫描
"""
import os
import sys
import time
import importlib.util
import logging
import contextlib

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

POLICY_DIR = os.path.join(project_root, 'default_0_policy')
# 执行日志目录: 放在 default_0_policy 下(安装环境即 /opt/cu-concrete/default_0_policy/logs)
LOG_DIR = os.path.join(POLICY_DIR, 'logs')

# 安装期需要加固的 department_1 加固项(共 24 项)
DEPT1_INSTALL_ITEMS = [
    '1_3', '1_5', '1_6', '1_7', '1_10', '1_11', '1_14', '1_16', '1_18', '1_22',
    '1_23', '1_26', '1_28', '1_30', '1_31', '1_32', '1_33', '1_34', '1_35',
    '1_36', '1_37', '1_38', '1_39', '1_40',
]

# 安装期加固完成后需要清理的临时文件(相对项目根目录)
CLEANUP_FILES = [
    'flag.txt',
    os.path.join('department_1_policy', 'data_status.pkl'),
    os.path.join('department_2_policy', 'data_status.pkl'),
]


class _TeeStream:
    """把写入内容记录到执行日志, 同时丢弃到 devnull(终端保持安静)

    用于承接 harden --list / harden items 内部的标准输出与标准错误,
    使其内容进入安装期执行日志而不是被直接丢弃。
    """

    def __init__(self, logger, devnull):
        self._logger = logger
        self._devnull = devnull

    def write(self, text):
        if self._logger:
            for line in str(text).splitlines():
                if line.strip():
                    self._logger.info(line)
        try:
            self._devnull.write(text)
        except Exception:
            pass
        return len(text)

    def flush(self):
        try:
            self._devnull.flush()
        except Exception:
            pass


class DefaultHardener:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.file_logger = None
        self.log_file_path = None
        self.dept_skip_count = 0
        self.items = self._discover()

    def _discover(self):
        """按名称排序发现 default_0_policy 下的加固项目录（含同名 .py 的子目录）"""
        found = []
        if not os.path.isdir(POLICY_DIR):
            return found
        for name in sorted(os.listdir(POLICY_DIR)):
            path = os.path.join(POLICY_DIR, name)
            if not os.path.isdir(path):
                continue
            if os.path.isfile(os.path.join(path, name + '.py')):
                found.append(name)
        return found

    def _load(self, name):
        """按文件路径加载项模块, 实例化其中的 base_default_fix 子类"""
        for p in (POLICY_DIR, os.path.join(POLICY_DIR, name)):
            if p not in sys.path:
                sys.path.insert(0, p)
        path = os.path.join(POLICY_DIR, name, name + '.py')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # 基类从已加载模块的命名空间中取得(模块顶层已导入该基类)
        base_default_fix = getattr(module, 'base_default_fix', None)
        if base_default_fix is None:
            raise ImportError("{} 中未找到 base_default_fix 基类".format(name))
        for attr in vars(module).values():
            if isinstance(attr, type) and issubclass(attr, base_default_fix) and attr is not base_default_fix:
                return attr()
        raise ImportError("{} 中未找到 base_default_fix 子类".format(name))

    # ---------------- 安装期总流程 ----------------

    def list_items(self):
        """列出安装期基线各细项的加固状态

        使用基线项自身的 check 方法逐细项检测(default_0_policy 下每个加固项的所有配置项),
        输出格式对齐 "cu-concrete harden --list"。
        """
        print("正在检测安装期基线加固状态...")
        if not self.items:
            print("没有找到安装期加固项")
            return
        total, hardened = 0, 0
        for name in self.items:
            try:
                obj = self._load(name)
            except Exception as e:
                print("[warn] {} : {}".format(name, e))
                self.logger.exception("default_harden list %s failed", name)
                continue
            print()
            print("{} - {}".format(name, obj.get_des()))
            try:
                steps = obj.describe_steps()
            except Exception as e:
                print("  [warn] 无法获取加固明细: {}".format(e))
                self.logger.exception("default_harden describe %s failed", name)
                continue
            for desc, fn in steps:
                total += 1
                ok, err = self._safe_check(fn)
                if ok:
                    hardened += 1
                    print("  [已加固] {}".format(desc))
                else:
                    print("  [未加固] {}".format(desc))
                    if err:
                        print("           [检查异常] {}".format(err))
        print()
        print("-" * 50)
        print("细项总数: {}, 已加固: {}, 未加固: {}".format(total, hardened, total - hardened))

    def harden_all(self):
        """安装期加固: 基线加固 + 部门指定加固项, 结束后清理临时文件"""
        self.file_logger = self._setup_file_logger()

        # 步骤1: 安装期基线加固(default_0_policy/Items_01_Baseline)
        self._harden(self.items, source='--all')

        # 步骤2 + 步骤3: 部门指定加固项
        ok, failed = self._harden_dept_items()

        # 步骤4: 清理安装期临时文件
        self._cleanup_install_files()

        # 汇总
        self._out("======== 安装期加固汇总 ========")
        self._out("部门指定加固项: success {} 个, warn {} 个, 已加固跳过 {} 个".format(
            ok, failed, self.dept_skip_count))
        self._out("执行日志: {}".format(self.log_file_path or '(未生成)'))

    @contextlib.contextmanager
    def _capture_to_log(self):
        """执行期间把标准输出与标准错误写入执行日志, 终端保持安静

        等价于命令行上的 > /dev/null 2>&1, 但内容会留在安装期执行日志中便于排查。
        """
        devnull = open(os.devnull, 'w', encoding='utf-8')
        stream = _TeeStream(self.file_logger, devnull)
        try:
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                yield
        finally:
            devnull.close()

    def _out(self, msg):
        """同时输出到控制台与执行日志文件"""
        print(msg)
        if self.file_logger:
            self.file_logger.info(msg)

    def _ensure_dept_status_pkl(self):
        """确保各部门的 data_status.pkl 存在

        harden items 依赖各部门 data_status.pkl(由 harden --list 的完整扫描生成),
        而 harden --list 在 flag.txt 已存在(flag=2)时只读取 pkl 不会重新生成,
        因此这里在 pkl 缺失时先清掉 flag.txt, 让 --list 走一次完整扫描。
        """
        pkls = [os.path.join(project_root, 'department_{}_policy'.format(dep), 'data_status.pkl')
                for dep in (1, 2)]
        if all(os.path.exists(p) for p in pkls):
            return
        flag_path = os.path.join(project_root, 'flag.txt')
        if os.path.exists(flag_path):
            try:
                os.remove(flag_path)
                self._out("已清除 flag.txt, 触发一次完整的加固项扫描")
            except OSError as e:
                self.logger.warning("删除 flag.txt 失败: %s", e)

    def _harden_dept_items(self):
        """执行安装期指定的部门加固项

        等价于依次执行:
          cu-concrete harden --list > /dev/null 2>&1
          cu-concrete harden items 1_3,1_5,... > /dev/null 2>&1
        与命令行的唯一差异: 输出写入安装期执行日志而非终端, 且逐项记录成功/失败。
        返回 (成功数, 失败数)
        """
        if hasattr(os, 'geteuid') and os.geteuid() != 0:
            print("错误: 安装期加固需要 root 权限执行")
            sys.exit(1)

        from cli.harden import Hardener
        hardener = Hardener(self.logger)

        # 步骤2: 扫描全部部门加固项, 生成各部门 data_status.pkl
        self._ensure_dept_status_pkl()
        self._out("======== 步骤2: 扫描全部部门加固项 ========")
        try:
            with self._capture_to_log():
                hardener.list_items()
        except Exception as e:
            self.logger.exception("扫描部门加固项失败")
            self._out("[warn] 扫描部门加固项: {}".format(e))
            sys.exit(1)

        # 步骤3: 执行安装期指定的加固项, 逐项记录成功/失败
        self._out("======== 步骤3: 执行安装期指定加固项(目标 {} 个) ========".format(len(DEPT1_INSTALL_ITEMS)))
        try:
            ok, failed = self._execute_dept_items(hardener)
        except Exception as e:
            self.logger.exception("执行安装期指定加固项失败")
            self._out("[warn] 执行安装期指定加固项: {}".format(e))
            sys.exit(1)

        # 复核结论已在 _execute_dept_items 内逐项输出(加固后立即用同一实例的 check() 复核)
        return ok, failed

    def _execute_dept_items(self, hardener):
        """逐个执行安装期指定的部门加固项, 返回 (成功数, 失败数)

        实例来源与 "cu-concrete harden items" 完全一致(读取各部门 data_status.pkl,
        只取状态为未加固的项), 区别是逐项把成功/失败写入安装期执行日志,
        并在每个项加固完成后立即用该项自身的 check() 复核。

        注: 复核必须复用同一个实例, 不能重新加载模块另建实例 ——
            各目录下存在同名模块(base_fix/base_shell/base_shell_function),
            重新加载时可能拿到与加固阶段不同的基类, 导致复核结论失真。
        """
        import action_logger
        instance_tuple = hardener.checker.sec_checklist()
        available = instance_tuple[0] if instance_tuple else []
        rb_available = instance_tuple[1] if len(instance_tuple) > 1 else []
        target_ids = set(DEPT1_INSTALL_ITEMS)
        instances = []
        for _desc, instance in available[1].items():
            dep_id = "{}_{}".format(instance.config['dep'], instance.config['id'])
            if dep_id in target_ids:
                instances.append(instance)
        instances.sort(key=lambda i: (i.config['dep'], i.config['id']))
        # 目标项中未进入可加固列表的项: 已加固(扫描阶段 check 通过, 跳过) 或 扫描时检查异常
        todo_ids = {"{}_{}".format(i.config['dep'], i.config['id']) for i in instances}
        done_ids = set()
        if rb_available:
            for _desc, instance in rb_available[1].items():
                done_ids.add("{}_{}".format(instance.config['dep'], instance.config['id']))
        # 复核结果: 已达标(跳过) 与 加固后复核通过
        recheck_ok, recheck_ng = [], []
        skip_ids = [i for i in DEPT1_INSTALL_ITEMS if i not in todo_ids and i in done_ids]
        missing_ids = [i for i in DEPT1_INSTALL_ITEMS if i not in todo_ids and i not in done_ids]
        self.dept_skip_count = len(skip_ids)
        self._out("  扫描结果: 待加固 {} 个, 已处于加固状态跳过 {} 个, 未在扫描结果中找到 {} 个".format(
            len(todo_ids), len(skip_ids), len(missing_ids)))
        for item_id in DEPT1_INSTALL_ITEMS:
            if item_id in todo_ids:
                continue
            if item_id in done_ids:
                self._out("  [skip] {} 已处于加固状态, 无需加固".format(item_id))
                recheck_ok.append(item_id)
            else:
                self._out("  [warn] {} 未在扫描结果中找到(该项检查可能异常)".format(item_id))
                recheck_ng.append(item_id)
        if not instances:
            self._out("[warn] 没有匹配到安装期指定的可加固项")
            return 0, len(target_ids)

        action_logger.log_start("安装期加固", instances)
        succeeded, failed = [], []
        for index, instance in enumerate(instances):
            dep_id = "{}_{}".format(instance.config['dep'], instance.config['id'])
            try:
                desc = instance.get_des()
            except Exception:
                desc = ''
            action_logger.log_item_begin("安装期加固", instance)
            self._out("  [{}/{}] 正在加固 {} - {}".format(index + 1, len(instances), dep_id, desc))
            try:
                instance.fix()
            except Exception as e:
                failed.append((instance, e))
                action_logger.log_item_failure("安装期加固", instance, e)
                action_logger.mark_failed(instance)
                self._out("  [warn] {} - {} : {}".format(dep_id, desc, e))
                if self.file_logger:
                    self.file_logger.exception("安装期加固 %s 异常详情", dep_id)
                self.logger.exception("安装期加固 %s failed", dep_id)
                recheck_ng.append(dep_id)
                continue
            # 加固完成后立即用该项自身的 check() 复核(与加固阶段同一实例)
            try:
                passed = bool(instance.check())
            except Exception as e:
                passed = False
                self._out("  [warn] {} 复核异常: {}".format(dep_id, e))
                if self.file_logger:
                    self.file_logger.exception("安装期加固 %s 复核异常", dep_id)
                self.logger.warning("复核 %s 异常: %s", dep_id, e)
            if passed:
                succeeded.append(instance)
                action_logger.log_item_success("安装期加固", instance)
                self._out("  [success] {} - {}".format(dep_id, desc))
                recheck_ok.append(dep_id)
            else:
                failed.append((instance, '加固后复核未通过'))
                action_logger.log_item_failure("安装期加固", instance, '加固后复核未通过')
                action_logger.mark_failed(instance)
                self._out("  [warn] {} - {} (加固后复核未通过)".format(dep_id, desc))
                recheck_ng.append(dep_id)
        action_logger.log_summary("安装期加固", succeeded, failed)
        self._out("执行结果: success {} 个, warn {} 个".format(len(succeeded), len(failed)))
        # 逐项复核结论
        self._out("======== 安装期指定加固项复核 ========")
        self._out("安装期指定加固项复核: 已加固 {} 个, 未通过 {} 个".format(
            len(recheck_ok), len(recheck_ng)))
        for item_id in DEPT1_INSTALL_ITEMS:
            if item_id in recheck_ok:
                self._out("  [success] {} 已加固".format(item_id))
            else:
                self._out("  [warn] {} 未通过".format(item_id))
        return len(succeeded), len(failed)

    def _cleanup_install_files(self):
        """删除安装期加固产生的临时文件: flag.txt 与各部门 data_status.pkl"""
        self._out("======== 清理安装期临时文件 ========")
        for rel in CLEANUP_FILES:
            path = os.path.join(project_root, rel)
            try:
                if os.path.exists(path):
                    os.remove(path)
                    self._out("已删除: {}".format(path))
            except OSError as e:
                self.logger.warning("删除 %s 失败: %s", path, e)
                self._out("[warn] 删除异常: {} ({})".format(path, e))

    # ---------------- 基线加固内部实现 ----------------

    @staticmethod
    def _safe_check(fn):
        """执行细项检查函数, 返回 (是否满足, 异常信息)"""
        try:
            return bool(fn()), None
        except Exception as e:
            return False, str(e)

    def _setup_file_logger(self):
        """创建执行日志文件(/opt/cu-concrete/default_0_policy/logs), 失败时仅输出到控制台"""
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            log_file = os.path.join(LOG_DIR, 'default_harden_{}.log'.format(
                time.strftime('%Y%m%d_%H%M%S')))
            logger = logging.getLogger('default_harden_exec')
            logger.setLevel(logging.INFO)
            logger.propagate = False
            # 清理旧 handler（同进程重复执行时避免文件句柄泄露）
            for h in logger.handlers[:]:
                h.close()
                logger.removeHandler(h)
            handler = logging.FileHandler(log_file, encoding='utf-8')
            handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s',
                                                  datefmt='%Y-%m-%d %H:%M:%S'))
            logger.addHandler(handler)
            # 日志头部: 记录本次执行的命令与范围, 便于事后追溯
            logger.info("=" * 60)
            logger.info("cu-concrete default_harden --all 执行日志")
            logger.info("开始时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S')))
            logger.info("项目根目录: {}".format(project_root))
            logger.info("基线加固项: {}".format(', '.join(self.items) or '(无)'))
            logger.info("部门指定加固项({}个): {}".format(
                len(DEPT1_INSTALL_ITEMS), ','.join(DEPT1_INSTALL_ITEMS)))
            logger.info("=" * 60)
            self.log_file_path = log_file
            print("日志文件: {}".format(log_file))
            return logger
        except OSError as e:
            print("警告: 无法创建日志文件({}), 仅输出到控制台".format(e))
            return None

    def _harden(self, names, source=''):
        if hasattr(os, 'geteuid') and os.geteuid() != 0:
            print("错误: 安装期加固需要 root 权限执行")
            sys.exit(1)
        if not names:
            print("没有需要执行的加固项")
            return
        if self.file_logger is None:
            self.file_logger = self._setup_file_logger()

        def out(msg):
            self._out(msg)

        if source:
            out("执行命令: cu-concrete default_harden {}".format(source))
        ok, skipped, failed = 0, 0, 0
        failed_names = []
        out("======== 安装期安全基线加固开始 ========")
        for name in names:
            try:
                obj = self._load(name)
                steps = obj.describe_steps()
                unmet_idx = []
                for i, (d, f) in enumerate(steps):
                    ok_flag, err = self._safe_check(f)
                    if not ok_flag:
                        unmet_idx.append(i)
                        if err:
                            out("  - [warn] 检查异常: {} : {}".format(d, err))
                if not unmet_idx:
                    out("[skip] {} 已处于加固状态, 无需加固".format(name))
                    for d, _ in steps:
                        out("  - [已加固] {}".format(d))
                    skipped += 1
                    continue
                out("[执行] {} （{} 个细项待加固, {} 个细项已加固）".format(
                    name, len(unmet_idx), len(steps) - len(unmet_idx)))
                # 已加固的细项同样输出, 便于看出本次只处理了哪些细项
                for i, (d, _fn) in enumerate(steps):
                    if i in unmet_idx:
                        out("  - [未加固] {}".format(d))
                    else:
                        out("  - [已加固] {}".format(d))
                obj.fix()
                # 逐项复核: fix 后仍不满足的细项记为失败
                failed_idx = []
                for i in unmet_idx:
                    ok_flag, err = self._safe_check(steps[i][1])
                    if not ok_flag:
                        failed_idx.append(i)
                        if err:
                            out("  - [检查异常] {} : {}".format(steps[i][0], err))
                for i in unmet_idx:
                    mark = "[warn]" if i in failed_idx else "[success]"
                    out("  - {} {}".format(mark, steps[i][0]))
                if not failed_idx:
                    out("[success] {}".format(name))
                    ok += 1
                else:
                    out("[warn] {} 有 {} 个细项未通过, 请人工确认".format(name, len(failed_idx)))
                    failed += 1
                    failed_names.append(name)
            except Exception as e:
                out("[warn] {} : {}".format(name, e))
                self.logger.exception("default_harden %s failed", name)
                failed += 1
                failed_names.append(name)
        if failed_names:
            out("存在未通过细项的加固项: {}".format(', '.join(failed_names)))
        out("======== 结束: success {} / 跳过 {} / warn {} ========".format(ok, skipped, failed))
        if failed:
            sys.exit(1)

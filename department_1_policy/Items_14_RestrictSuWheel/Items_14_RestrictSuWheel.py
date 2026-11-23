import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import json
import yaml
import time
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_14_RestrictSuWheel(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_14_RestrictSuWheel.yaml")
        with open(file=self.config_file,mode='r+',encoding='utf-8') as f :
            config = yaml.load(f,Loader = yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None

    def finalfix(self):
        self.status=2
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=2
        self.status_form.to_pickle(self.pkl_file)

    def fix(self):
        self.status = 1
        # 每次加固前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)
        su_path = self.config['query']['path'][0]
        defs_path = self.config['query']['path'][1]
        # 备份(仅作人工兜底, rollback 不再用它整体覆盖, 避免回滚掉安装期基线)
        bsf.cp_shell(su_path, su_path+'.bak')
        bsf.cp_shell(defs_path, defs_path+'.bak')

        # 1) /etc/pam.d/su: 确保存在未被注释的 pam_wheel.so use_uid 标准行
        #    写入的是 query.value(标准配置行), 不再把 query.form(正则原文)写进文件
        target = self.config['query']['value'][0]
        result = bsf.grep_shell(self.config['query']['form'][0], su_path)
        if len(result[0]) == 0:
            bsf.append_line(target, su_path)
        else:
            for line in result[0].splitlines():
                line = line.strip()
                if not line:
                    continue
                if line != target:
                    # 注释行/其它写法 -> 规范为标准行
                    bsf.sed_shell(line, target, su_path)

        # 2) /etc/pam.d/su: 补齐 pam_rootok.so(root执行su的豁免, 缺失会导致root也无法su)
        rootok = self.config['query']['value'][2]
        rootok_result = bsf.grep_shell(self.config['query']['form'][2], su_path)
        if len(rootok_result[0]) == 0:
            bsf.append_line(rootok, su_path)
        else:
            for line in rootok_result[0].splitlines():
                line = line.strip()
                if not line:
                    continue
                if line != rootok:
                    # 注释行/其它写法 -> 规范为标准行
                    bsf.sed_shell(line, rootok, su_path)

        # 3) /etc/login.defs: 确保存在未被注释的 SU_WHEEL_ONLY yes 标准行
        defs_target = self.config['query']['value'][1]
        defs_result = bsf.grep_shell(self.config['query']['form'][1], defs_path)
        if len(defs_result[0]) == 0:
            bsf.append_line(defs_target, defs_path)
        else:
            for line in defs_result[0].splitlines():
                line = line.strip()
                if not line:
                    continue
                if line != defs_target:
                    # 注释行/其它写法 -> 规范为标准行
                    bsf.sed_shell(line, defs_target, defs_path)
        self.finalfix()

    def check(self):
        # 1) /etc/pam.d/su 中必须有未被注释、且内容规范的 pam_wheel.so use_uid 行
        target = self.config['query']['value'][0]
        result = bsf.grep_shell(self.config['query']['form'][0], self.config['query']['path'][0])
        if len(result[0]) == 0:
            return False
        for line in result[0].splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                return False          # 注释行/空行, 视为未加固
            if line != target:
                return False          # 行内容不规范, 视为未加固
        # 2) /etc/pam.d/su 中必须有未被注释、且内容规范的 pam_rootok.so 行
        rootok = self.config['query']['value'][2]
        rootok_result = bsf.grep_shell(self.config['query']['form'][2], self.config['query']['path'][2])
        if len(rootok_result[0]) == 0:
            return False
        for line in rootok_result[0].splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                return False          # 注释行/空行, 视为未加固
            if line != rootok:
                return False          # 行内容不规范, 视为未加固
        # 3) /etc/login.defs 中必须有未被注释、且内容规范的 SU_WHEEL_ONLY yes 行
        defs_target = self.config['query']['value'][1]
        result1 = bsf.grep_shell(self.config['query']['form'][1], self.config['query']['path'][1])
        if len(result1[0]) == 0:
            return False
        for line in result1[0].splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                return False          # 注释行/空行, 视为未加固
            if line != defs_target:
                return False          # 行内容不规范, 视为未加固
        return True
                
    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        # 不再整体覆盖 /etc/pam.d/su(会把 pam_rootok.so 一并回滚掉, 导致 root 无法 su),
        # 改为把本项写入的 pam_wheel 行注释掉; pam_rootok 行保留, 维持 root 的 su 豁免
        su_path = self.config['query']['path'][0]
        target = self.config['query']['value'][0]
        result = bsf.grep_shell(self.config['query']['form'][0], su_path)
        for line in result[0].splitlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith('#'):
                # 注释掉本项写入的 pam_wheel 行(撤销"仅wheel组可su"的限制)
                bsf.sed_shell(line, '#'+target, su_path)
        bsf.remove_line(self.config['query']['value'][1], self.config['query']['path'][1])
        result = self.check()
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description
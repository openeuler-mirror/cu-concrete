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
class Items_07_SetLoginFailLock(base_fix):
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_07_SetLoginFailLock.yaml")
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
        after = self.config['harden_after']['value']
        # 三条 PAM 行: 按 'pam_faillock.so + 控制位(preauth/authfail/authsucc)' 定位现有行,
        # 整行替换为加固后的标准行; 定位式里不含 [default=die], 避开 sed 把方括号当 ERE 字符类
        # system-auth 与 password-auth 两个文件都要加固
        for path in self.config['query']['path']:
            for idx, ctrl in ((1, 'preauth'), (2, 'authfail'), (3, 'authsucc')):
                form = '^.*pam_faillock\\.so.*{}.*$'.format(ctrl)
                flag = bsf.grep_shell(form, path)
                if len(flag[0]) == 0:
                    # 没有该控制位 -> 追加标准行
                    bsf.append_line(after[idx], path)
                elif flag[0].strip() != after[idx]:
                    # 已有该行但内容不是标准行 -> 整行替换(已是标准行则跳过, 不做无谓改写)
                    bsf.sed_shell(form, after[idx], path)
        self.finalfix()

    def check(self):
        # check() 返回 True = 已加固; 返回 False = 未加固
        # harden_after.value[0] 是参数片段, 不能整行比较, 只校验 value[1..3] 三条完整 PAM 行
        except_value = True
        for path in self.config['query']['path']:
            for idx in (1, 2, 3):
                expect = self.config['harden_after']['value'][idx]
                # grep -F 固定字符串(不解释 [default=die]), -x 整行完全相等
                # rc=0 命中; rc=1 未命中; rc=2 文件不存在/出错 -> 一律判未加固, 不会抛异常
                result = base_shell(['grep', '-F', '-x', expect, path])
                if result[1] != 0:
                    except_value = False
        return except_value

    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        before = self.config['harden_before']['value']
        # 把三条加固行还原为 harden_before 的三行(deny=3 / unlock_time=60)
        for path in self.config['query']['path']:
            for idx, ctrl in ((1, 'preauth'), (2, 'authfail'), (3, 'authsucc')):
                form = '^.*pam_faillock\\.so.*{}.*$'.format(ctrl)
                flag = bsf.grep_shell(form, path)
                if len(flag[0]) != 0 and flag[0].strip() != before[idx]:
                    bsf.sed_shell(form, before[idx], path)
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
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import yaml
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
import Panda as pd
logging.getLogger(__name__)
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_06_SetPasswdComplexity(base_fix):
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_06_SetPasswdComplexity.yaml")
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
        target = self.config['change']['value']
        for path in self.config['query']['path']:
            flag = bsf.grep_shell(self.config['query']['form'], path)
            if len(flag[0]) != 0:
                # 已存在 pam_pwquality 行: 整行规范化为基线参数
                for line in flag[0].splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line != target:
                        bsf.sed_shell(line, target, path)
            else:
                # 不存在该行: 追加标准行, 避免 tee+input 写入时多出一个空行
                bsf.append_line(target, path)
        self.finalfix()

    def check(self):
        # 两个文件中的 pam_pwquality 行都包含全部基线参数, 才视为已加固
        required = self.config['change']['required']
        for path in self.config['query']['path']:
            result = bsf.grep_shell(self.config['query']['form'], path)
            matched = False
            for line in result[0].splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if all(p in line for p in required):
                    matched = True
                    break
            if not matched:
                return False
        return True

    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])

        # 还原: 用还原值替换 pam_pwquality 行(system-auth 与 password-auth 同一还原值)
        recovery = self.config['change']['recovery']
        for path in self.config['query']['path']:
            result = bsf.grep_shell(self.config['query']['form'], path)
            for line in result[0].splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line != recovery:
                    bsf.sed_shell(line, recovery, path)
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


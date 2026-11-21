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
class Items_05_SetPasswdExpiry(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_path = os.path.join(self.current_dir, "Items_05_SetPasswdExpiry.yaml")
        with open(file = self.config_file_path, mode='r+', encoding='utf-8') as f :
            config = yaml.load(f, Loader = yaml.Loader)
        self.pkl_file = os.path.join(os.path.dirname(self.current_dir), 'data_status.pkl')
        self.config = config
        self.status = None

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
        
        # PASS_MAX_DAYS
        PASS_MAX_DAYS_RESULT = bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0]
        if len(PASS_MAX_DAYS_RESULT)!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][0],self.config['query']['path'])[0],self.config['change']['value'][0],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][0],self.config['query']['path'])
        
        # PASS_MIN_DAYS
        PASS_MIN_DAYS_RESULT = bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0]
        if len(PASS_MIN_DAYS_RESULT)!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][1],self.config['query']['path'])[0],self.config['change']['value'][1],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][1],self.config['query']['path'])
        
        # PASS_MIN_LEN
        PASS_MIN_LEN_RESULT = bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0]
        if len(PASS_MIN_LEN_RESULT)!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][2],self.config['query']['path'])[0],self.config['change']['value'][2],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][2],self.config['query']['path'])
        
        # PASS_WARN_AGE
        PASS_WARN_AGE_RESULT = bsf.grep_shell(self.config['query']['form'][3],self.config['query']['path'])[0]
        if len(PASS_WARN_AGE_RESULT)!=0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][3],self.config['query']['path'])[0],self.config['change']['value'][3],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['change']['value'][3],self.config['query']['path'])
        
        self.finalfix()
        
        
    def check(self):
        # except_value = False 代表未加固，可加固; = True 代表已加固，可还原
        except_value = True

        for i in range(len(self.config['query']['form'])):
            # grep 未命中时返回空串, 文件不存在时返回 stderr 文本, 不能直接 split 取值
            line = bsf.grep_shell(self.config['query']['form'][i], self.config['query']['path'])[0] or ''
            lines = [l for l in line.splitlines() if l.strip()]
            parts = lines[0].split() if lines else []
            if len(parts) < 2:
                # 目标键缺失 -> 视为未加固
                except_value = False
                continue
            try:
                current_value = int(parts[1])
            except ValueError:
                # 取值不是数字 -> 视为未加固
                except_value = False
                continue

            # 从 change 配置中解析期望值（取第二列数字）
            expected_parts = self.config['change']['value'][i].split()
            expected_value = int(expected_parts[1])

            if current_value != expected_value:
                except_value = False

        return except_value

    def rollback(self):
        
        if len(bsf.grep_shell(self.config['query']['form'][0], self.config['query']['path'])[0]) != 0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][0], self.config['query']['path'])[0],self.config['recovery']['value'][0],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][0],self.config['query']['path'])
            
        if len(bsf.grep_shell(self.config['query']['form'][1], self.config['query']['path'])[0]) != 0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][1], self.config['query']['path'])[0],self.config['recovery']['value'][1],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][1],self.config['query']['path'])
            
        if len(bsf.grep_shell(self.config['query']['form'][2], self.config['query']['path'])[0]) != 0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][2], self.config['query']['path'])[0],self.config['recovery']['value'][2],self.config['query']['path']) 
        else:
            bsf.append_line(self.config['recovery']['value'][2], self.config['query']['path'])

        if len(bsf.grep_shell(self.config['query']['form'][3], self.config['query']['path'])[0]) != 0:
            bsf.sed_shell(bsf.grep_shell(self.config['query']['form'][3], self.config['query']['path'])[0], self.config['recovery']['value'][3], self.config['query']['path'])
        else:
            bsf.append_line(self.config['recovery']['value'][3], self.config['query']['path'])

        result = self.check()
        
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        
        result = self.check()
        if result==False:   # False 代表可加固状态
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description

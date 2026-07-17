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
class AuditSock_6(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "AuditSock_6.yaml")
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
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=1
        self.status_form.to_pickle(self.pkl_file)
        path=self.config['query']['form']
        with open(self.config['query']['path'][1], 'w') as f:
            f.write(path+'\n')
        bsf.delete_audit_rule()
        bsf.reload_audit_rules()
        data='type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()
        
    def check(self):
        except_value=True
        result=bsf.command_search(self.config['change']['set'])
        if len(result[0])!=0:
            result2=bsf.search_audit_rule(self.config['query']['path'][0])
            if result2[0]==self.config['query']['form']:
                except_value=True
            else:
                except_value=False
        else:
            result3=bsf.pipe_grep_shell(self.config['query']['form'],self.config['query']['path'][0],self.config['change']['value'])
            if result3[0]==self.config['query']['form']:
                except_value=True
            else:
                except_value=False
        return except_value

    def rollback(self):
        bsf.remove_file(self.config['query']['path'][1])
        bsf.delete_audit_rule()
        bsf.reload_audit_rules()
        result = self.check()
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)
            

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description

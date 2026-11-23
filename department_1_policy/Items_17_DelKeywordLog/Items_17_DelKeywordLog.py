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
class Items_17_DelKeywordLog(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_17_DelKeywordLog.yaml")
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
        # 彻底删除：按关键字把命中的日志记录整行删除，且不生成任何备份副本，
        # 被删除的日志内容在系统中永久消失，属于不可逆加固
        for value in self.config['change']['value']:
            bsf.remove_line(value,self.config['query']['path'])
        self.finalfix()

    def check(self):
        except_value=True
        results = [
            bsf.grep_shell(self.config['change']['value'][0], self.config['query']['path']),
            bsf.grep_shell(self.config['change']['value'][1], self.config['query']['path']),
            bsf.grep_shell(self.config['change']['value'][2], self.config['query']['path']),
            bsf.grep_shell(self.config['change']['value'][3], self.config['query']['path']),
            bsf.grep_shell(self.config['change']['value'][4], self.config['query']['path']),
        ]
        for i in results:
            if len(i[0])!=0:
                except_value=False
        return except_value
    
    def rollback(self):
        # 不可还原的原因：
        # 1) fix() 是按关键字把 /var/log/messages 中命中的记录整行彻底删除，并且不保留任何备份副本，
        #    被删除的日志内容在系统中已经永久消失，没有任何数据可以用来恢复；
        # 2) 因此本方法不执行任何还原动作，直接 pass。
        # 状态说明：本方法不做任何状态处理，pkl 中的状态保持 fix() 写入的"已加固"(2)；
        #    由于日志中已无关键字，check() 恒为 True，该项在扫描时也始终被判定为已加固。
        pass

    def reset(self):
        self.rollback()
        self.fix()
    

    def get_des(self):
        description=self.config['description']
        return description

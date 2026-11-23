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
class Items_27_SetSafeAlias(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_27_SetSafeAlias.yaml")
        with open(file=self.config_file,mode='r+',encoding='utf-8') as f :
            config = yaml.load(f,Loader = yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None

    def finalfix(self):
        self.status=2
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=2
        self.status_form.to_pickle(self.pkl_file)

    @staticmethod
    def _sed_escape(text):
        """转义 sed 正则元字符与分隔符, 保证按字面量匹配删除"""
        out=''
        for ch in text:
            if ch in '\\.^$*+?()[]{}|/#&':
                out+='\\'+ch
            else:
                out+=ch
        return out

    def _remove_matched_lines(self, pattern):
        """删除 bashrc 中匹配 pattern 的所有行
        注意: grep_shell 返回 [stdout, returncode], 匹配到的文本是 result[0],
        result[1] 是返回码(0/1), 误用会执行 sed '/0/d' 误删所有含 0 的行
        """
        result=bsf.grep_shell(pattern,self.config['query']['path'])
        if len(result[0])==0:
            return
        for line in result[0].splitlines():
            if not line.strip():
                continue
            bsf.remove_line(self._sed_escape(line),self.config['query']['path'])

    def fix(self):
        self.status = 1
        # 每次加固前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)

        # 逐条 alias 处理: 每条独立判断是否存在, 不存在才追加
        for value in self.config['change']['value']:
            result= bsf.grep_shell(value,self.config['query']['path'])
            if len(result[0])==0:
                cmd=['sudo','tee','-a',self.config['query']['path']]
                base_shell(cmd,input=f'\n{value}')

        self.finalfix()
    
    def check(self):
        except_value=True
        result=bsf.grep_shell(self.config['change']['value'][0],self.config['query']['path'])
        if len(result[0])==0:
            except_value=False
        result=bsf.grep_shell(self.config['change']['value'][1],self.config['query']['path'])
        if len(result[0])==0:
            except_value=False
        return except_value
    
    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])

        # 用 grep 匹配到的文本逐行精确删除(原实现误用 result[1] 返回码,
        # 实际执行 sed '/0/d', 会误删 bashrc 中所有含 0 的行)
        for value in self.config['change']['value']:
            self._remove_matched_lines(value)

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

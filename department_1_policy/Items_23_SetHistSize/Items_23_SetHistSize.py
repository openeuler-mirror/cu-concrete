import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import json
import yaml
import time
import re
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
# import pandas as pd
import Panda as pd
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_23_SetHistSize(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_23_SetHistSize.yaml")
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
        path = self.config['query']['path']
        value = self.config['change']['value']
        # 查找所有以 export HISTSIZE 开头的配置行
        result = bsf.grep_shell(self.config['query']['form'], path)
        matched = [line for line in result[0].splitlines() if line.strip()]
        if len(matched) == 1:
            # 已有唯一一条配置行: 就地把值改写为标准值(已是标准值则不动, 幂等)
            if matched[0] != value:
                bsf.sed_shell(re.escape(matched[0]), value, path)
        else:
            # 没有配置项或存在重复配置行: 清理后在文件末尾空一行追加标准值, 保证只有一条
            for line in set(matched):
                bsf.remove_line(re.escape(line), path)
            # 追加前保证文件以换行结尾, 否则追加的空行会粘到上一行末尾
            try:
                with open(path, 'rb+') as f:
                    f.seek(0, os.SEEK_END)
                    if f.tell() > 0:
                        f.seek(-1, os.SEEK_END)
                        if f.read(1) != b'\n':
                            f.seek(0, os.SEEK_END)
                            f.write(b'\n')
            except OSError as e:
                logging.warning("ensure end newline failed: %s", e)
            # 先追加一个空行, 再在下一行写入标准配置
            bsf.append_line('', path)
            bsf.append_line(value, path)
        # 重新加载 /etc/profile, 使当前会话立即生效
        strs = f'source {path}'
        base_shell(['bash', '-c', strs])
        self.finalfix()
    
    def check(self):
       except_value=True
       result=bsf.grep_shell(self.config['query']['form'],self.config['query']['path'])
       if result[0]!=self.config['change']['value'] or len(result[0])==0:
           except_value=False
       return except_value
    
    def rollback(self):
        # 还原: 删除所有以 export HISTSIZE 开头的配置行(不限取值),
        # 而不是只删除值为 5 的那一行, 避免残留 export HISTSIZE=1000 之类的旧配置
        bsf.remove_line(self.config['query']['form'],self.config['query']['path'])
        strs=f'source {self.config["query"]["path"]}'
        cmd=['bash','-c',strs]
        base_shell(cmd)
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


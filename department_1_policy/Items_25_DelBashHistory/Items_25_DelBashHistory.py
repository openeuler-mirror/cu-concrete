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
import Panda as pd
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_25_DelBashHistory(base_fix):    
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_25_DelBashHistory.yaml")
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
        # 先备份历史文件, 备份只在首次生成, 避免多次加固覆盖原始备份
        if not os.path.exists(self.config['query']['path1']):
            bsf.cp_shell(self.config['query']['path'],self.config['query']['path1'])
        # 清空历史记录: 删除原文件后重新创建空文件
        base_shell(['rm',self.config['query']['path']])
        base_shell(['touch',self.config['query']['path']])

        self.finalfix()
    
    def check(self):
        except_value=True
        cmd=['wc','-c',self.config['query']['path']]
        result=base_shell(cmd)
        # wc -c 输出形如 "0 /path/to/file", 这里只取字节数字段比较:
        # 1) 不再硬编码 /root/.bash_history, 跟随 query.path 配置
        # 2) 不依赖 wc 是否打印文件名以及空格排版, 避免不同实现下判断失效
        parts=result[0].split()
        if not parts or parts[0] != '0':
            except_value=False
        return except_value
    
    def rollback(self):
        # 用备份还原历史文件
        if os.path.exists(self.config['query']['path1']):
            bsf.cp_shell(self.config['query']['path1'], self.config['query']['path'])
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])

        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
        self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description

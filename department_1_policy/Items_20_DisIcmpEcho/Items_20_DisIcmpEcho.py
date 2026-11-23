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
class Items_20_DisIcmpEcho(base_fix):
    def __init__(self):
        super().__init__()

        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_20_DisIcmpEcho.yaml")
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
        # 清理历史遗留的配置行(等号两侧有空格等各种写法), 保证文件里只有一行且为标准值
        bsf.remove_line(self.config['query']['form'], path)
        # 追加前保证文件以换行结尾, 否则新配置会粘到上一行末尾
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
        # 在文件末尾另起一行写入加固值, 配置项始终保留在配置文件中
        bsf.append_line(self.config['change']['value'], path)
        # 立即生效: 重新加载 /etc/sysctl.conf, 让内核运行时值与配置文件一致
        base_shell(['sysctl', '-p'])
        self.finalfix()

    def check(self):
        # 查找是否存在 net.ipv4.icmp_echo_ignore_all 配置行, 没有则视为未加固
        path = self.config['query']['path']
        result = bsf.grep_shell(self.config['query']['form'], path)
        lines = [line.strip() for line in result[0].splitlines() if line.strip()]
        if not lines:
            return False
        # 存在时判断取值是否为 1
        for line in lines:
            if line.startswith('#'):
                continue
            if line.split('=', 1)[-1].strip() == '1':
                return True
        return False

    def rollback(self):
        # 还原: 把配置项显式写回 0
        recovery = self.config['change'].get('recovery', 'net.ipv4.icmp_echo_ignore_all=0')
        path = self.config['query']['path']
        bsf.remove_line(self.config['query']['form'], path)
        # 追加前保证文件以换行结尾, 否则新配置会粘到上一行末尾
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
        # 在文件末尾另起一行写入还原值, 配置项始终保留在配置文件中
        bsf.append_line(recovery, path)
        # 立即生效: 重新加载 /etc/sysctl.conf, 让内核运行时值与配置文件一致
        base_shell(['sysctl', '-p'])
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

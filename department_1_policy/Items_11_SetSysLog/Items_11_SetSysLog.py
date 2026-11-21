import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import yaml
import logging
from base_fix import base_fix
from base_shell import base_shell
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)

#TestCase-部门编号-子加固项名称-子加固项编号
class Items_11_SetSysLog(base_fix):
    """系统日志落盘加固：cron 与 authpriv 日志分别落地到 /var/log/cron 与 /var/log/secure"""

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_11_SetSysLog.yaml")
        with open(file=self.config_file,mode='r+',encoding='utf-8') as f :
            config = yaml.load(f,Loader = yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None
        self.status_form=None

    def finalfix(self):
        self.status=2
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']),'status']=2
        self.status_form.to_pickle(self.pkl_file)

    def fix(self):
        # 每次加固前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status = 1
        self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)
        path = self.config['path']
        for entry in self.config['entries']:
            key = entry['key']
            standard = key + ' ' + entry.get('value', '')
            if not os.path.isfile(path):
                continue
            # newline='' 保留文件原有行尾, splitlines+join 保证写回后末尾有换行
            with open(path, 'r', encoding='utf-8', errors='replace', newline='') as f:
                lines = f.read().splitlines()
            # 已有该 selector 的生效行就整行改写(多余的重复行去掉), 没有就在文件末尾另起一行追加
            new_lines = []
            matched = False
            for line in lines:
                if self.match_key(line, key):
                    if not matched:
                        new_lines.append(standard)
                        matched = True
                else:
                    new_lines.append(line)
            if not matched:
                new_lines.append(standard)
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(('\n'.join(new_lines) + '\n') if new_lines else '')
        # 执行 yaml 中配置的服务操作(重启 rsyslog 使配置生效 + 开机自启)
        for cmd in (self.config.get('commands') or {}).get('fix') or []:
            rc = base_shell(cmd.split())
            if rc[1] != 0:
                logging.warning("command failed: %s", cmd)
        # 复核: 两条规则都写成功才算加固成功
        if self.check():
            self.finalfix()
        else:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def check(self):
        # 两条日志落盘规则都存在才算已加固
        path = self.config['path']
        if not os.path.isfile(path):
            return False
        with open(path, 'r', encoding='utf-8', errors='replace', newline='') as f:
            lines = [l.strip() for l in f.read().splitlines()]
        for entry in self.config['entries']:
            if (entry['key'] + ' ' + entry.get('value', '')) not in lines:
                return False
        return True

    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        path = self.config['path']
        # 还原: 直接删除这两行配置(注释行保留), 回到 rsyslog 内置默认值
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='replace', newline='') as f:
                lines = f.read().splitlines()
            new_lines = []
            for line in lines:
                if not any(self.match_key(line, e['key']) for e in self.config['entries']):
                    new_lines.append(line)
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(('\n'.join(new_lines) + '\n') if new_lines else '')
        # 执行 yaml 中配置的服务操作(重启 rsyslog 使还原后的配置生效)
        for cmd in (self.config.get('commands') or {}).get('rollback') or []:
            rc = base_shell(cmd.split())
            if rc[1] != 0:
                logging.warning("command failed: %s", cmd)
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

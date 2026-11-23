import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_dir)
import yaml
import re
from base_fix import base_fix
from base_shell_function import base_shell_function as bsf
from base_shell import base_shell
import logging
# import pandas as pd
import Panda as pd
logging.getLogger(__name__)
#TestCase-部门编号-子加固项名称-子加固项编号
class Items_22_ModSshPort(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_22_ModSshPort.yaml")
        with open(file=self.config_file,mode='r+',encoding='utf-8') as f :
            config = yaml.load(f,Loader = yaml.Loader)
        self.pkl_file=os.path.join(os.path.dirname(self.current_dir),'data_status.pkl')
        self.config=config
        self.status=None
        # 有效的 Port 指令行(未注释), 用于识别真实生效的端口声明
        self.port_re = re.compile(self.config['query']['form'])

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
        path = self.config['query']['path'][0]
        target = self.config['change']['value'][0]
        # 读取配置文件所有行, 文件不存在时按空列表处理
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.read().splitlines()
        else:
            lines = []
        # 所有生效中的 Port 声明行
        active = [i for i, l in enumerate(lines) if self.port_re.match(l)]
        if active:
            # 第一条改成目标端口, 其余注释掉(避免 sshd 同时监听多个端口)
            lines[active[0]] = target
            for i in active[1:]:
                lines[i] = '#' + lines[i]
        else:
            # 没有 Port 声明(文件不存在或全被注释) -> 追加标准行
            lines.append(target)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        # 防火墙放行新端口并重启 sshd, 新端口生效后再关闭原端口, 避免重启失败时远程断连
        for cmd in self.config['change']['fix_set']:
            base_shell(cmd.split())
        if self.restart_sshd():
            for cmd in self.config['change']['fix_close']:
                base_shell(cmd.split())
        self.finalfix()
    
    def check(self):
        # 生效中的 Port 声明只有一行且等于目标端口, 才算已加固
        path = self.config['query']['path'][0]
        target = self.config['change']['value'][0]
        if not os.path.isfile(path):
            return False
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            active = [l.strip() for l in f.read().splitlines() if self.port_re.match(l)]
        return active == [target]
    
    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        path = self.config['query']['path'][0]
        target = self.config['change']['value'][1]
        # 把目标端口行改回原端口, 其余行保持原样
        # 注: 加固时注释掉的其他 Port 行不恢复(与旧版本行为一致)
        port = self.config['change']['value'][0].split()[-1]
        src_re = re.compile(r'^([ \t]*)Port[ \t]+' + port + r'([ \t]*(#.*)?)?$')
        if os.path.isfile(path):
            lines = []
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for line in f.read().splitlines():
                    m = src_re.match(line)
                    lines.append(m.group(1) + target + (m.group(2) or '') if m else line)
            with open(path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines) + '\n')
        # 防火墙放行原端口并重启 sshd, 原端口生效后再关闭新端口
        for cmd in self.config['change']['rollback_set']:
            base_shell(cmd.split())
        if self.restart_sshd():
            for cmd in self.config['change']['rollback_close']:
                base_shell(cmd.split())
        result = self.check()
        if result == False:
            self.status_form.loc[str(self.config['dep'])+str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def restart_sshd(self):
        # 重启 sshd, 返回是否重启成功; 只有重启成功才允许关闭端口, 避免远程失联
        result = base_shell(['systemctl', 'restart', 'sshd'])
        if result and len(result) > 1 and result[1] == 0:
            return True
        logging.error('sshd 重启失败, 跳过关闭端口操作, 避免远程连接中断: %s', result)
        return False

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description=self.config['description']
        return description

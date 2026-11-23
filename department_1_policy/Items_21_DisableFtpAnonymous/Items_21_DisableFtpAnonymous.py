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
class Items_21_DisableFtpAnonymous(base_fix):    
    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, "Items_21_DisableFtpAnonymous.yaml")
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
        after = self.config['harden_after']['value']
        for path in self.config['query']['path']:
            # vsftpd 未安装(配置文件不存在)则跳过
            if not os.path.isfile(path):
                continue
            # 整行替换为 anonymous_enable=NO
            # ^#*[[:space:]]* : 同时匹配 "#anonymous_enable=YES" 和 "anonymous_enable=YES"
            #                      (发行版默认这行是注释状态, 必须能匹配到才能取消注释)
            # [[:space:]]*=     : 允许等号两侧有空格
            # .*$               : 覆盖整行, 避免只替换片段留下行尾残留
            bsf.sed_shell('^#*[[:space:]]*anonymous_enable[[:space:]]*=.*$', after, path)
        # 重启 vsftpd 使配置生效(未安装则忽略失败)
        result = base_shell(['sudo', 'systemctl', 'restart', 'vsftpd'])
        if result[1] != 0:
            logging.warning("restart vsftpd failed (maybe not installed)")
        self.finalfix()

    def check(self):
        # check() 返回 True = 已加固; 返回 False = 未加固
        # 已加固 = 存在生效的 anonymous_enable=NO
        # 注释掉的行(#anonymous_enable=NO)不算生效 -> 判未加固
        except_value = True
        checked = False
        for path in self.config['query']['path']:
            # vsftpd 未安装(配置文件不存在)视为无需加固, 跳过
            if not os.path.isfile(path):
                continue
            checked = True
            # grep -E: rc=0 命中 / rc=1 未命中 / rc=2 出错
            # 用退出码判断, 避免文件不存在时把 stderr 当成匹配内容而误判 True
            result = bsf.grep_shell(
                '^[^#]*anonymous_enable[[:space:]]*=[[:space:]]*NO[[:space:]]*$', path)
            if result[1] != 0:
                except_value = False
        # 所有 vsftpd 配置文件都不存在 -> 无需加固
        return except_value if checked else True


    def rollback(self):
        # 每次还原前都读取最新的 pkl，避免覆盖其他加固项状态
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        before = self.config['harden_before']['value']
        for path in self.config['query']['path']:
            # vsftpd 未安装(配置文件不存在)则跳过
            if not os.path.isfile(path):
                continue
            # 整行替换回 anonymous_enable=YES(同时把注释去掉, 恢复匿名可登录)
            bsf.sed_shell('^#*[[:space:]]*anonymous_enable[[:space:]]*=.*$', before, path)
        # 重启 vsftpd 使配置生效(未安装则忽略失败)
        result = base_shell(['sudo', 'systemctl', 'restart', 'vsftpd'])
        if result[1] != 0:
            logging.warning("restart vsftpd failed (maybe not installed)")
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

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
import Panda as pd
logging.getLogger(__name__)

class Telent_15(base_fix):

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, 'Telent_15.yaml')
        with open(file=self.config_file, mode='r+', encoding='utf-8') as f:
            config = yaml.load(f, Loader=yaml.Loader)
        self.pkl_file = os.path.join(os.path.dirname(self.current_dir), 'data_status.pkl')
        self.config = config
        self.status = None

    def finalfix(self):
        self.status = 2
        self.status_form.loc[str(self.config['dep']) + str(self.config['id']), 'status'] = 2
        self.status_form.to_pickle(self.pkl_file)

    def fix(self):
        self.status = 1
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        self.status_form.loc[str(self.config['dep']) + str(self.config['id']), 'status'] = 1
        self.status_form.to_pickle(self.pkl_file)
        if os.path.exists(self.config['query']['path']):
            result1 = bsf.grep_shell(self.config['query']['form'], self.config['query']['path'])
            if len(result1[0]) != 0:
                for re in result1[0].splitlines():
                    bsf.sed_shell(re, self.config['change']['value'][0], self.config['query']['path'])
        value1 = self.config['change']['value'][2].split(' ')
        value2 = self.config['change']['value'][3].split(' ')
        base_shell(value1)
        base_shell(value2)
        value3 = base_shell(['rpm', '-qa'])
        value4 = base_shell(['grep', 'openssh'], input=value3[0])
        value5 = base_shell(['wc', '-l'], input=value4[0])
        if len(value5) != 0:
            base_shell(['yum', '-y', 'install'] + value4[0].splitlines())
        result2 = self.config['change']['value'][6].split(' ')
        base_shell(result2)
        result3 = self.config['change']['value'][7].split(' ')
        base_shell(result3)
        data = 'type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()

    def check(self):
        except_value = True
        cmd = ['systemctl', 'is-active', 'telnet.socket']
        result = base_shell(cmd)
        if 'inactive' not in result[0]:
            except_value = False

    def rollback(self):
        pass

    def reset(self):
        pass

    def get_des(self):
        pass
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

class RmToShred_31(base_fix):

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, 'RmToShred_31.yaml')
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
        backup_cmd = ['bash', '-c', 'sudo mv /usr/bin/rm /usr/bin/rm-rule 2>/dev/null || true']
        base_shell(backup_cmd)
        rm_script_content = self.config['change']['value']
        script_cmd = ['sudo', 'tee', '/usr/bin/rm']
        base_shell(script_cmd, input=f'#!/bin/bash\n\n{rm_script_content}')
        chmod_cmd = ['bash', '-c', 'sudo chmod +x /usr/bin/rm']
        base_shell(chmod_cmd)
        data = 'type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()

    def check(self):
        import os
        if not os.path.exists('/usr/bin/rm'):
            return False
        result = bsf.grep_shell(self.config['query']['form'], '/usr/bin/rm')
        if len(result[0]) != 0:
            return True
        else:
            return False

    def rollback(self):
        delete_cmd = ['bash', '-c', 'sudo rm -f /usr/bin/rm']

    def reset(self):
        pass

    def get_des(self):
        pass
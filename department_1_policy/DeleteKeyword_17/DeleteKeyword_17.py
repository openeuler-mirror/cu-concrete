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

class DeleteKeyword_17(base_fix):

    def __init__(self):
        super().__init__()
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.current_dir, 'DeleteKeyword_17.yaml')
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
        bsf.remove_line(self.config['change']['value'][0], self.config['query']['path'])
        bsf.remove_line(self.config['change']['value'][1], self.config['query']['path'])
        bsf.remove_line(self.config['change']['value'][2], self.config['query']['path'])
        bsf.remove_line(self.config['change']['value'][3], self.config['query']['path'])
        bsf.remove_line(self.config['change']['value'][4], self.config['query']['path'])
        data = 'type:fix,des:{}'.format(self.config['description'])
        logging.info(data)
        self.finalfix()

    def check(self):
        except_value = True
        results = [bsf.grep_shell(self.config['change']['value'][0], self.config['query']['path']), bsf.grep_shell(self.config['change']['value'][1], self.config['query']['path']), bsf.grep_shell(self.config['change']['value'][2], self.config['query']['path']), bsf.grep_shell(self.config['change']['value'][3], self.config['query']['path']), bsf.grep_shell(self.config['change']['value'][4], self.config['query']['path'])]
        for i in results:
            if len(i[0]) != 0:
                except_value = False
        return except_value

    def rollback(self):
        pass
        result = self.check()
        if os.path.exists(self.pkl_file):
            self.status_form = pd.read_pickle(self.pkl_file)
        else:
            self.status_form = pd.DataFrame(columns=['status', 'module_name', 'module_path'])
        if result == False:
            self.status_form.loc[str(self.config['dep']) + str(self.config['id']), 'status'] = 0
            self.status_form.to_pickle(self.pkl_file)

    def reset(self):
        self.rollback()
        self.fix()

    def get_des(self):
        description = self.config['description']
        return description
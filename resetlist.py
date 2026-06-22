from whiptail import Whiptail
import time
import os
import subprocess
TITLE = '安全加固工具'
HEIGHT = 25
WIDTH = 60

class resetlist:

    def show_progress(self, title='进度', message='处理中，请稍候...', choice_list=[]):
        """
        使用 whiptail --gauge 显示进度条
        """
        total = len(choice_list)
        cmd = ['whiptail', '--title', title, '--gauge', message, '10', '70', '0']

    def sub_resetlist(self, title, message_func, InstanceTuple):
        pass
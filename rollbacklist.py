from whiptail import Whiptail
import time
import os
import subprocess
TITLE = '安全加固工具'
HEIGHT = 25
WIDTH = 60

class rollbacklist:

    def show_progress(self, title='进度', message='处理中，请稍候...', choice_list=[], InstanceTuple=None):
        """
        使用 whiptail --gauge 显示进度条
        """
        total = len(choice_list)
        cmd = ['whiptail', '--title', title, '--gauge', message, '10', '70', '0']
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for i in range(1, total + 1):
                percent = int(i / total * 100)
                choice_list[i - 1].rollback()
                process.stdin.write(f'{percent}\n'.encode())
                process.stdin.flush()
                time.sleep(0.05)
        finally:
            process.stdin.close()
            process.wait()

    def sub_rollbacklist(self, title, message_func, InstanceTuple):
        pass
from whiptail import Whiptail
import time
import os
import subprocess
import logging
TITLE = "安全加固工具"
HEIGHT = 25
WIDTH = 60

class fixlist:    
    def show_progress(self,title="进度", message="处理中，请稍候...", choice_list=[]):
        """
        使用 whiptail --gauge 显示进度条
        """
        total=len(choice_list)
        
        cmd = ['whiptail', '--title', title, '--gauge', message, '10', '70', '0']
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        try:
            for i in range(1, total+ 1):
                percent = int(i / total * 100)
                choice_list[i-1].fix()
                process.stdin.write(f"{percent}\n".encode())
                process.stdin.flush()
                time.sleep(0.05)
        finally:
            process.stdin.close()
            process.wait()

        # 显示完成提示
        subprocess.run(['whiptail', '--msgbox', '加固完成！请重新启动机器', '10', '40'])

    def sub_fixlist(self,title,message_func,InstanceTuple):
        w = Whiptail(title=TITLE, backtitle=title, height=HEIGHT, width=WIDTH)
        if len(InstanceTuple[0])!=0:
            choice = w.checklist(
                message_func,
                InstanceTuple[0]
            )
            # #获取实例的键
            # key_list=list(InstanceTuple[1].keys())
            #构建实例的字典，键名是dep_id,值是实例
            key_dict={"{}_{}".format(str(v.config['dep']),str(v.config['id'])):v for v in InstanceTuple[1].values()}
            #获取列表的下标
            rollback_list=[x for x in choice[0]]
            #根据键的值获取实例
            choice_list=[key_dict[i] for i in rollback_list]
            if choice[1] == 0:
                self.show_progress("修复中，请稍候...",choice_list=choice_list)
            else:
                return "exit"
        else:
           msgbox = w.msgbox("无可修复项") 
from whiptail import Whiptail
import time
import os
import subprocess
import logging
import action_logger
TITLE = "安全加固工具"
HEIGHT = 25
WIDTH = 60

class fixlist:    
    def show_progress(self,title="进度", message="处理中，请稍候...", choice_list=[]):
        """
        使用 whiptail --gauge 显示进度条
        单项失败只记录日志并继续执行，不中断整个批次
        """
        total=len(choice_list)
        if total == 0:
            return
        
        cmd = ['whiptail', '--title', title, '--gauge', message, '10', '70', '0']
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        succeeded = []
        failed = []
        action_logger.log_start("加固", choice_list)
        try:
            for i in range(1, total+ 1):
                percent = int(i / total * 100)
                instance = choice_list[i-1]
                action_logger.log_item_begin("加固", instance)
                try:
                    instance.fix()
                    succeeded.append(instance)
                    action_logger.log_item_success("加固", instance)
                except Exception as e:
                    failed.append((instance, e))
                    action_logger.log_item_failure("加固", instance, e)
                    action_logger.mark_failed(instance)
                process.stdin.write(f"{percent}\n".encode())
                process.stdin.flush()
                time.sleep(0.05)
        finally:
            process.stdin.close()
            process.wait()

        action_logger.log_summary("加固", succeeded, failed)

        # 显示完成提示
        subprocess.run(['whiptail', '--msgbox', self._summary_msg("加固", succeeded, failed), '20', '70'])

    @staticmethod
    def _summary_msg(action, succeeded, failed):
        """生成带成功/失败统计的提示信息"""
        msg = f"{action}完成！成功 {len(succeeded)} 项，失败 {len(failed)} 项"
        if failed:
            msg += "\n\n失败项：\n"
            for instance, _ in failed:
                dep_id, desc, _name = action_logger.item_info(instance)
                msg += f"{dep_id} {desc}\n"
            msg += "\n详细信息请查看日志文件"
        else:
            msg += "\n请重新启动机器"
        return msg

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

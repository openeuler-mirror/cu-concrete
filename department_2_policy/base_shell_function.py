from base_shell import base_shell,base_pipe_shell
import os
class base_shell_function:
    def __init__(self):
        pass

    @staticmethod
    def append_line(new_line, file):  # 向文件添加一行
        cmd = ['sh', '-c', 'echo "$1" >> "$2"', 'sh', new_line, file]
        return base_shell(cmd)

    #删除特定行
    @staticmethod
    def remove_line(line,file):
        cmd=['sudo','sed','-i',f'/{line}/d',file]
        return base_shell(cmd)
    
    @staticmethod
    def remove_file(file):
        cmd=['rm','-rf',file]
        return base_shell(cmd)
    
    #替换特定行
    @staticmethod
    def sed_shell(old,new,path):
        cmd=['sed','-i',f's@{old}@{new}@g',path]
        return base_shell(cmd)

    @staticmethod
    def grep_shell(form,path):
        cmd=['grep','-E',form,path]
        return base_shell(cmd)
    
    @staticmethod
    def mv_shell(source_path,new_path):
        cmd=["mv","-p","source_path",new_path]
        return base_shell(cmd)

    @staticmethod
    def cp_shell(source_path,new_path):
        cmd=["cp",'-p',source_path,new_path]
        return base_shell(cmd)

    @staticmethod
    def touch_shell(path):
        cmd=["touch",path]
        return base_shell(cmd)

    @staticmethod
    def awk_shell(split,form,path):
        #eg. `awk -F ":" '( $2 == "" ) { print $1 }' /etc/shadow`
        cmd = ["awk", "-F", split, form, path]
        return base_shell(cmd)

    @staticmethod
    def command_search(command):
        cmd=['command','-v',command]
        return base_shell(cmd)
    
    @staticmethod
    def search_audit_rule(form):
        cmd='auditctl -l | grep "{}"'.format(form)
        return base_pipe_shell(cmd)
    
    @staticmethod
    def delete_audit_rule():
        cmd=['auditctl','-D']
        return base_shell(cmd)

    @staticmethod
    def reload_audit_rules():
        cmd=['augenrules','--load']
        return base_shell(cmd)
    
    @staticmethod
    def pipe_grep_shell(form,path,path1):
        cmd='grep -s {} {}| grep {}'.format(form,path,path1)
        return base_pipe_shell(cmd)

    @staticmethod
    def get_service_file(service_name):
        cmd=['systemctl','show','-p','FragmentPath','--value',service_name]
        result = base_shell(cmd)
        if result[1] == 0 and result[0].strip():
            path = result[0].strip()
            if os.path.isfile(path):
                return path
        if os.path.isfile(f'/usr/lib/systemd/system/{service_name}'):
            return f'/usr/lib/systemd/system/{service_name}'
        elif os.path.isfile(f'/etc/systemd/system/{service_name}'):
            return f'/etc/systemd/system/{service_name}'
        elif os.path.isfile(f'/lib/systemd/system/{service_name}'):
            return f'/lib/systemd/system/{service_name}'
        return f"/usr/lib/systemd/system/{service_name}"

    @staticmethod
    def file_owner(path):
        cmd=f'stat -c %U:%G {path}'
        return base_pipe_shell(cmd)

    @staticmethod
    def file_permission(path):
        cmd=f'stat -c %a {path}'
        return base_pipe_shell(cmd) 
        
    @staticmethod
    def chown_file(form,path):
        cmd=f'chown {form} {path}'
        return base_pipe_shell(cmd)

    @staticmethod
    def chmod_file(form,path):
        cmd=f'chmod {form} {path}'
        return base_pipe_shell(cmd)
    
    @staticmethod
    def append_content_to_file(content,path):
        cmd=['sudo','tee','-a',path]
        value=content
        return base_shell(cmd,input=f'\n{value}')

    @staticmethod
    def remove_user_from_group(user,group):
        cmd=['gpasswd','-d',user,group]
        return base_shell(cmd)
    
    @staticmethod
    def append_user_group(group,user):
        cmd=['usermod','-aG',group,user]
        return base_shell(cmd)

    @staticmethod
    def get_group_user(group_name):
        cmd=f'getent group {group_name}'
        return base_pipe_shell(cmd)
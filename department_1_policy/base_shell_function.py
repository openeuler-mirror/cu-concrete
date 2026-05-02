from base_shell import base_shell, base_pipe_shell
import os

class base_shell_function:

    def __init__(self):
        pass

    def append_line(new_line, file):
        cmd = ['sh', '-c', 'echo "$1" >> "$2"', 'sh', new_line, file]
        return base_shell(cmd)

    def remove_line(line, file):
        cmd = ['sudo', 'sed', '-i', f'/{line}/d', file]
        return base_shell(cmd)

    def remove_file(file):
        cmd = ['rm', '-rf', file]
        return base_shell(cmd)

    def sed_shell(old, new, path):
        cmd = ['sed', '-i', f's@{old}@{new}@g', path]
        return base_shell(cmd)

    def grep_shell(form, path):
        cmd = ['grep', '-E', form, path]
        return base_shell(cmd)

    def mv_shell(source_path, new_path):
        cmd = ['mv', '-p', 'source_path', new_path]
        return base_shell(cmd)

    def cp_shell(source_path, new_path):
        cmd = ['cp', '-p', source_path, new_path]
        return base_shell(cmd)

    def touch_shell(path):
        cmd = ['touch', path]
        return base_shell(cmd)

    def awk_shell(split, form, path):
        cmd = ['awk', '-F', split, form, path]
        return base_shell(cmd)

    def command_search(command):
        cmd = ['command', '-v', command]
        return base_shell(cmd)

    def search_audit_rule(form):
        cmd = 'auditctl -l | grep "{}"'.format(form)
        return base_pipe_shell(cmd)

    def delete_audit_rule():
        cmd = ['auditctl', '-D']
        return base_shell(cmd)

    def reload_audit_rules():
        cmd = ['augenrules', '--load']
        return base_shell(cmd)

    def pipe_grep_shell(form, path, path1):
        cmd = 'grep -s {} {}| grep {}'.format(form, path, path1)
        return base_pipe_shell(cmd)

    def get_service_file(service_name):
        cmd = ['systemctl', 'show', '-p', 'FragmentPath', '--value', service_name]
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
        return f'/usr/lib/systemd/system/{service_name}'

    def file_owner(path):
        cmd = f'stat -c %U:%G {path}'
        return base_pipe_shell(cmd)

    def file_permission(path):
        pass

    def chown_file(form, path):
        pass

    def chmod_file(form, path):
        pass

    def append_content_to_file(content, path):
        pass

    def remove_user_from_group(user, group):
        pass

    def append_user_group(group, user):
        pass

    def get_group_user(group_name):
        pass
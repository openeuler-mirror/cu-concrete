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

    def awk_shell(split, form, path):
        pass

    def command_search(command):
        pass

    def search_audit_rule(form):
        pass

    def delete_audit_rule():
        pass

    def reload_audit_rules():
        pass

    def pipe_grep_shell(form, path, path1):
        pass

    def get_service_file(service_name):
        pass

    def file_owner(path):
        pass

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
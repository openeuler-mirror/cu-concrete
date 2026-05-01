import subprocess
import subprocess
import logging

def base_shell(command, input=None, stdin=None, timeout=None):
    try:
        result = subprocess.run(command, capture_output=True, text=True, input=input, stdin=stdin, timeout=timeout, encoding='utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        print('命令执行超时！')
        return ['timeout', -1]
    except Exception as e:
        print(f'命令执行异常: {e}')
        logging.error(f'Command failed: {command}, Error: {e}')
        return ['', 'exception']
    if result.returncode == 0:
        return [result.stdout.strip(), result.returncode]
    elif result.stderr.strip() == '':
        return [result.stdout.strip(), result.returncode]
    else:
        return [result.stderr.strip(), result.returncode]

def base_pipe_shell(command, input=None, stdin=None, timeout=None):
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True, input=input, stdin=stdin, timeout=timeout, encoding='utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        print('命令执行超时！')
        return ['timeout', -1]
    except Exception as e:
        print(f'命令执行异常: {e}')
        logging.error(f'Command failed: {command}, Error: {e}')
        return ['', 'exception']
    if result.returncode == 0:
        return [result.stdout.strip(), result.returncode]
    elif result.stderr.strip() == '':
        return [result.stdout.strip(), result.returncode]
    else:
        return [result.stderr.strip(), result.returncode]
import subprocess

# #1,命令,list。2，字符串标准输入。3，文件读取的标准输入
# def base_shell(command,input=None,stdin=None):
#     try:
#         #capture_output=True 捕获标准输入标准输出。 text=True 将输入输出作为str返回。
#         result = subprocess.run(command, capture_output=True, text=True,input=input,stdin=stdin)
#         # print(result.stdout)
#         # print(result.stderr)
#         # print(result.returncode)
#     except subprocess.TimeoutExpired:
#         print("命令执行超时！")

#     # 检查命令是否成功执行：1，result.stdout标准输出。2，result.stderr标准错误。3，result.returncode执行码，为0成功执行，为1执行错误
#     if result.returncode == 0:
#         # print("Command executed successfully")
#         # print("Standard Output:")
#         # print(result.stdout)
#         return [result.stdout.strip(),result.returncode]
#     else:
#         # print("Command failed with return code:", result.returncode)
#         # print("Standard Error:")
#         # print(result.stderr)
#         return [result.stderr,result.returncode]
import subprocess
import logging

def base_shell(command, input=None, stdin=None, timeout=None):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            input=input,
            stdin=stdin,
            timeout=timeout,  
            encoding='utf-8',
            errors='replace'  
        )
    except subprocess.TimeoutExpired:
        print("命令执行超时！")
        return ['timeout', -1]
    except Exception as e:
        print(f"命令执行异常: {e}")
        logging.error(f"Command failed: {command}, Error: {e}")
        return ['', 'exception']

    #  调试输出
    # print(f"Command: {' '.join(command)}")
    # print(f"Return code: {result.returncode}")
    # print(f"Stdout: {result.stdout}")
    # print(f"Stderr: {result.stderr}")

    if result.returncode == 0:
        return [result.stdout.strip(), result.returncode]
    else:
        if result.stderr.strip() == "":
            # stderr 为空，说明不是错误，只是状态码非零（如 inactive unit）
            return [result.stdout.strip(), result.returncode]
        else:
            # 真正的错误
            return [result.stderr.strip(), result.returncode]
        
def base_pipe_shell(command, input=None, stdin=None, timeout=None):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True,
            input=input,
            stdin=stdin,
            timeout=timeout,  
            encoding='utf-8',
            errors='replace'  
        )
    except subprocess.TimeoutExpired:
        print("命令执行超时！")
        return ['timeout', -1]
    except Exception as e:
        print(f"命令执行异常: {e}")
        logging.error(f"Command failed: {command}, Error: {e}")
        return ['', 'exception']

    #  调试输出
    # print(f"Command: {' '.join(command)}")
    # print(f"Return code: {result.returncode}")
    # print(f"Stdout: {result.stdout}")
    # print(f"Stderr: {result.stderr}")

    if result.returncode == 0:
        return [result.stdout.strip(), result.returncode]
    else:
        if result.stderr.strip() == "":
            # stderr 为空，说明不是错误，只是状态码非零（如 inactive unit）
            return [result.stdout.strip(), result.returncode]
        else:
            # 真正的错误
            return [result.stderr.strip(), result.returncode]
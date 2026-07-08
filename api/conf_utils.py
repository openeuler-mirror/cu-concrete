# 1、conf_data.json: 用来做生成的加固文本，配置映射
# 2、conf_harden.json: 用来做不同模式的加固配置映射

# 本文件做配置关系映射
import json
from django.http import JsonResponse
import yaml
import os
import re
import uuid
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
import logging
# 设置日志
logger = logging.getLogger(__name__)
# 导入统一响应工具
from .response_utils import ApiResponse, CommonResponses
# 导入配置文件
path= Path(__file__).parent
config_path = path / "config.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    CLOUD_POOLS = yaml.load(f,Loader=yaml.Loader)
# 导入配置数据库路径
config_data_path = path / "conf_data.json"
# 模板配件文件
playbook_template_path = path.parent / "data/fetch/playbook_template.yml"

from rest_framework.response import Response
from rest_framework import status

# 查找云池列表
def pool_list(request):
    try:
        # 获取所有云池数据
        all_pools = []
        for pool_id, pool_info in CLOUD_POOLS.items():
            all_pools.append({
                'id': pool_id,
                'name': pool_info['name']
            })
        # 处理分页参数
        try:
            current_param = request.query_params.get('current', '1')
            pageSize_param = request.query_params.get('pageSize', str(len(all_pools)))
            # 验证并转换参数
            current = int(current_param) if current_param.isdigit() and int(current_param) > 0 else 1
            pageSize = int(pageSize_param) if pageSize_param.isdigit() and int(pageSize_param) > 0 else len(all_pools)
        except (ValueError, TypeError):
            # 如果参数转换失败，使用默认值
            current = 1
            pageSize = len(all_pools)
        # 分页处理
        total_count = len(all_pools)
        start_index = (current - 1) * pageSize
        end_index = start_index + pageSize
        paginated_pools = all_pools[start_index:end_index]
        # 构造响应数据
        response_data = {
            'count': total_count,
            'pageIndex': current,
            'pageSize': pageSize,
            'list': paginated_pools
        }
        return CommonResponses.QUERY_SUCCESS(response_data)
    # 异常处理
    except Exception as e:
        logger.error(f"获取云池列表时出错: {str(e)}")
        return ApiResponse.error(f'获取云池列表时出错: {str(e)}', 500)

# 根据pool名获取所有配置文件名
def find_pool_configs(pool_name: str):
    """
    根据云池名获取所有配置文件
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(config_data_path):
            return ApiResponse.error(f'配置文件 {config_data_path} 不存在', 404)
        # 读取并解析JSON文件
        with open(config_data_path, "r", encoding="utf-8") as f:
            conf_data = json.load(f)
        # 根据pool_name查找对应配置
        if pool_name not in conf_data:
            return ApiResponse.error(f'未找到名为 {pool_name} 的云池配置', 404)
        # 获取并返回对应pool的所有配置
        pool_configs = conf_data[pool_name]
        config_file_list = list(pool_configs.keys())
        print("提取的配置文件名列表：", config_file_list)
        
        # 修复1：安全处理文件名，避免索引越界
        formatted_configs = []
        for filename in config_file_list:
            # 安全分割文件名
            parts = filename.split('_')
            
            # 确保至少有两个部分，否则使用整个文件名
            if len(parts) >= 2:
                # 取前两部分作为名称
                name = '_'.join(parts[:2])
            else:
                # 如果只有一个部分或没有下划线，使用整个文件名
                name = filename
                
            # 获取生成时间，如果没有则使用"未知时间"
            generate_time = pool_configs[filename].get("generateTime", "未知时间")
            
            formatted_configs.append({
                'id': filename,
                'name': name,
                'description': f'生成于 {generate_time}'
            })
        
        # 修复2：返回标准分页格式
        return CommonResponses.QUERY_SUCCESS({
            'count': len(formatted_configs),
            'pageIndex': 1,
            'pageSize': len(formatted_configs),
            'list': formatted_configs
        })
    # 异常处理
    except Exception as e:
        logger.error(f"获取配置列表时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'获取所有配置文件时出错: {str(e)}', 500)

# 根据pool名和配置名获取配置文件内容
def find_config_content(pool_name: str, file_name: str):
    try:
        # 检查文件是否存在
        if not os.path.exists(config_data_path):
            return ApiResponse.error(f"配置文件 {config_data_path} 不存在", 404)
        # 读取并解析JSON
        with open(config_data_path, "r", encoding="utf-8") as f:
            conf_data = json.load(f)
        # 检查pool是否存在
        if pool_name not in conf_data:
            return ApiResponse.error(f"未找到云池：{pool_name}", 404)
        pool_data = conf_data[pool_name]
        
        # 检查配置文件是否存在
        if file_name not in pool_data:
            return ApiResponse.error(f"云池 {pool_name} 中未找到配置文件：{file_name}", 404)
        file_data = pool_data[file_name]
        # 获取 serverConfigPath 和 execFilePath 字段
        server_config_path = file_data.get("serverConfigPath")
        exec_file_path = file_data.get("execFilePath")
        
        # 目前根据文件名获取到了文件路径字段 例：exec_file_path = data/fetch/pool-1/playbook_XXX.yml
        # 读取生成的文件内容返回给前端
        with open(server_config_path, 'r', encoding='utf-8') as f:
            ini_content_display = f.read()
        with open(exec_file_path, 'r', encoding='utf-8') as f:
            yml_content_display = f.read()
            
        # 返回前端
        return CommonResponses.OPERATION_SUCCESS({
            'ini_file': str(server_config_path),
            'yml_file': str(exec_file_path),
            'ini_content': ini_content_display,
            'yml_content': yml_content_display,
        })
    except Exception as e:
        return ApiResponse.error(f'获取配置文件内容时出错: {str(e)}', 500)

# 获取级别配置信息
def get_level_conf(harden_models: str):
    try:
        # 获取 conf_harden.json 文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        conf_file_path = os.path.join(base_dir, 'api', 'conf_harden.json')
        
        # 读取配置文件
        with open(conf_file_path, 'r', encoding='utf-8') as f:
            conf_data = json.load(f)
        
        # 获取对应的加固项列表
        harden_items = conf_data['harden-models'].get(harden_models, [])
        
        return JsonResponse({
            'code': 200,
            'message': 'success',
            'data': {
                'harden_items': harden_items
            }
        })
    except Exception as e:
        logger.exception("获取加固模型失败")
        return ApiResponse.error(f'获取级别配置信息时出错: {str(e)}', 500)

# 保存修改后的配置内容到指定文件
def save_conf_content(pool_id: str, file_name: str, ini_content: str, yml_content: str):
    """
    保存修改后的配置内容到指定文件
    Args:
        pool_name (str): 云池名称（如 pool-1）
        file_name (str): 配置文件名（如 playbook_123456.yml）
        ini_content (str): 新的INI文件内容
        yml_content (str): 新的YML文件内容
    Returns:
        Response: 标准响应对象
    """
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_data_path):
            return ApiResponse.error(f'配置数据库 {config_data_path} 不存在', 404)
        
        # 读取配置数据库
        with open(config_data_path, "r", encoding="utf-8") as f:
            conf_data = json.load(f)
        
        # 获取文件路径
        file_data = conf_data[pool_id][file_name]
        server_config_path = file_data.get("serverConfigPath")
        exec_file_path = file_data.get("execFilePath")
        
        # 验证路径是否存在
        if not server_config_path or not os.path.exists(server_config_path):
            return ApiResponse.error(f'INI配置文件路径无效: {server_config_path}', 400)
        if not exec_file_path or not os.path.exists(exec_file_path):
            return ApiResponse.error(f'YML配置文件路径无效: {exec_file_path}', 400)
        
        # 写入新内容
        with open(server_config_path, 'w', encoding='utf-8') as f:
            f.write(ini_content)
            
        with open(exec_file_path, 'w', encoding='utf-8') as f:
            f.write(yml_content)
        
        # 更新生成时间
        conf_data[pool_id][file_name]["generateTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 保存更新后的配置数据库
        with open(config_data_path, "w", encoding="utf-8") as f:
            json.dump(conf_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"配置文件已更新: 云池={pool_id}, 配置={file_name}")
        
        # 返回成功响应
        return JsonResponse({
            'code': 200,
            'message': '配置保存成功',
            'data': {
                'pool_name': pool_id,
                'config_name': file_name
            }
        })
        
    except Exception as e:
        logger.error(f"保存配置内容时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'保存配置内容时出错: {str(e)}', 500)

# 删除配置内容
def delete_conf(pool_id: str, config_name: str):
    try:
        # 检查配置文件是否存在
        if not os.path.exists(config_data_path):
            return ApiResponse.error(f'配置数据库 {config_data_path} 不存在', 404)
        
        # 读取配置数据库
        with open(config_data_path, "r", encoding="utf-8") as f:
            conf_data = json.load(f)
        
        # 检查云池是否存在
        if pool_id not in conf_data:
            return ApiResponse.error(f'未找到云池 {pool_id} 的配置记录', 404)
        
        # 检查配置文件是否存在
        if config_name not in conf_data[pool_id]:
            return ApiResponse.error(f'云池 {pool_id} 中未找到配置文件 {config_name}', 404)
        
        # 从配置数据库中移除记录
        del conf_data[pool_id][config_name]
        
        # 如果云池下没有配置了，可以考虑移除整个云池记录
        # if not conf_data[pool_id]:
        #     del conf_data[pool_id]
        
        # 保存更新后的配置数据库
        with open(config_data_path, "w", encoding="utf-8") as f:
            json.dump(conf_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"配置文件已删除: 云池={pool_id}, 配置={config_name}")
        
        return CommonResponses.OPERATION_SUCCESS({
            'pool_id': pool_id,
            'config_name': config_name
        }, message='配置已成功删除')
        
    except Exception as e:
        logger.error(f"删除配置时出错: {str(e)}", exc_info=True)
        return ApiResponse.error(f'删除配置时出错: {str(e)}', 500)


# 生成配置文件
def generate_config(params_json: dict):
    """
    3、生成配置文件并做持久化归档
    :param generate_mode: 生成模式（对应 harden-model）
    :param pool_name: 云池名（如 pool-1 / pool-2）
    :param servers: 机器IP列表
    :param harden_items: 加固项列表，用于生成文件内容
    :return: 成功返回结果字典，失败返回异常信息
    """
    try:
        # 初始化
        # 将 JSON 字符串解析为字典
        params = json.loads(params_json)
        # 生成时间
        generate_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_str = f"{generate_time}_{uuid.uuid4()}"
        unique_key = hashlib.md5(raw_str.encode()).hexdigest()[:16]
        
        # 定义输出目录
        # output_dir = Path('/opt/cu-concrete/data/fetch')
        output_dir = path.parent / "data/fetch" / params.get("pool_id")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成新的 inventory.ini 文件
        ini_lines = ['[servers]']
        for host in params.get("hosts"):
            host_ip = host.get('ip', host.get('name', ''))
            if host_ip:
                ini_lines.append(host_ip)
        ini_lines.append('')
        ini_lines.append('[servers:vars]')
        ini_lines.append('ansible_user=root')
        ini_lines.append('ansible_port=22')
        ini_lines.append('ansible_ssh_private_key_file=/root/.ssh/id_rsa')
        ini_content = '\n'.join(ini_lines)
        # 写入新的 inventory.ini 文件 唯一生成文件
        ini_file_name = f'inventory_{unique_key}.ini'
        ini_file_path = output_dir / ini_file_name
        with open(ini_file_path, 'w', encoding='utf-8') as f:
            f.write(ini_content)
        
        # 读取源 playbook_template.yml 文件作为模板
        with open(playbook_template_path, 'r', encoding='utf-8') as f:
            yml_content = f.read()
        # harden_items 已经是 dep_id 格式 (如 "1_3", "2_4")
        # 直接拼接成 items 参数
        harden_items_str = ','.join(params.get("harden_items"))
        # 使用正则替换 items 后面的加固项列表
        # 匹配 "python3 main.py harden items " 后面的加固项列表
        pattern = r'(python3 main\.py harden items )([\d_,]+)'
        def replace_items(match):
            return match.group(1) + harden_items_str
        yml_content = re.sub(pattern, replace_items, yml_content)
        
        # 写入新的 playbook.yml 文件 唯一生成文件
        yml_file_name = f'playbook_{unique_key}.yml'
        yml_file_path = output_dir / yml_file_name
        with open(yml_file_path, 'w', encoding='utf-8') as f:
            f.write(yml_content)
        
        # 读取生成的文件内容返回给前端, 文件获取后删除
        with open(ini_file_path, 'r', encoding='utf-8') as f:
            ini_content_display = f.read()
        os.remove(ini_file_path)
        with open(yml_file_path, 'r', encoding='utf-8') as f:
            yml_content_display = f.read()
        os.remove(yml_file_path)
        
        # 返回给前端
        return CommonResponses.OPERATION_SUCCESS({
            'ini_file': str(ini_file_path),
            'yml_file': str(yml_file_path),
            'ini_content': ini_content_display,
            'yml_content': yml_content_display,
            'hosts_count': len(params.get("hosts")),
            'harden_items': harden_items_str
        }, message='配置文件生成并保存成功')
        
    except Exception as e:
        logger.error(f"配置生成异常：: {str(e)}", exc_info=True)
        return ApiResponse.error(f'配置生成异常：: {str(e)}', 500)


# 保存新生成的配置文件
def save_generated_config(params_json: dict):
    '''
    保存新生成的配置文件
    conf_data需要的参数:
        云池名、配置文件名、生成人姓名、加固模式、ini配置文件路径、yml配置文件路径、保存生成的配置文件时间
    '''
    
    try:
        #1、初始化
        # 将 JSON 字符串解析为字典
        params = json.loads(params_json)
        print(params.get("hosts"))
        # 生成时间
        generate_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_str = f"{generate_time}_{uuid.uuid4()}"
        unique_key = hashlib.md5(raw_str.encode()).hexdigest()[:16]
        # 定义输出目录
        output_dir = path.parent / "data/fetch" / params.get("pool_id")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        #2、打开conf_data数据库
        if os.path.exists(config_data_path):
            with open(config_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else : 
            data = {}

        #3、检查配置文件名是否已存在，若存在，则返回错误
        # 修复1：先检查云池是否存在，避免KeyError
        if params.get("pool_id") in data and params.get("config_name") in data[params.get("pool_id")]:
            # 返回错误
            return CommonResponses.OPERATION_FAILED('配置文件名已存在, 请更换名称！')

        #4、将ini和yml内容写入文件中
        # 生成新的 inventory.ini 文件 - 修复hosts处理逻辑
        ini_lines = ['[servers]']
        for host in params.get("hosts"):
            # 修复2：处理host可能是字符串或字典的情况
            if isinstance(host, dict):
                host_ip = host.get('ip', host.get('name', ''))
            else:
                host_ip = host  # 直接使用字符串作为IP
            if host_ip:
                ini_lines.append(host_ip)
        ini_lines.append('')
        ini_lines.append('[servers:vars]')
        ini_lines.append('ansible_user=root')
        ini_lines.append('ansible_port=22')
        ini_lines.append('ansible_ssh_private_key_file=/root/.ssh/id_rsa')
        ini_content = '\n'.join(ini_lines)
        ini_file_name = f'inventory_{unique_key}.ini'
        ini_file_path = output_dir / ini_file_name
        with open(ini_file_path, 'w', encoding='utf-8') as f:
            f.write(params.get("ini_content"))
        # 写入新的 playbook.yml 文件 唯一生成文件
        yml_file_name = params.get("config_name")
        yml_file_path = output_dir / yml_file_name
        with open(yml_file_path, 'w', encoding='utf-8') as f:
            f.write(params.get("yml_content"))
        
        #5、获取参数new_record - 修复文件路径问题
        new_record = {
            "harden-model": params.get("harden_model"),
            "hosts": params.get("hosts"),
            # 修复3：使用生成的文件路径，而不是params中的不存在的字段
            "serverConfigPath": str(ini_file_path),
            "execFilePath": str(yml_file_path),
            "generatePersonName": params.get("generate_person_name"),
            "generateTime": generate_time
        }
        
        #6、将new_record存入数据库中
        if params.get("pool_id") not in data:
            data[params.get("pool_id")] = {}
        data[params.get("pool_id")][yml_file_name] = new_record

        with open(config_data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        #7、返回前端成功
        # 直接拼接成 items 参数
        harden_items_str = ','.join(params.get("harden_items"))
        
        return CommonResponses.OPERATION_SUCCESS({
            'ini_file': str(ini_file_path),
            'yml_file': str(yml_file_path),
            'hosts_count': len(params.get("hosts")),
            'harden_items': params.get("harden_items"),
            "harden_items_str": harden_items_str
        }, message='配置文件保存成功')
        
    except Exception as e:
        # 保持现有的错误处理
        logger.error(f"配置保存异常：{str(e)}", exc_info=True)
        return ApiResponse.error(f'配置保存异常：{str(e)}', 500)
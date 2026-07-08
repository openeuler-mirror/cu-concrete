# cu-concrete - 系统安全加固工具

cu-concrete 是一个用于 Linux 系统的安全加固工具，能够自动化检测和修复系统层面的安全隐患。

## 功能特性

- 提供30+项基础安全加固项
- 支持按部门/模块组织加固策略
- 每个加固项包含检查、修复、回滚逻辑
- 支持 YAML 配置驱动
- 提供图形界面和命令行界面两种操作方式

## 安装方式

### 方法一：直接运行（开发环境）

```bash
# 克隆项目
git clone <repository-url>
cd cu-concrete

# 运行TUI界面
./start_interface.sh

# 运行CLI命令
python cu-concrete-cli.py --help
```

### 方法二：yum安装（推荐，生产环境）

```bash
# 下载项目
yum install cu-concrete

# 安装完成后可在任意位置运行
cu-concrete 
```

## 使用说明

### 图形界面(TUI)

```bash
./start_interface.sh
```

### 命令行界面(CLI)

```bash
# 查看帮助
cu-concrete --help

# 列出可加固项目
cu-concrete harden --list

# 对所有项目执行加固
cu-concrete harden --all

# 对特定项目执行加固
cu-concrete harden CheckRootDir_9 SetCrack_6

# 列出可还原项目
cu-concrete restore --list

# 还原所有项目
cu-concrete restore --all

#远程拉取策略

# 检查是否已有密钥
ls ~/.ssh/id_rsa.pub

# 如果没有，生成一个新的（一路回车用默认设置）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# 复制公钥到主机
ssh-copy-id root@Xxxx

ansible-playbook -i fetch.ini fetch.yml
```



## 项目结构

- `department_1_policy/` - 第一类安全策略
- `department_2_policy/` - 第二类安全策略
- `cli/` - 命令行界面实现
- `interface.py` - 图形界面实现
- `checklist.py` - 检查项管理
- `fixlist.py` - 加固项管理
- `rollbacklist.py` - 还原项管理
- `mappingdes.py` - 策略映射管理

## 技术栈

- Python 3.x
- whiptail (TUI界面)
- YAML (配置文件)

## 注意事项

1. 工具需要root权限运行
2. 在生产环境中使用前请先在测试环境验证
3. 某些加固项可能需要重启系统才能生效

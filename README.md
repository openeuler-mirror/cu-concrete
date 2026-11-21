# cu-concrete - 系统安全加固工具

cu-concrete 用于 Linux 系统的安全加固，自动化检测并修复账号权限、SSH、网络参数、文件权限、审计策略等系统层隐患。提供 **终端界面（TUI）**、**命令行（CLI）**、**Web 平台** 三种操作方式。

## 功能特性

- **66 项加固策略**：安装期基线 1 项（`default_0_policy`）+ 部门一 40 项（`department_1_policy`）+ 部门二 25 项（`department_2_policy`）
- 每项策略均含 **检查 / 加固 / 还原** 三套逻辑，加固后立即复核
- **YAML 驱动**：判定规则、参数、目标文件路径均在策略 YAML 中定义，可自定义
- 支持按项执行、批量执行与还原，适配等保、CIS 等合规要求

## 目录结构

| 路径 | 说明 |
|------|------|
| `default_0_policy/` | 安装期安全基线（1 项，不可还原） |
| `department_1_policy/` | 第一部门加固项（40 项） |
| `department_2_policy/` | 第二部门加固项（25 项） |
| `cli/` | 命令行实现（harden / restore / repair / default_harden） |
| `api/` | Web 后端（Django + DRF），含云池、任务、结果、配置管理接口 |
| `config/` | Django 配置与路由 |
| `templates/` `static_root/` | Web 前端页面与静态资源 |
| `data/` | 配置模板、任务记录、结果 CSV、备份数据 |
| `interface.py` | TUI 终端界面（whiptail） |
| `mappingdes.py` | 策略描述映射 |

每个加固项目录包含三个文件：`Items_XX_名称.py`（逻辑）、`Items_XX_名称.yaml`（配置）、`test_Items_XX_名称.py`（单元测试）。

## 部署

### yum 安装（推荐，生产环境）

```bash
yum install cu-concrete
cu-concrete            # 启动 TUI 界面
cu-concrete --help     # 查看命令帮助
```

安装位置 `/opt/cu-concrete`，`cu-concrete` 为其软链接。

### 源码运行（开发环境）

```bash
git clone <repository-url>
cd cu-concrete
pip install -r requirements.txt

./start_interface.sh          # TUI 界面（需 root）
python3 main.py --help        # CLI
```

### Docker

```bash
docker build -t cu-concrete .
docker run -d -p 8000:8000 cu-concrete
```

## 使用

### TUI 终端界面

```bash
./start_interface.sh
```

主菜单：加固 / 还原 / 修复 / 日志 / 退出。需 root 权限，同一时刻仅允许一个实例。

### CLI 命令行

```bash
python3 main.py harden --list                # 列出可加固项
python3 main.py harden --all                  # 执行全部加固项
python3 main.py harden items 1_9,1_6          # 执行指定项（格式 {dep}_{item_id}）
python3 main.py restore --list                # 列出可还原项
python3 main.py restore --all                 # 还原全部
python3 main.py restore items 1_9,1_6         # 还原指定项
python3 main.py repair --all                  # 系统修复
python3 main.py default_harden --all          # 安装期一次性加固（基线 + 部门一指定 24 项，需 root）
```

> `main.py` 不带参数时启动 TUI，带参数时转交 `cli/main.py`。

### Web 平台

```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

| 地址 | 说明 |
|------|------|
| `http://<host>:8000/` | 管理平台（云池管理、配置生成、任务执行、结果查询） |
| `http://<host>:8000/swagger/` | Swagger 接口文档 |
| `http://<host>:8000/redoc/` | ReDoc 接口文档 |

## 远程批量加固

目标机需配置 SSH 免密（`ssh-copy-id root@<target>`），控制节点需安装 ansible：

```bash
ansible-playbook -i <inventory_xxx.ini> <playbook_xxx.yml>
```

inventory 与 playbook 由「配置生成」页渲染模板生成，详见 `配置说明.md`。

## 依赖

- Python 3.6+
- Django 4.2、djangorestframework、drf-yasg、django-cors-headers、uvicorn
- PyYAML、pandas、numpy
- whiptail（TUI）、ansible（远程执行）

完整清单见 `requirements.txt`。

## 文档

- `配置说明.md` —— 配置文件、模板文件、执行前提
- `API接口文档.md` —— 15 个 HTTP 接口的完整说明

## 注意事项

1. 加固、还原、修复均需 **root 权限**
2. 生产环境使用前请先在测试环境验证
3. 部分加固项（如 SSH 配置、内核参数）需重启系统才能完全生效
4. 单项策略逻辑调整后，请同步运行该目录下的 `test_Items_XX_名称.py`


# PC 管家助手

基于 AI 的 Windows 电脑诊断与管理工具，通过自然语言对话自动调用系统工具解决电脑问题。

## 功能特性

- **自然语言交互**：直接描述问题，AI 自动判断并调用相关工具
- **ReAct 推理模式**：每次执行一个工具，观察结果后再决定下一步
- **按需加载工具**：根据问题类型只加载相关工具类别，节省 token
- **危险操作保护**：写操作/破坏性操作执行前强制用户确认
- **跨会话记忆**：自动提取系统信息和用户偏好保存至 `memory.json`，下次启动自动加载
- **对话轨迹归档**：每次会话结束后保存完整对话记录至 `trajectories/`，超出窗口的历史自动归档
- **兼容多厂商 API**：基于 OpenAI 兼容接口，支持 GPT、DeepSeek、通义等

## 快速开始

**1. 安装依赖**

```bash
pip install openai
```

**2. 配置 API**

编辑 `config.py`，填入你的 API Key、Base URL 和模型名称：

```python
API_KEY  = "sk-xxx"
BASE_URL = "https://api.openai.com/v1"
MODEL    = "gpt-4o"
```

**3. 注入工具定义（仅需运行一次，或新增工具后重新运行）**

```bash
python inject_tool_defs.py
```

**4. 以管理员身份启动**

```bash
python agent.py
```

> 部分工具（如温度查询、驱动重装）需要管理员权限。启动时若非管理员，程序会提示是否提权重启。

## 使用示例

```
你: 为什么电脑打游戏卡？
Assistant: 正在思考...
[调用] get_active_power_plan
[结果] 当前电源计划：节能

[警告] 即将执行高危操作: set_active_power_plan
参数: {"plan_name": "高性能"}
确认执行? (y/n): y
[调用] set_active_power_plan
[结果] 已切换至高性能模式
```

## 会话命令

| 命令 | 说明 |
|------|------|
| `quit` | 退出并保存记忆与对话轨迹 |
| `clear` | 清除当前会话上下文（保留跨会话记忆）|

## 工具类别（12 类，81 个工具）

| 类别 | 说明 |
|------|------|
| `network` | DNS、IP、连接、代理、VPN、WiFi、路由、网络重置 |
| `system` | 磁盘、内存、CPU、温度、电池、BitLocker、防火墙 |
| `process` | 查看/终止进程、启动/停止/重启 Windows 服务 |
| `power` | 查看/切换电源计划 |
| `printer` | 打印机列表、队列、安装、删除、配置 |
| `software` | 已安装软件、卸载、浏览器扩展 |
| `startup` | 查看/启用/禁用开机自启项 |
| `file` | 磁盘清理、大文件扫描、回收站 |
| `security` | 杀毒软件、系统更新、组策略 |
| `hardware` | 驱动、音频服务、摄像头、显示器、设备启用/禁用 |
| `sysconfig` | hosts 文件、虚拟内存、用户账户、USB 存储 |
| `diag` | 蓝屏历史、事件日志、系统健康快照、时间同步 |

## 项目结构

```
PC_MANAGER_AGENT/
├── agent.py              # 主入口 + ReAct 循环 + Spinner
├── tools.py              # 工具加载、意图识别、执行、facts 提取
├── memory.py             # 会话上下文 + 跨会话记忆 + 轨迹归档
├── config.py             # API 配置、工具分类、危险工具列表
├── inject_tool_defs.py   # 一次性脚本：从函数签名生成 TOOL_DEF
├── TOOL_CATALOG.md       # 工具说明文档
├── memory.json           # 运行时生成，跨会话记忆
├── trajectories/         # 运行时生成，对话轨迹归档
├── logs/                 # 运行时生成，每日日志
├── pyscripts/            # Python 工具封装
└── scripts/              # PowerShell 脚本
```"# pc-manager-agent" 

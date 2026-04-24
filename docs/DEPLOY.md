# Agent Evolution System v3 — 详细部署指南

## 环境要求

### 基础环境

| 组件 | 要求 | 说明 |
|------|------|------|
| **操作系统** | Ubuntu 20.04+ / Debian 11+ | 本文档以腾讯云 CVM 为例 |
| **Node.js** | v18.0.0+ | OpenClaw 运行依赖 |
| **Python** | 3.10+ | 评分/分析脚本运行依赖 |
| **内存** | 2GB+ | 推荐 4GB |
| **磁盘** | 10GB+ | 用于日志和记忆存储 |

### 检查当前环境

```bash
node --version   # 需 v18+
python3 --version # 需 3.10+
free -h           # 查看可用内存
df -h /           # 查看磁盘空间
```

---

## Step 1：安装 OpenClaw

```bash
# 通过 npm 全局安装
npm install -g openclaw

# 验证安装
openclaw --version

# 如果遇到权限问题
sudo npm install -g openclaw
```

**或者通过脚本安装**（自动处理依赖）：
```bash
curl -fsSL https://raw.githubusercontent.com/openclaw/openclaw/main/install.sh | bash
```

---

## Step 2：创建工作区结构

```bash
# 创建主工作区
mkdir -p /root/.openclaw/workspace

# 创建各省工作区
mkdir -p /root/.openclaw/workspace-{ada,zen,leo}

# 创建经验存储目录
mkdir -p /root/.openclaw/workspace/.learnings/{experiences,ERRORS.md,LEARNINGS.md,CHANGELOG.md}

# 创建每日记忆目录
mkdir -p /root/.openclaw/workspace/memory/daily
```

---

## Step 3：配置模型提供商

### MiniMax（GLM 模型推荐）

1. 访问 [api.minimax.io](https://api.minimax.io) 注册账号
2. 获取 API Key（GLM-5 系列使用 Coding Plan）
3. 模型端点：`https://open.bigmodel.cn/api/anthropic`（Anthropic Messages 格式）

### DeepSeek

1. 访问 [platform.deepseek.com](https://platform.deepseek.com) 注册
2. 获取 API Key
3. 模型端点：`https://api.deepseek.com/v1`（OpenAI Completions 格式）

### OpenRouter（Gemini 等）

1. 访问 [openrouter.ai/keys](https://openrouter.ai/keys)
2. 获取 API Key
3. 选择模型：`google/gemini-3.1-pro-preview`

---

## Step 4：创建 models.json

创建文件 `/root/.openclaw/models.json`：

```json
{
  "mode": "merge",
  "providers": {
    "minimax": {
      "baseUrl": "https://api.minimax.io/anthropic",
      "apiKey": "YOUR_MINIMAX_API_KEY",
      "api": "anthropic-messages",
      "models": [
        {
          "id": "MiniMax-M2.7",
          "name": "MiniMax M2.7",
          "reasoning": true,
          "input": ["text"],
          "contextWindow": 200000,
          "maxTokens": 8192
        }
      ]
    },
    "deepseek": {
      "baseUrl": "https://api.deepseek.com/v1",
      "apiKey": "YOUR_DEEPSEEK_API_KEY",
      "api": "openai-completions",
      "models": [
        {
          "id": "deepseek-v4-flash",
          "name": "DeepSeek V4 Flash",
          "reasoning": false,
          "input": ["text"],
          "contextWindow": 1000000,
          "maxTokens": 16384
        }
      ]
    },
    "openrouter": {
      "baseUrl": "https://openrouter.ai/api/v1",
      "apiKey": "YOUR_OPENROUTER_API_KEY",
      "api": "openai-completions",
      "models": [
        {
          "id": "google/gemini-3.1-pro-preview",
          "name": "Gemini 3.1 Pro"
        }
      ]
    },
    "bigmodel": {
      "baseUrl": "https://open.bigmodel.cn/api/anthropic",
      "apiKey": "YOUR_BIGMODEL_API_KEY",
      "api": "anthropic-messages",
      "models": [
        {
          "id": "glm-5.1",
          "name": "GLM-5.1",
          "reasoning": true,
          "input": ["text"],
          "contextWindow": 200000,
          "maxTokens": 8192
        },
        {
          "id": "glm-5-turbo",
          "name": "GLM-5 Turbo",
          "reasoning": true,
          "input": ["text"],
          "contextWindow": 200000,
          "maxTokens": 8192
        }
      ]
    }
  }
}
```

---

## Step 5：创建 openclaw.json

创建文件 `/root/.openclaw/openclaw.json`：

```json
{
  "meta": {
    "lastTouchedVersion": "2026.4.21"
  },
  "wizard": {
    "lastRunAt": "2026-04-23T11:30:00.000Z",
    "lastRunCommand": "doctor"
  },
  "models": {
    "mode": "merge"
  },
  "agents": {
    "defaults": {
      "memorySearch": { "enabled": false },
      "compaction": { "mode": "safeguard" }
    },
    "list": [
      {
        "id": "neo",
        "default": true,
        "workspace": "/root/.openclaw/workspace",
        "model": {
          "primary": "deepseek/deepseek-v4-flash",
          "fallbacks": ["minimax/MiniMax-M2.7"]
        }
      },
      {
        "id": "ada",
        "workspace": "/root/.openclaw/workspace-ada",
        "model": {
          "primary": "bigmodel/glm-5.1"
        }
      },
      {
        "id": "zen",
        "workspace": "/root/.openclaw/workspace-zen",
        "model": {
          "primary": "openrouter/google/gemini-3.1-pro-preview"
        }
      },
      {
        "id": "leo",
        "workspace": "/root/.openclaw/workspace-leo",
        "model": {
          "primary": "bigmodel/glm-5-turbo"
        }
      }
    ]
  },
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": ["http://localhost:18789", "http://127.0.0.1:18789"]
    }
  }
}
```

---

## Step 6：配置 IM 通道

### Telegram Bot

1. 在 Telegram 联系 `@BotFather`，创建 Bot，获取 Token
2. 添加配置到 `channels`：

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "YOUR_TELEGRAM_BOT_TOKEN"
    }
  }
}
```

### 飞书 Bot

1. 在[飞书开放平台](https://open.feishu.cn/app)创建企业自建应用
2. 获取 `App ID` 和 `App Secret`
3. 添加配置：

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "appSecret": "YOUR_APP_SECRET"
    }
  }
}
```

### Discord Bot

1. 在 [Discord Developer Portal](https://discord.com/developers/applications) 创建应用
2. 创建 Bot，获取 Token
3. 启用 Message Content Intent
4. 添加配置：

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "botToken": "YOUR_DISCORD_BOT_TOKEN"
    }
  }
}
```

**注意**：合并通道配置时需将各通道配置合并到 `channels` 对象中。

---

## Step 7：配置 systemd 自启动

```bash
mkdir -p ~/.config/systemd/user

# 创建服务文件
cat > ~/.config/systemd/user/openclaw-gateway.service << 'EOF'
[Unit]
Description=OpenClaw Gateway Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/openclaw gateway start
Restart=on-failure
RestartSec=10
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=NODE_ENV=production

[Install]
WantedBy=default.target
EOF

# 重载 systemd 并启用服务
systemctl --user daemon-reload
systemctl --user enable openclaw-gateway.service
systemctl --user start openclaw-gateway.service

# 检查状态
systemctl --user status openclaw-gateway.service
```

---

## Step 8：安装 MemOS（推荐）

MemOS 提供语义记忆检索能力，让 Agent 能够**跨会话记住重要决策和上下文**，是进化系统长期记忆能力的核心支撑。

### 方式一：Docker 部署（推荐）

```bash
# 拉取 MemOS 镜像
docker pull neucrack/memos:latest

# 创建数据目录
mkdir -p ~/memos-data

# 启动 MemOS
docker run -d \
  --name memos \
  --restart always \
  -p 127.0.0.1:18799:5230 \
  -v ~/memos-data:/var/opt/memos \
  neucrack/memos:latest
```

### 方式二：二进制部署

```bash
# 下载最新 release
curl -LO https://github.com/usememos/memos/releases/latest/download/memos-linux-amd64.tar.gz
tar xzf memos-linux-amd64.tar.gz
mv memos-linux-amd64/memos /usr/local/bin/

# 启动
memos --data /var/opt/memos
```

### 配置 MemOS 接入 OpenClaw

```bash
# 在 OpenClaw workspace 中安装 memos-memory-guide skill
openclaw skill install memos-memory-guide

# 或手动复制
mkdir -p /root/.openclaw/workspace/skills/memos-memory-guide
cp -r agent-evolution/skills/memos-memory-guide/* /root/.openclaw/workspace/skills/memos-memory-guide/
```

### MemOS API 配置

MemOS 需要配置 embedding 和 summarizer：

```bash
# 设置 SiliconFlow API（用于 embedding）
export SILICONFLOW_API_KEY=your_siliconflow_api_key

# 设置智谱 API（用于 summarizer）
export ZHIPU_API_KEY=your_zhipu_api_key
```

访问 MemOS 面板：`http://your-server:18799`

---

## Step 11：安装进化系统组件

### 质量评分模块

```bash
# 复制评分模块
cp -r agent-evolution/src/scoreboard.py /root/.openclaw/workspace/skills/emotion-analyzer/src/
chmod +x /root/.openclaw/workspace/skills/emotion-analyzer/src/scoreboard.py

# 初始化追踪文件
cp -r agent-evolution/templates/.learnings/* /root/.openclaw/workspace/.learnings/

# 创建每日评分目录
mkdir -p /root/.openclaw/workspace/memory/daily
```

### 复制工作区模板文件

```bash
# 复制模板文件到主工作区
cp agent-evolution/templates/SOUL.md /root/.openclaw/workspace/SOUL.md
cp agent-evolution/templates/AGENTS.md /root/.openclaw/workspace/AGENTS.md
cp agent-evolution/templates/HEARTBEAT.md /root/.openclaw/workspace/HEARTBEAT.md

# 为各省复制对应模板
cp agent-evolution/templates/SOUL.md /root/.openclaw/workspace-ada/SOUL.md
cp agent-evolution/templates/SOUL.md /root/.openclaw/workspace-zen/SOUL.md
cp agent-evolution/templates/SOUL.md /root/.openclaw/workspace-leo/SOUL.md
```

---

## Step 11：配置心跳集成

### cron 调用方式

`scoreboard.py` 和 `tracker.py` 可通过 cron 定时调用，实现自动巡检。

```bash
# 每 4 小时心跳：评分统计
0 */4 * * * python3 /root/.openclaw/workspace/skills/emotion-analyzer/src/scoreboard.py stats >> /var/log/openclaw-heartbeat.log 2>&1

# 每周晋升检查（周日 UTC 20:00）
0 20 * * 0 python3 /root/.openclaw/workspace/skills/emotion-analyzer/src/tracker.py check >> /var/log/openclaw-weekly.log 2>&1
```

### 心跳巡检流程

每次心跳（cron 触发）执行：

```
1. scoreboard.py stats  → 读取当日评分，判断是否需要人工审核
2. tracker.py check    → 检查晋升阈值，返回需晋升条目
3. tracker.py bump     → 模式出现次数 +1
```

### 路径可移植性

支持环境变量覆盖默认路径（解决 Zen 提出的硬编码问题）：

```bash
# 默认路径
WORKSPACE_DIR=/root/.openclaw/workspace

# 自定义路径（macOS 等场景）
export WORKSPACE_DIR=$HOME/openclaw-workspace
```

### 修复记录（v3.1）

| 日期 | 修复内容 |
|------|---------|
| 2026-04-24 | tracker.py `bump_pattern` 返回真实计数（非固定 1） |
| 2026-04-24 | tracker.py `_promote()` 重写为普通函数，加注释 |
| 2026-04-24 | scoreboard.py 增加 `correction_flag` 标注（需人工审核） |
| 2026-04-24 | scoreboard.py/tracker.py 路径改为环境变量可配置 |
| 2026-04-24 | tracker.py 增加 JSONL 备份文件 |

---

## Step 12：验证部署

```bash
# 1. 启动 Gateway
openclaw gateway start

# 2. 运行健康检查
openclaw doctor

# 3. 测试评分系统
python3 /root/.openclaw/workspace/skills/emotion-analyzer/src/scoreboard.py stats

# 4. 测试晋升检查
python3 /root/.openclaw/workspace/skills/emotion-analyzer/src/tracker.py check

# 5. 检查 Tracker 状态
python3 /root/.openclaw/workspace/skills/emotion-analyzer/src/tracker.py stats
```

---

## Step 13：配置定时任务

```bash
crontab -e

# 添加以下任务：

# 每 4 小时心跳检查
0 */4 * * * cd /root/.openclaw/workspace && python3 skills/emotion-analyzer/src/scoreboard.py stats >> /var/log/openclaw-heartbeat.log 2>&1

# 每周能力深检（周日 UTC 20:00）
0 20 * * 0 cd /root/.openclaw/workspace && python3 skills/emotion-analyzer/src/tracker.py check >> /var/log/openclaw-weekly.log 2>&1
```

---

## 常见问题

### Q1: Gateway 无法启动

```bash
# 检查配置语法
jq . < /root/.openclaw/openclaw.json

# 检查端口占用
lsof -i :18789

# 查看日志
journalctl --user -u openclaw-gateway -n 50
```

### Q2: 模型 API 调用失败

```bash
# 测试 API 连通性
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.deepseek.com/v1/models

# 检查 API Key 配置是否正确
cat /root/.openclaw/models.json | jq '.providers.deepseek.apiKey'
```

### Q3: 心跳检查无响应

```bash
# 手动运行心跳检查
cd /root/.openclaw/workspace
python3 -c "
import sys
sys.path.insert(0, 'skills/emotion-analyzer/src')
from scoreboard import get_daily_stats, check_promotion
print(get_daily_stats())
print(check_promotion())
"

# 检查 cron 是否正常
systemctl --user status cron
```

---

## 升级指南

```bash
# 1. 备份当前配置
cp -r /root/.openclaw /root/.openclaw.bak.$(date +%Y%m%d)

# 2. 拉取更新
git -C /root/.openclaw/agent-evolution pull

# 3. 重启服务
systemctl --user restart openclaw-gateway.service
```

---

## 下一步

- 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 了解架构设计
- 阅读 [API.md](API.md) 了解各模块 API
- 基于 B=MAP 框架配置你的 Agent 自我进化系统

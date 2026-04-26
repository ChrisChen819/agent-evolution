# Ubuntu Hermes Agent + Clash 一键部署方案

## 架构图

```
用户 (Telegram/飞书)
       ↓
  Hermes Agent (Ubuntu)
       ↓
  Clash (本地代理)
       ↓
  GLaDOS Cloud (海外出口)
       ↓
  Telegram/ChatGPT API
```

## 前置要求

| 项目 | 要求 |
|------|------|
| Ubuntu 版本 | 22.04 LTS + |
| 网络 | 能访问 GLaDOS 订阅链接 |
| Tailscale | 用于远程控制（可选但推荐） |
| SSH | 需开启以便远程部署 |

## 部署方式一：全自动脚本（推荐）

### 下载并执行
```bash
# 在目标 Ubuntu 上以普通用户执行
curl -fsSL https://raw.githubusercontent.com/ChrisChen819/agent-evolution/main/scripts/deploy-hermes.sh | bash
```

### 脚本功能
1. 安装基础依赖（curl, wget, git, python3, pip）
2. 安装 Tailscale
3. 加入 Tailscale 网络
4. 下载并配置 Clash
5. 配置 Clash 开机自启（systemd）
6. 安装 Hermes Agent
7. 配置 Hermes 基本设置

---

## 部署方式二：手动分步部署

### Step 1: 开启 SSH（纯服务器版必须）
```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
sudo ufw allow 22/tcp
```

### Step 2: 安装 Tailscale
```bash
curl -fsSL https://tailscale.com/install.sh | bash
tailscale up
# 会显示登录链接，浏览器打开完成认证
```

### Step 3: 安装 Clash
```bash
# 创建目录
mkdir -p ~/clash && cd ~/clash

# 下载 Clash
wget https://github.com/Dreamacro/clash/releases/download/v1.10.0/clash-linux-amd64-v1.10.0.gz
gzip -d clash-linux-amd64-v1.10.0.gz
chmod +x clash-linux-amd64-v1.10.0

# 下载 GLaDOS 配置
wget -O ~/glados.yaml 你的GLaDOS_Clash订阅链接
```

### Step 4: 配置 Clash 开机自启
```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/clash.service << 'EOF'
[Unit]
Description=Clash Proxy
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/user/clash
ExecStart=/home/user/clash/clash-linux-amd64-v1.10.0 -f /home/user/glados.yaml -d .
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target

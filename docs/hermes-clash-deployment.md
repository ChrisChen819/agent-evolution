# Ubuntu Hermes Agent + Clash 一键部署方案

> 适用：Ubuntu 22.04+ Desktop / Server
> 架构：Clash 本地代理 + GLaDOS 出国隧道 + Hermes Agent

---

## 架构图

```
用户 (Telegram/飞书)
       ↓
  Hermes Agent (Ubuntu)
       ↓
  系统代理 (ALL_PROXY)
       ↓
  Clash (本地 HTTP:7890 / SOCKS:7891)
       ↓
  GLaDOS Cloud (规则模式)
       ↓
  Telegram / ChatGPT / GLM API
```

---

## 前置要求

| 项目 | 要求 |
|------|------|
| Ubuntu | 22.04 LTS + |
| 网络 | 能访问 GLaDOS 订阅链接 |
| Tailscale | 远程控制（可选但推荐） |
| SSH | 开启（纯服务器版必须） |

---

## Step 1：开启 SSH（纯服务器版必须）

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo ufw allow 22/tcp
```

---

## Step 2：安装 Tailscale（用于远程控制）

```bash
curl -fsSL https://tailscale.com/install.sh | bash
sudo tailscale up
# 浏览器打开显示的链接完成认证
```

**无公网 IP 时用 Tailscale SSH 登录：**

```bash
sudo tailscale set --ssh
# 之后从其他机器: tailscale ssh user@100.x.x.x
```

---

## Step 3：安装 Clash

### 3.1 创建目录

```bash
mkdir -p ~/clash && cd ~/clash
```

### 3.2 下载 Clash 二进制

> Dreamacro/clash 仓库已删除，推荐从镜像获取：

```bash
# 方式A：从 GitHub 代理镜像
wget -O clash.gz https://github.moeyy.xyz/Dreamacro/clash/releases/download/v1.10.0/clash-linux-amd64-v1.10.0.gz

# 方式B：从其他镜像站
wget -O clash.gz https://mirror.gd/sing-box/clash.gz

gzip -d clash.gz
chmod +x clash-linux-amd64-v1.10.0
```

### 3.3 下载 GLaDOS 配置

```bash
# 将下面的链接替换成你自己的 GLaDOS Clash 订阅地址
wget -O ~/glados.yaml 你的_GLaDOS_Clash订阅链接
```

---

## Step 4：配置 Clash 开机自启

### 4.1 创建 systemd 服务

```bash
mkdir -p ~/.config/systemd/user
nano ~/.config/systemd/user/clash.service
```

内容：

```ini
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
```

### 4.2 开启 linger（SSH 退出后服务不停止）

```bash
loginctl enable-linger
```

### 4.3 启用并启动

```bash
systemctl --user daemon-reload
systemctl --user enable clash
systemctl --user start clash
```

### 4.4 验证

```bash
systemctl --user status clash
# 应显示: active (running)
```

---

## Step 5：配置系统代理环境变量

> 让所有应用（包括 Hermes）走 Clash 代理

```bash
# 写入 .bashrc（永久生效）
echo 'export ALL_PROXY="socks5://127.0.0.1:7891"' >> ~/.bashrc
source ~/.bashrc

# 验证代理（应显示 Taichung 或其他海外 IP）
curl -s https://ipinfo.io/json
```

### 桌面版额外配置（如使用 GNOME）

```bash
gsettings set org.gnome.system.proxy.http host '127.0.0.1'
gsettings set org.gnome.system.proxy.http-port 7890
gsettings set org.gnome.system.proxy.https host '127.0.0.1'
gsettings set org.gnome.system.proxy.https-port 7890
gsettings set org.gnome.system.proxy.socks host '127.0.0.1'
gsettings set org.gnome.system.proxy.socks-port 7891
gsettings set org.gnome.system.proxy mode 'manual'
```

重启桌面会话让桌面代理生效，或使用新的终端窗口。

---

## Step 6：安装 Hermes Agent

### 6.1 安装 uv（Python 包管理器）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 6.2 克隆 Hermes Agent

```bash
git clone https://github.com/NousResearch/hermes-agent.git ~/hermes-agent
cd ~/hermes-agent
```

### 6.3 创建虚拟环境并安装

```bash
uv venv .venv --python 3.11 --clear
uv pip install --python .venv/bin/python -e .
```

### 6.4 配置 API Key

```bash
mkdir -p ~/.hermes
nano ~/.hermes/.env
```

内容：

```
ZAI_API_KEY=你的_ZAI_API_KEY
```

### 6.5 配置 Hermes（使用 GLM-5-Turbo）

```bash
cat > ~/.hermes/config.yaml << 'EOF'
model: glm-5-turbo
providers:
  zai: {}
EOF
```

---

## Step 7：启动并验证 Hermes

### 7.1 重启 hermes（让代理生效）

```bash
pkill hermes
cd ~/hermes-agent
source .venv/bin/activate
hermes
```

### 7.2 配置 Telegram Bot（如需要）

```bash
hermes configure telegram
# 按提示填入 Bot Token
```

### 7.3 验证 Telegram 连通性

```bash
curl -s https://api.telegram.org | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else 'FAIL')"
# 应返回: OK
```

---

## 快速命令汇总

| 功能 | 命令 |
|------|------|
| 启动 Clash | `systemctl --user start clash` |
| 查看 Clash 状态 | `systemctl --user status clash` |
| Clash 日志 | `journalctl --user -u clash -f` |
| 重启 hermes | `pkill hermes && cd ~/hermes-agent && source .venv/bin/activate && hermes` |
| 测试代理 | `curl -s https://ipinfo.io/json` |
| Tailscale 状态 | `tailscale status` |
| Tailscale SSH | `tailscale ssh user@100.x.x.x` |

---

## 故障排查

### Clash 启动失败

```bash
# 查看详细日志
journalctl --user -u clash -n 50

# 验证配置文件 YAML 格式
python3 -c "import yaml; yaml.safe_load(open('~/glados.yaml'))"
```

### Hermes 401 错误

```bash
# 检查 API Key 是否正确
cat ~/.hermes/.env

# 重启 hermes
pkill hermes && cd ~/hermes-agent && source .venv/bin/activate && hermes
```

### 代理不生效

```bash
# 确认环境变量
echo $ALL_PROXY
# 应显示: socks5://127.0.0.1:7891

# 手动设置
export ALL_PROXY="socks5://127.0.0.1:7891"
```

### Telegram 无法连接

```bash
# 测试 Telegram API
curl -s --max-time 10 https://api.telegram.org
# 应返回 JSON（而非超时）
```

---

## 卸载方法

```bash
# 停止服务
systemctl --user stop clash
systemctl --user disable clash

# 删除文件
rm -rf ~/clash ~/glados.yaml ~/.config/systemd/user/clash.service
rm -rf ~/hermes-agent

# 清理环境变量（编辑 ~/.bashrc 删除 ALL_PROXY 那行）
```

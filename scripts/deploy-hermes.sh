#!/bin/bash
#=======================================
# Hermes Agent + Clash 一键部署脚本
# 适用于：Ubuntu Desktop / Server 22.04+
# 作者：Neo (老陈的数字分身)
# 日期：2026-04-26
#=======================================

set -e

#====== 配置区 ======
GLADOS_SUBSCRIBE_URL="你的GLaDOS_Clash订阅链接"
TAILSCALE_AUTH_KEY=""  # 如需自动加入，填入 Tailscale auth key
SSH_USER="chris"
SSH_PORT="22"

#====== 颜色 ======
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err() { echo -e "${RED}[ERR]${NC} $1"; }

#====== 1. 安装基础依赖 ======
log_info "1/7: 安装基础依赖..."
apt-get update -qq
apt-get install -y -qq curl wget git python3 python3-venv python3-pip > /dev/null 2>&1

#====== 2. 安装 Tailscale ======
log_info "2/7: 安装 Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | bash
fi

#====== 3. 加入 Tailscale 网络 ======
log_info "3/7: 加入 Tailscale 网络..."
if [ -n "$TAILSCALE_AUTH_KEY" ]; then
    tailscale up --authkey="$TAILSCALE_AUTH_KEY" --accept-routes
else
    log_warn "请手动执行: tailscale up (会生成登录链接)"
fi

#====== 4. 安装 Clash ======
log_info "4/7: 安装 Clash..."
mkdir -p ~/clash
cd ~/clash

# 下载 Clash (从本地或其他可用源)
CLASH_URL="https://github.com/Dreamacro/clash/releases/download/v1.10.0/clash-linux-amd64-v1.10.0.gz"
wget -q --timeout=60 "$CLASH_URL" -O clash.gz || {
    log_warn "GitHub 下载失败，尝试其他镜像..."
    wget -q --timeout=60 "https://mirror.gd/sing-box/clash.gz" -O clash.gz
}
gzip -d clash.gz
chmod +x clash-linux-amd64-v1.10.0

# 下载 GLaDOS 配置
log_info "下载 GLaDOS 配置..."
wget -q --timeout=30 "$GLADOS_SUBSCRIBE_URL" -O ~/glados.yaml

#====== 5. 配置 Clash systemd 服务 ======
log_info "5/7: 配置 Clash 开机自启..."
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/clash.service << 'EOF'
[Unit]
Description=Clash Proxy
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/clash
ExecStart=%h/clash/clash-linux-amd64-v1.10.0 -f %h/glados.yaml -d .
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable clash
systemctl --user start clash
systemctl --user status clash

#====== 6. 安装 Hermes Agent ======
log_info "6/7: 安装 Hermes Agent..."
if [ ! -d ~/hermes-agent ]; then
    git clone https://github.com/NousResearch/hermes-agent.git ~/hermes-agent
fi

cd ~/hermes-agent
python3 -m venv .venv --clear
source .venv/bin/activate
pip install -q -e .

#====== 7. 配置 Hermes ======
log_info "7/7: 配置 Hermes Agent..."
mkdir -p ~/.hermes

# API Key 配置 (需要手动填入)
if [ ! -f ~/.hermes/.env ]; then
    cat > ~/.hermes/.env << 'EOF'
ZAI_API_KEY=your_api_key_here
EOF
    log_warn "请编辑 ~/.hermes/.env 填入你的 ZAI API Key"
fi

# Hermes 配置
cat > ~/.hermes/config.yaml << 'EOF'
model: glm-5-turbo
providers:
  zai: {}
EOF

#====== 完成 ======
log_info "======================================"
log_info "部署完成!"
log_info "======================================"
echo ""
log_info "下一步操作:"
echo "  1. 编辑 ~/.hermes/.env 填入 API Key"
echo "  2. 重启 hermes: pkill hermes && cd ~/hermes-agent && source .venv/bin/activate && hermes"
echo "  3. 配置 Telegram bot: hermes configure telegram"
echo ""
log_info "常用命令:"
echo "  查看 Clash 状态: systemctl --user status clash"
echo "  重启 Clash: systemctl --user restart clash"
echo "  启动 Hermes: cd ~/hermes-agent && source .venv/bin/activate && hermes"
echo "  Tailscale 状态: tailscale status"

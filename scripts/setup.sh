#!/bin/bash
#===============================================================================
# Agent Evolution System v3 — 安装脚本
# 目标用户：已安装 OpenClaw 的用户
# 功能：把进化模块复制到已有 workspace，不覆盖任何现有文件
#===============================================================================

set -e
set +o pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
bold()  { echo -e "${BOLD}$1${NC}"; }

WORKSPACE_DIR="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ------------------------------------------------------------------------------
# 核心：复制进化模块（不覆盖）
# ------------------------------------------------------------------------------
install_modules() {
    bold "═ 安装进化模块 ═"
    mkdir -p "$WORKSPACE_DIR/skills/emotion-analyzer/src"
    mkdir -p "$WORKSPACE_DIR/.learnings/experiences"
    mkdir -p "$WORKSPACE_DIR/memory/daily"

    # 复制进化模块
    for f in scoreboard.py emotion_analyzer.py; do
        SRC="$PROJECT_DIR/src/$f"
        DST="$WORKSPACE_DIR/skills/emotion-analyzer/src/$f"
        if [ -f "$SRC" ]; then
            if [ -f "$DST" ]; then
                warn "$f 已存在，跳过"
            else
                cp "$SRC" "$DST"
                ok "$f 已安装"
            fi
        fi
    done

    # 复制 tracker
    SRC="$PROJECT_DIR/src/tracker.py"
    DST="$WORKSPACE_DIR/.learnings/tracker.py"
    if [ -f "$SRC" ]; then
        if [ ! -f "$DST" ]; then
            cp "$SRC" "$DST"
            ok "tracker.py 已安装"
        else
            warn "tracker.py 已存在，跳过"
        fi
    fi

    # 初始化追踪文件（不存在才创建）
    TRACKER="$WORKSPACE_DIR/.learnings/TRACKER.md"
    if [ ! -f "$TRACKER" ]; then
        cat > "$TRACKER" << 'EOF'
# 频繁模式追踪

> 由 Agent Evolution System v3 自动维护

## 当前活跃追踪

| 模式 | 次数 | 首次 | 最近 | 状态 |
|------|------|------|------|------|
| _(暂无活跃记录)_ | - | - | - | - |
EOF
        ok "TRACKER.md 已创建"
    else
        warn "TRACKER.md 已存在，跳过"
    fi
}

# ------------------------------------------------------------------------------
# 复制补充内容（不覆盖）
# ------------------------------------------------------------------------------
install_supplements() {
    bold "═ 安装补充内容 ═"
    info "补充内容只会追加到现有文件，不会覆盖任何内容"

    for f in SOUL_SUPPLEMENT.md HEARTBEAT_SUPPLEMENT.md AGENTS_SUPPLEMENT.md; do
        SRC="$PROJECT_DIR/templates/$f"
        if [ ! -f "$SRC" ]; then continue; fi

        # 目标文件名去掉 _SUPPLEMENT 后缀
        DST_NAME="${f%.SUPPLEMENT.md}"
        DST="$WORKSPACE_DIR/$DST_NAME"

        if [ -f "$DST" ]; then
            # 追加到现有文件
            echo "" >> "$DST"
            echo "---" >> "$DST"
            echo "EOF" >> "$DST"
            echo "" >> "$DST"
            echo "> 来源：agent-evolution $f" >> "$DST"
            cat "$SRC" >> "$DST"
            ok "$DST 已追加"
        else
            # 不存在时复制为新文件
            cp "$SRC" "$DST"
            ok "$DST 已创建"
        fi
    done
}

# ------------------------------------------------------------------------------
# MemOS 检测（可选）
# ------------------------------------------------------------------------------
check_memos() {
    bold "═ 检测 MemOS ═"
    if curl -s --connect-timeout 3 http://127.0.0.1:18799/api/status &>/dev/null; then
        ok "MemOS 已运行于 http://127.0.0.1:18799"
    else
        info "MemOS 未检测到（可选，不影响进化模块运行）"
        info "如需安装: docs/DEPLOY.md Step 8"
    fi
}

# ------------------------------------------------------------------------------
# 环境检查
# ------------------------------------------------------------------------------
check_env() {
    bold "═ 检查环境 ═"
    if [ -d "$WORKSPACE_DIR" ]; then
        ok "Workspace: $WORKSPACE_DIR"
    else
        warn "Workspace 目录不存在: $WORKSPACE_DIR"
        info "请确认 OpenClaw 已正确安装"
    fi

    if command -v python3 &>/dev/null; then
        ok "Python: $(python3 --version | awk '{print $2}')"
    else
        warn "Python3 未安装"
    fi

    if [ -f "$WORKSPACE_DIR/skills/emotion-analyzer/src/scoreboard.py" ]; then
        INSTALLED_VERSION=$(python3 "$WORKSPACE_DIR/skills/emotion-analyzer/src/scoreboard.py" --version 2>&1 || echo "unknown")
        ok "进化模块已安装 (v$INSTALLED_VERSION)"
    fi
}

# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
main() {
    echo ""
    bold "╔══════════════════════════════════════════╗"
    bold "║   Agent Evolution System v3 — 安装向导   ║"
    bold "╚══════════════════════════════════════════╝"
    echo ""
    info "目标：把进化模块安装到已有的 OpenClaw workspace"
    info "原则：不覆盖任何现有文件"
    echo ""

    check_env
    echo ""
    install_modules
    echo ""
    install_supplements
    echo ""
    check_memos
    echo ""

    bold "══════════════════════════════════════════"
    bold "  安装完成！"
    bold "══════════════════════════════════════════"
    echo ""
    info "已安装："
    info "  - skills/emotion-analyzer/src/ (评分+情绪分析)"
    info "  - .learnings/tracker.py (频繁模式追踪)"
    info "  - .learnings/TRACKER.md (追踪表)"
    echo ""
    info "补充内容（已追加到现有文件）："
    info "  - SOUL.md, HEARTBEAT.md, AGENTS.md"
    info "  - 请查看文件末尾的补充章节"
    echo ""
    info "查看详情: docs/DEPLOY.md"
    echo ""
}

main "$@"

#!/bin/bash
# Agent Reach 一键完整测试
# 用法: bash test.sh
# 在任何有 Python 3.10+ 的机器上跑就行

set -euo pipefail

echo "╔════════════════════════════════════════════╗"
echo "║    👁️  Agent Reach 完整测试                ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# ── 1. 准备干净环境 ──
echo "📦 创建测试环境..."
TEST_DIR=$(mktemp -d)
python3 -m venv "$TEST_DIR/venv"
source "$TEST_DIR/venv/bin/activate"

# ── 2. 安装 ──
echo "📥 从 GitHub 安装..."
pip install -q https://github.com/Panniantong/agent-reach/archive/main.zip 2>&1 | tail -1
echo ""

# ── 3. CLI smoke tests ──
PASS=0
FAIL=0

test_ok() {
    local name="$1"
    local expect="$2"
    shift
    shift
    echo -n "  $name ... "
    output=$(eval "$@" 2>&1 || true)
    if echo "$output" | grep -Eq "$expect"; then
        echo "✅"
        PASS=$((PASS+1))
    else
        echo "❌"
        echo "    $(echo "$output" | head -3)"
        FAIL=$((FAIL+1))
    fi
}

echo "🧪 CLI 冒烟测试"
test_ok "版本输出" "Agent Reach v" "agent-reach version"
test_ok "安装预演" "DRY RUN|Dry run complete" "agent-reach install --env=auto --dry-run"
test_ok "健康检查" "Agent Reach 状态|渠道可用|状态：" "agent-reach doctor"
test_ok "更新检查" "当前版本|已是最新版本|最新版本|无法检查更新|最新提交" "agent-reach check-update"

echo ""
echo "════════════════════════════════════════════"
echo "  ✅ 通过: $PASS   ❌ 失败: $FAIL"
echo "════════════════════════════════════════════"

# ── 4. 清理 ──
deactivate 2>/dev/null || true
rm -rf "$TEST_DIR"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 全部通过！"
else
    echo ""
    echo "⚠️  有 $FAIL 个测试失败，请检查上面的输出"
    exit 1
fi

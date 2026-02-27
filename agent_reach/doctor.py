# -*- coding: utf-8 -*-
"""Environment health checker — powered by channels.

Each channel knows how to check itself. Doctor just collects the results.
"""

from typing import Dict

from agent_reach.channels import get_all_channels
from agent_reach.config import Config

_SIGNAL_VALUES = {"yes", "no", "unknown", "n/a"}
_AUTH_CHANNELS = {"github", "twitter", "xiaohongshu", "linkedin", "bosszhipin"}


def _normalize_signal(value: str) -> str:
    if value in _SIGNAL_VALUES:
        return value
    return "unknown"


def _infer_signals(channel_name: str, status: str, message: str) -> Dict[str, str]:
    """Infer four-level health signals from existing status + message."""
    msg = (message or "").lower()

    installed = "yes"
    if "未安装" in message or "not installed" in msg or "not found" in msg:
        installed = "no"
    if status == "off" and ("安装" in message or "install" in msg):
        installed = "no"

    configured = "unknown"
    if installed == "no":
        configured = "no"
    elif any(k in message for k in ["未配置", "无代理", "需扫码登录", "未认证", "未登录"]):
        configured = "no"
    elif any(k in message for k in ["已配置", "完整可用", "可提取", "可读取", "可用"]):
        configured = "yes"

    reachable = "unknown"
    if status == "ok":
        reachable = "yes"
    elif status == "warn":
        reachable = "yes"
        if any(k in message for k in ["连接异常", "调用异常", "失败"]):
            reachable = "no"
    elif status in ("off", "error"):
        reachable = "no"

    if channel_name not in _AUTH_CHANNELS:
        authenticated = "n/a"
    elif any(k in message for k in ["未登录", "未认证", "需扫码登录", "cookie"]):
        authenticated = "no"
    elif any(k in message for k in ["已登录", "完整可用"]):
        authenticated = "yes"
    else:
        authenticated = "unknown"

    return {
        "installed": _normalize_signal(installed),
        "configured": _normalize_signal(configured),
        "reachable": _normalize_signal(reachable),
        "authenticated": _normalize_signal(authenticated),
    }


def _signal_badge(signals: Dict[str, str]) -> str:
    icon = {"yes": "✅", "no": "❌", "unknown": "❓", "n/a": "➖"}
    return (
        f"[I:{icon[signals['installed']]} "
        f"C:{icon[signals['configured']]} "
        f"R:{icon[signals['reachable']]} "
        f"A:{icon[signals['authenticated']]}]"
    )


def check_all(config: Config) -> Dict[str, dict]:
    """Check all channels and return status dict."""
    results = {}
    for ch in get_all_channels():
        status, message = ch.check(config)
        signals = _infer_signals(ch.name, status, message)
        results[ch.name] = {
            "status": status,
            "name": ch.description,
            "message": message,
            "tier": ch.tier,
            "backends": ch.backends,
            "signals": signals,
        }
    return results


def format_report(results: Dict[str, dict]) -> str:
    """Format results as a readable text report."""
    lines = []
    lines.append("👁️  Agent Reach 状态")
    lines.append("=" * 40)
    lines.append("信号图例: I=installed C=configured R=reachable A=authenticated")

    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)

    # Tier 0 — zero config
    lines.append("")
    lines.append("✅ 装好即用：")
    for key, r in results.items():
        if r["tier"] == 0:
            badge = _signal_badge(r["signals"])
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} {badge} — {r['message']}")
            elif r["status"] == "warn":
                lines.append(f"  ⚠️  {r['name']} {badge} — {r['message']}")
            elif r["status"] in ("off", "error"):
                lines.append(f"  ❌ {r['name']} {badge} — {r['message']}")

    # Tier 1 — needs free key
    tier1 = {k: r for k, r in results.items() if r["tier"] == 1}
    if tier1:
        lines.append("")
        lines.append("🔍 搜索（mcporter 即可解锁）：")
        for key, r in tier1.items():
            badge = _signal_badge(r["signals"])
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} {badge} — {r['message']}")
            else:
                lines.append(f"  ⬜ {r['name']} {badge} — {r['message']}")

    # Tier 2 — optional setup
    tier2 = {k: r for k, r in results.items() if r["tier"] == 2}
    if tier2:
        lines.append("")
        lines.append("🔧 配置后可用：")
        for key, r in tier2.items():
            badge = _signal_badge(r["signals"])
            if r["status"] == "ok":
                lines.append(f"  ✅ {r['name']} {badge} — {r['message']}")
            elif r["status"] == "warn":
                lines.append(f"  ⚠️  {r['name']} {badge} — {r['message']}")
            else:
                lines.append(f"  ⬜ {r['name']} {badge} — {r['message']}")

    lines.append("")
    lines.append(f"状态：{ok_count}/{total} 个渠道可用")
    if ok_count < total:
        lines.append("运行 `agent-reach setup` 解锁更多渠道")

    # Security check: config file permissions
    import stat
    config_path = Config.CONFIG_DIR / "config.yaml"
    if config_path.exists():
        try:
            mode = config_path.stat().st_mode
            if mode & (stat.S_IRGRP | stat.S_IROTH):
                lines.append("")
                lines.append("⚠️  安全提示：config.yaml 权限过宽（其他用户可读）")
                lines.append("   修复：chmod 600 ~/.agent-reach/config.yaml")
        except OSError:
            pass

    return "\n".join(lines)

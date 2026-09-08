#!/bin/bash
# Q100-E BIOS 一键完整分析
# 用法: bash full_analyze.sh <32MB.bin>
# 输出: 综合报告到 stdout + analysis_report.md

set -e
BIN_FILE="$1"
if [ -z "$BIN_FILE" ] || [ ! -f "$BIN_FILE" ]; then
    echo "用法: $0 <32MB.bin>"
    echo ""
    echo "例: $0 backups/original/Q100E_original_2026xxxx.bin"
    exit 1
fi

WORKSPACE="/d/OneDrive/User/硬件Fix/噢易乾Q100-E准系统"
TOOLS_DIR="$WORKSPACE/tools"

echo "=========================================="
echo "  Q100-E BIOS 完整分析"
echo "  文件: $BIN_FILE"
echo "  大小: $(stat -c%s "$BIN_FILE" 2>/dev/null || wc -c < "$BIN_FILE") bytes"
echo "=========================================="
echo ""

# 1. SHA256 + MD5
echo "=== 1. 哈希 ==="
sha256sum "$BIN_FILE"
md5sum "$BIN_FILE"
echo ""

# 2. 综合分析
echo "=== 2. 整体分析 (tools/analyze.py) ==="
python "$TOOLS_DIR/analyze.py" "$BIN_FILE" 2>&1 | head -50
echo ""

# 3. MCExtractor 解析 microcode
echo "=== 3. MCExtractor 解析 microcode ==="
MCE_SCRIPT="$TOOLS_DIR/MCExtractor/MCExtractor-r352/MCE.py"
if [ -f "$MCE_SCRIPT" ]; then
    python "$MCE_SCRIPT" -skip -exit "$BIN_FILE" 2>&1 | head -40 || echo "  (MCExtractor 失败，可能需要 GUI 模式)"
else
    echo "  MCExtractor 未安装, 跳过"
fi
echo ""

# 4. binwalk 扫描 microcode
echo "=== 4. binwalk 扫 microcode ==="
which binwalk > /dev/null 2>&1 && {
    binwalk -y 'microcode\|UEFI PI Firmware' "$BIN_FILE" 2>&1 | head -20
} || echo "  binwalk 未安装, 跳过"
echo ""

# 5. iucode_tool 解析 microcode
echo "=== 5. iucode_tool 解析 ==="
which iucode_tool > /dev/null 2>&1 && {
    iucode_tool -l "$BIN_FILE" 2>&1 | head -20
} || echo "  iucode_tool 未安装, 跳过"
echo ""

# 6. 找关键字符串
echo "=== 6. 关键字符串扫描 ==="
echo "  找 'Microcode' 字符串位置:"
grep -boa 'Microcode' "$BIN_FILE" 2>&1 | head -5
echo ""
echo "  找 'Raptor Lake' 字符串:"
grep -boa 'Raptor Lake' "$BIN_FILE" 2>&1 | head -5
echo ""
echo "  找 '0x000B067' 字符串 (14 代 RPL-R):"
grep -boa '0x000B067' "$BIN_FILE" 2>&1 | head -5
echo ""

# 7. 14 代 microcode 检测总结
echo "=== 7. 14 代 microcode 检测总结 ==="
if grep -q '000B067' "$BIN_FILE" 2>/dev/null; then
    echo "  ✅ 找到 0x000B067 (RPL-R, 14 代) 字符串"
    echo "  → 14 代 CPU 理论上可点亮"
else
    echo "  ❌ 未找到 0x000B067 (RPL-R) 字符串"
    echo "  → 14 代 CPU 装上可能无法点亮"
    echo "  → i3-12100 跑得起来可能靠 CPU 内置 microcode fallback"
fi
echo ""

# 8. 12 代 microcode 检测
if grep -q '0009067A' "$BIN_FILE" 2>/dev/null; then
    echo "  ✅ 找到 0x0009067A (ADL-S, 12 代) 字符串"
else
    echo "  ⚠️ 未找到 0x0009067A (ADL-S) 字符串"
fi
echo ""

# 9. 9/10 代 microcode 检测
if grep -q '00090671' "$BIN_FILE" 2>/dev/null; then
    echo "  9 代 Coffee Lake microcode: ✅ 存在"
fi
if grep -q '000906A0' "$BIN_FILE" 2>/dev/null; then
    echo "  10 代 Comet Lake microcode: ✅ 存在"
fi
echo ""

# 10. PMCC000 容器位置
echo "=== 10. PMCC000 容器位置 (ME 区域 microcode) ==="
if grep -q 'PMCC000' "$BIN_FILE" 2>/dev/null; then
    grep -bao 'PMCC000' "$BIN_FILE" 2>&1 | head -5
else
    echo "  未找到 PMCC000 字符串"
fi
echo ""

# 11. 总结
echo "=========================================="
echo "  总结"
echo "=========================================="
echo ""
echo "  1. 如果 14 代 microcode (0x000B067) 存在 → BIOS 已含 14 代支持"
echo "  2. 如果只有 12 代或 9/10 代 → 需升级 ME 或找支持 14 代的新 BIOS"
echo "  3. 如果只有 9/10 代 + 12 代 missing → i3-12100 靠 CPU 内置 fallback"
echo ""
echo "  下一步建议:"
echo "  - 有 14 代 microcode: 装 i5-14400 测试"
echo "  - 缺 14 代 microcode:"
echo "    1. 打电话 4001-027-580 (5 分钟最稳)"
echo "    2. 找 Shuttle XH610 公开 BIOS 移植 microcode"
echo "    3. 升级 ME 16.x (高级, 高风险)"
echo ""

"""用 Python 调 MEInfoWin64 提取 ME 版本信息"""
import subprocess
from pathlib import Path

bin_file = Path("D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/backups/H610_full_32mb_V1.bin").absolute()
tool = Path("D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/backups/CSME System Tools v16.0 r8/MEInfo/WIN64/MEInfoWin64.exe").absolute()

# 试 -desc (descriptor) 模式
print("=== MEInfo -desc (descriptor) ===")
r = subprocess.run([str(tool), "-desc", str(bin_file)], capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])

# 试默认（也是 desc）
print("\n=== MEInfo 默认 ===")
r = subprocess.run([str(tool), str(bin_file)], capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])

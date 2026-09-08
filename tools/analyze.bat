@echo off
REM Q100-E BIOS 一键完整分析 (Windows 版)
REM 用法: analyze.bat <32MB.bin>

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo 用法: %~nx0 ^<32MB.bin^>
    echo.
    echo 例: %~nx0 backups\original\Q100E_original_2026xxxx.bin
    exit /b 1
)

set "BIN_FILE=%~1"
if not exist "%BIN_FILE%" (
    echo 文件不存在: %BIN_FILE%
    exit /b 1
)

set "WORKSPACE=D:\OneDrive\User\硬件Fix\噢易乾Q100-E准系统"
set "TOOLS=%WORKSPACE%\tools"

echo ==========================================
echo   Q100-E BIOS 完整分析
echo   文件: %BIN_FILE%
for %%I in ("%BIN_FILE%") do echo   大小: %%~zI bytes
echo ==========================================
echo.

echo === 1. 哈希 ===
certutil -hashfile "%BIN_FILE%" SHA256
certutil -hashfile "%BIN_FILE%" MD5
echo.

echo === 2. 整体分析 (tools\analyze.py) ===
python "%TOOLS%\analyze.py" "%BIN_FILE%" 2>nul
echo.

echo === 3. MCExtractor 解析 microcode ===
if exist "%TOOLS%\MCExtractor\MCExtractor-r352\MCE.py" (
    echo 跑 MCExtractor (输入文件后回车)...
    echo %BIN_FILE% | python "%TOOLS%\MCExtractor\MCExtractor-r352\MCE.py" -skip -exit 2>nul
) else (
    echo MCExtractor 未安装, 跳过
)
echo.

echo === 4. binwalk 扫 microcode (需要 WSL) ===
echo 在 WSL Ubuntu 22.04 跑:
echo   wsl -d Ubuntu-22.04 -- binwalk -y 'microcode' "%BIN_FILE%"
echo.

echo === 5. 关键字符串扫描 ===
echo.
echo Microcode 字符串位置:
powershell -Command "$content = [System.IO.File]::ReadAllBytes('%BIN_FILE%'); $ascii = [System.Text.Encoding]::ASCII.GetString($content); $matches = Select-String -InputObject $ascii -Pattern 'Microcode' -AllMatches; $matches | Select-Object -First 5 | ForEach-Object { '  偏移 0x{0:X}: {1}' -f $_.Index, $_.Matches[0].Value }"
echo.

echo RPL-R microcode (0x000B067) 检测:
findstr /a /c:"000B067" "%BIN_FILE%" 2>nul >nul && (
    echo   ! 找到 0x000B067 (RPL-R, 14 代) 字符串
    echo   → 14 代 CPU 理论上可点亮
) || (
    echo   X 未找到 0x000B067 (RPL-R) 字符串
    echo   → 14 代 CPU 装上可能无法点亮
    echo   → i3-12100 跑得起来可能靠 CPU 内置 microcode fallback
)
echo.

echo ADL-S microcode (0x0009067A) 检测:
findstr /a /c:"0009067A" "%BIN_FILE%" 2>nul >nul && (
    echo   ! 找到 0x0009067A (ADL-S, 12 代) 字符串
) || (
    echo   ! 未找到 0x0009067A (ADL-S) 字符串
)
echo.

echo Coffee Lake (0x00090671) 检测:
findstr /a /c:"00090671" "%BIN_FILE%" 2>nul >nul && echo   ! 9 代 Coffee Lake microcode: 存在
echo Comet Lake (0x000906A0) 检测:
findstr /a /c:"000906A0" "%BIN_FILE%" 2>nul >nul && echo   ! 10 代 Comet Lake microcode: 存在
echo.

echo PMCC000 容器位置:
powershell -Command "$content = [System.IO.File]::ReadAllBytes('%BIN_FILE%'); $ascii = [System.Text.Encoding]::ASCII.GetString($content); $matches = Select-String -InputObject $ascii -Pattern 'PMCC000' -AllMatches; $matches | Select-Object -First 5 | ForEach-Object { '  偏移 0x{0:X}: {1}' -f $_.Index, $_.Matches[0].Value }"
echo.

echo ==========================================
echo   下一步建议
echo ==========================================
echo.
echo   1. 有 14 代 microcode - 装 i5-14400 测试
echo   2. 缺 14 代 microcode:
echo      a. 打电话 4001-027-580 (5 分钟最稳)
echo      b. 找 Shuttle XH610 公开 BIOS 移植 microcode
echo      c. 升级 ME 16.x (高级, 高风险)
echo.
echo   详细文档: docs\14th-gen-adaptation.md
echo            docs\me-upgrade-feasibility-2026-09-08.md
echo            docs\cross-vendor-bios-ports-2026-09-08.md
echo            docs\official-support-contacts.md
echo.

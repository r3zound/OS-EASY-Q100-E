"""提取 docx 文档内容（docx 是 zip 格式）"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

docx = Path(r"C:\Users\holike\.minimax\v2\assets\2026\09\09\14-20-30-168-asset_20260909-142030-168_c57c5d5b809f_de3d84fd-H610_SPI备份指导书.docx")
print(f"文件: {docx}")
print(f"大小: {docx.stat().st_size} bytes")

# 读 document.xml
with zipfile.ZipFile(docx) as z:
    print(f"\nZIP 内容 ({len(z.namelist())} 个文件):")
    for name in z.namelist():
        print(f"  {name}")

    print("\n=== document.xml 内容 (去 XML 标签) ===\n")
    with z.open("word/document.xml") as f:
        content = f.read().decode("utf-8")

# 用 ElementTree 解析
ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
root = ET.fromstring(content)

paragraphs = []
for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
    text = "".join(t.text or "" for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
    if text.strip():
        paragraphs.append(text)

print(f"=== 共 {len(paragraphs)} 段文字 ===\n")
for i, p in enumerate(paragraphs):
    print(f"[{i+1:3d}] {p}")

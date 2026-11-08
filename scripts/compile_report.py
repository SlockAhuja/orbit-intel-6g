"""
ORBIT-INTEL 6G — Technical Report Compilation & Verification Script
Compiles reports/technical_report/main.tex using XeLaTeX and verifies exact 2-page constraint.
"""

import os
import subprocess
import sys
import fitz

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_dir = os.path.join(root, "reports", "technical_report")
    tex_file = os.path.join(report_dir, "main.tex")
    pdf_file = os.path.join(report_dir, "main.pdf")

    xelatex = r"C:\Users\OM\AppData\Local\Programs\MiKTeX\miktex\bin\x64\xelatex.EXE"
    if not os.path.exists(xelatex):
        xelatex = "xelatex"

    cmd = [
        xelatex,
        "-interaction=nonstopmode",
        f"-output-directory={report_dir}",
        tex_file
    ]

    print("[1/2] Compiling LaTeX source with XeLaTeX...")
    res1 = subprocess.run(cmd, capture_output=True, text=True)
    res2 = subprocess.run(cmd, capture_output=True, text=True)

    if res2.returncode != 0:
        print("Compilation failed with returncode", res2.returncode)
        print(res2.stdout[-500:])
        sys.exit(1)

    print("[2/2] Verifying generated PDF...")
    if not os.path.exists(pdf_file):
        print("Error: PDF output does not exist:", pdf_file)
        sys.exit(1)

    doc = fitz.open(pdf_file)
    page_count = len(doc)
    print(f"Total Page Count: {page_count}")
    if page_count != 2:
        print(f"FAILED: Expected exactly 2 pages, got {page_count} pages.")
        sys.exit(1)

    for i, p in enumerate(doc):
        lines = [line.strip() for line in p.get_text().splitlines() if line.strip()]
        print(f"  Page {i+1} ({len(lines)} text lines): '{lines[0][:60]}' -> '{lines[-1][:60]}'")

    doc.close()
    print("SUCCESS: Technical report compiled and verified as strictly 2 pages.")

if __name__ == "__main__":
    main()

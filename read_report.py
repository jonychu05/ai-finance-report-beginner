import pdfplumber

pdf_path = "贵州茅台2025年报.PDF"  # 改成你下载的文件名

with pdfplumber.open(pdf_path) as pdf:
    print("总页数:", len(pdf.pages))
    first_text = pdf.pages[0].extract_text()
    print(first_text[:800])
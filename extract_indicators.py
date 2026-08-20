import pdfplumber

with pdfplumber.open("贵州茅台2025年报.PDF") as pdf:
    pages_text = [page.extract_text() or "" for page in pdf.pages]
    text = "\n".join(pages_text)

print("全本总字数:", len(text))

import re
targets = ["营业收入", "归属于上市公司股东的净利润", "总资产","负债合计"]

for key in targets:
    pos = text.find(key)                      # ① 找关键词第一次出现的位置
    if pos != -1:                             # ② 找到了
        snippet = text[pos:pos+100].replace("\n", " ")   # ③ 截取后面100个字
        print(key, "→", snippet)
def extract_number(text, keyword):
    pattern = keyword + r"[^0-9]{0,30}([0-9,\.]+)"   # ①
    m = re.search(pattern, text)                       # ②
    if m:
        return float(m.group(1).replace(",", ""))      # ③
    return None

revenue = extract_number(text, "营业收入")
cost = extract_number(text, "营业成本")
profit = extract_number(text, "归属于上市公司股东的净利润")
asset = extract_number(text, "总资产")
debt = extract_number(text, "负债合计")

print("营业收入:", revenue)
print("营业成本:", cost)
print("净利润:", profit)
print("总资产:", asset)
print("总负债:", debt)

if revenue and cost:
    gross_margin = (revenue - cost) / revenue   # 毛利率
    print("毛利率: {:.2%}".format(gross_margin))
if revenue and profit:
    net_margin = profit / revenue               # 净利率
    print("净利率: {:.2%}".format(net_margin))

# --- 用 pandas 排成表格 ---
import pandas as pd
df = pd.DataFrame({
    "指标": ["营业收入", "营业成本", "净利润","总资产","总负债"],
    "金额(元)": [revenue, cost, profit,asset,debt],
})
print(df)
from openai import OpenAI

# 创建客户端:告诉程序用哪个 key、连 DeepSeek 的服务器
client = OpenAI(
    api_key="sk-在这里填你的key",          # ← 把你的 key 粘进来
    base_url="https://api.deepseek.com"
)

# 把指标拼成给 AI 的"问题"
prompt = f"""以下是贵州茅台2025年度报告的核心财务数据：
营业收入：{revenue:,.2f} 元（同比 -1.21%）
营业成本：{cost:,.2f} 元
净利润：{profit:,.2f} 元（同比 -4.53%）
毛利率：{gross_margin:.2%}
净利率：{net_margin:.2%}

请写一份200字以内的分析报告，包括：经营表现、盈利能力、潜在风险。
注意：营收和净利润同比均小幅下滑，分析时必须体现这一点。"""

# 发起对话请求
resp = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一名资深的金融分析师，用简洁专业的语言分析上市公司财务数据。"},
        {"role": "user", "content": prompt}
    ]
)

# 打印 AI 的回复
print(resp.choices[0].message.content)
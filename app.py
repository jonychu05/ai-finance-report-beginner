# AI 财报分析工具 v2.1（UX 优化 P3：图表单位 + toast + 标签交互）
import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO
from openai import OpenAI
from indicators import analyze_pdf, search_keyword
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AI 财报分析工具", page_icon="📊", layout="wide")

st.markdown("""
<style>
    /* ===== 隐藏 Streamlit 默认 UI（P0-1） ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {visibility: hidden; height: 0;}
    .stDeployButton {display: none !important;}
    #viewerBadge {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}

    /* ===== 品牌配色体系（P0-2）：金融科技风 ===== */
    :root {
        --primary: #0958D9;
        --primary-light: #E6F4FF;
        --primary-strong: #1677FF;
        --cyan: #13C2C2;
        --success: #52C41A;
        --danger: #F5222D;
        --warning: #FA8C16;
        --bg: #F7F8FA;
        --card-bg: #FFFFFF;
        --text-1: #1F2329;
        --text-2: #4E5969;
        --text-3: #86909C;
        --border: #E5E8EF;
    }
    .stApp {background-color: var(--bg);}
    h1, h2, h3 {color: var(--text-1);}

    /* 全局统一：按钮主色 */
    .stButton > button[kind="primary"] {background-color: var(--primary); border-color: var(--primary);}
    .stButton > button[kind="primary"]:hover {background-color: var(--primary-strong); border-color: var(--primary-strong);}
    .stDownloadButton > button {background-color: var(--primary); color: #fff; border-color: var(--primary);}
    .stDownloadButton > button:hover {background-color: var(--primary-strong);}
    /* 链接与强调文字 */
    a {color: var(--primary);}
    strong {color: var(--text-1);}

    /* ===== 标签语义修正（P0-3）：已选指标 主色浅底+主色字 ===== */
    span[data-baseweb="tag"] {
        background-color: var(--primary-light) !important;
        color: var(--primary) !important;
        border-radius: 6px !important;
        border: 1px solid #B7D5FF !important;
    }
    span[data-baseweb="tag"] svg {color: var(--primary) !important; width: 14px; height: 14px; cursor: pointer; transition: color .15s ease;}
    span[data-baseweb="tag"] svg:hover {color: var(--danger) !important;}

    /* ===== 排版与卡片 ===== */
    .block-container {padding-top: 1.6rem; max-width: 1280px;}
    .hero-title {font-size: 2rem; font-weight: 700; color: var(--primary); margin-bottom: .2rem; letter-spacing: -0.5px;}
    .hero-sub {color: var(--text-3); font-size: .95rem; margin-bottom: .6rem;}
    .card {background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: .9rem 1.1rem; box-shadow: 0 1px 3px rgba(31,35,41,.04);}
    .metric-label {color: var(--text-3); font-size: .78rem;}
    .metric-value {color: var(--text-1); font-size: 1.3rem; font-weight: 700;}
    .ok {color: var(--success);} .warn {color: var(--warning);} .err {color: var(--danger);}
    .footer {color: var(--text-3); font-size: .75rem; text-align: center; margin-top: 2rem;}
    .feature-tag {display:inline-block; padding:2px 10px; background:var(--primary-light); color:var(--primary); border-radius:12px; font-size:.78rem; margin:2px 4px 2px 0; font-weight:500;}

    /* ===== P1-① 品牌头部导航 + 合规页脚 ===== */
    .app-header {display:flex; align-items:center; justify-content:space-between; padding:.4rem 0 .8rem; border-bottom:1px solid var(--border); margin-bottom:1rem;}
    .app-brand {display:flex; align-items:center; gap:10px; font-size:1.05rem; font-weight:700; color:var(--primary);}
    .brand-logo {width:26px; height:26px; border-radius:6px; background:var(--primary); color:#fff; display:flex; align-items:center; justify-content:center; font-size:.85rem;}
    .app-nav a {color:var(--text-2); text-decoration:none; font-size:.85rem; margin-left:18px; font-weight:500;}
    .app-nav a:hover {color:var(--primary);}
    .legal-footer {border-top:1px solid var(--border); margin-top:2rem; padding-top:.8rem; text-align:center; color:var(--text-3); font-size:.75rem; line-height:1.8;}

    /* ===== P2-e 交互动效 ===== */
    .card {transition: box-shadow .2s ease, transform .2s ease;}
    .card:hover {box-shadow: 0 4px 14px rgba(9,88,217,.14); transform: translateY(-1px);}
    .stButton > button, .stDownloadButton > button {transition: all .18s ease;}
    .stButton > button:hover, .stDownloadButton > button:hover {box-shadow: 0 2px 8px rgba(9,88,217,.18); transform: translateY(-1px);}

    /* ===== P1-⑤ 统一设计语言：圆角/阴影/边框 ===== */
    .stButton > button, .stDownloadButton > button, .stTextInput input, .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div, .stFileUploader > div, .stTextArea textarea {
        border-radius: 8px !important;
    }
    .card {border-radius: 12px; box-shadow: 0 1px 4px rgba(31,35,41,.06);}
    .stDataFrame {border-radius: 10px; overflow: hidden; border: 1px solid var(--border);}
    [data-testid="stSidebar"] {border-right: 1px solid var(--border);}
    [data-testid="stWidgetLabel"] p {font-size: .85rem; color: var(--text-2); font-weight: 500;}
</style>
""", unsafe_allow_html=True)

st.markdown('''
<div class="app-header">
  <div class="app-brand"><span class="brand-logo"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="4" y1="20" x2="4" y2="12"/><line x1="10" y1="20" x2="10" y2="5"/><line x1="16" y1="20" x2="16" y2="14"/><line x1="22" y1="20" x2="22" y2="9"/></svg></span> AI 财报分析工具</div>
  <div class="app-nav">
    <a href="#" onclick="return false;">单份分析</a>
    <a href="#" onclick="return false;">多年报对标</a>
    <a href="https://github.com/jonychu05/ai-finance-report-beginner" target="_blank">GitHub</a>
  </div>
</div>
''', unsafe_allow_html=True)

st.markdown('<div class="hero-title">AI 财报分析工具</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">上市年报 AI 解析 · 指标提取 · 勾稽校验 · 多年报对标 · 一键导出</div>', unsafe_allow_html=True)
st.markdown('<div>'
            '<span class="feature-tag">20+ 核心指标</span>'
            '<span class="feature-tag">勾稽自检</span>'
            '<span class="feature-tag">关键词搜索</span>'
            '<span class="feature-tag">多年报对比</span>'
            '<span class="feature-tag">报告导出</span>'
            '<span class="feature-tag">多模型支持</span>'
            '</div>', unsafe_allow_html=True)

MODEL_PROVIDERS = {
    "DeepSeek 深度求索": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "豆包（火山方舟）": {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-seed-1-6-250615"},
    "通义千问（阿里云）": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "Kimi（月之暗面）": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "智谱 GLM": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
}

with st.sidebar:
    st.markdown("### 配置")
    provider_name = st.selectbox("模型供应商", list(MODEL_PROVIDERS.keys()), key="provider")
    provider = MODEL_PROVIDERS[provider_name]
    api_key = st.text_input(f"{provider_name} API Key", type="password",
                            help="仅用于当前会话调用，不会存储或上传到服务器；使用后刷新页面即可清除")
    model_name = st.text_input("模型名称", value=provider["model"], key="model_name")
    base_url = provider["base_url"]

    st.markdown("---")
    st.markdown("### 图表设置")
    preset = st.selectbox("指标预设方案", ["综合对标", "盈利能力", "偿债风险", "现金流质量"], key="preset")

# ================= 页面 =================
uploaded = st.file_uploader("上传年报 PDF（可多选，≥2 份进入对比模式）", type=["pdf"], accept_multiple_files=True)

# ============ 指标标签 ============
LABELS = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润", "扣非净利润",
          "总资产", "总负债", "归母净资产", "少数股东权益", "总股本", "流动资产", "流动负债", "货币资金",
          "基本每股收益", "经营现金流净额", "营收同比%", "净利同比%", "毛利率%", "净利率%",
          "ROE%", "资产负债率%", "流动比率"]
RATIO_KEYS = {"毛利率%", "净利率%", "ROE%", "资产负债率%", "流动比率"}

# 真正以百分比展示的指标（流动比率是倍数，不加%）
PERCENT_COLS = {"毛利率%", "净利率%", "ROE%", "资产负债率%", "营收同比%", "净利同比%"}

def fmt_styler(df):
    """对比表样式：千分位 + 百分比 + 条件格式（P1-③④）"""
    fmt = {}
    for col in df.columns:
        if col in PERCENT_COLS:
            fmt[col] = lambda x: f"{x:.2f}%" if pd.notna(x) else "—"
        elif col in AMOUNT_KEYS:
            fmt[col] = lambda x: f"{x:,.2f}" if pd.notna(x) else "—"
        else:
            fmt[col] = lambda x: f"{x:,.2f}" if pd.notna(x) else "—"
    styler = df.style.format(fmt)

    # 每列最大值浅蓝高亮（axis=0 按列）
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().any()]
    if num_cols:
        styler = styler.highlight_max(subset=num_cols, color="#E6F4FF", axis=0)

    # 同比红绿：正红（涨）负绿（跌），A股惯例
    def _yoy(v):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        if v > 0:
            return "color:#F5222D;font-weight:600;"
        if v < 0:
            return "color:#52C41A;font-weight:600;"
        return ""
    # 异常区间高亮（财务合理性检查）
    def _range(v, lo, hi):
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return ""
        if not (lo <= v <= hi):
            return "background-color:#FFF7E6;color:#D46B08;"
        return ""
    for col in ["营收同比%", "净利同比%"]:
        if col in df.columns:
            styler = styler.map(_yoy, subset=[col])
    for col, lo, hi in [("毛利率%", 0, 100), ("净利率%", -100, 100), ("资产负债率%", 0, 100)]:
        if col in df.columns:
            styler = styler.map(lambda v, lo=lo, hi=hi: _range(v, lo, hi), subset=[col])
    return styler

def fmt_single_df(df):
    """单份指标表：金额转亿+千分位、比率加%，避免科学计数法"""
    rows = []
    for _, r in df.iterrows():
        k, v = r["指标"], r["数值"]
        if v is None or (isinstance(v, float) and pd.isna(v)):
            rows.append((k, "—"))
        elif k in PERCENT_COLS:
            rows.append((k, f"{v:.2f}%"))
        elif k in AMOUNT_KEYS:
            rows.append((k, f"{v / 1e8:,.2f} 亿"))
        else:
            rows.append((k, f"{v:,.2f}"))
    return pd.DataFrame(rows, columns=["指标", "数值"])
AMOUNT_KEYS = {"营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润", "扣非净利润",
               "总资产", "总负债", "归母净资产", "少数股东权益", "总股本", "流动资产", "流动负债",
               "货币资金", "经营现金流净额"}

def clean_name(fname):
    """公司名清洗：去掉扩展名/年份/年报字样/前导编号，图表横坐标短标签用"""
    name = re.sub(r"\.pdf$", "", fname, flags=re.I)
    name = re.sub(r"\d{4}", "", name)
    name = re.sub(r"年度报告|年报|年度", "", name)
    name = re.sub(r"^[\d_\-]+", "", name)
    name = re.sub(r"[_\-]+", "", name)
    return name.strip() or fname

def fmt_val(v, key):
    """按指标类型格式化：金额转亿、比率保留%"""
    if v is None:
        return None
    if key in RATIO_KEYS:
        return round(v, 2)
    if key in AMOUNT_KEYS:
        return round(v / 1e8, 2)
    return round(v, 4)

def chart_type_of(key):
    """自动选图：按指标类型返回图表类型说明"""
    if key in RATIO_KEYS:
        return "比率类 → 柱状图（%）"
    if key in AMOUNT_KEYS:
        return "金额类 → 柱状图（亿元）"
    return "数值类 → 柱状图（原单位）"

def _mark_dl(msg):
    """导出按钮回调：标记 toast 消息（P3-2）"""
    st.session_state["_dl_msg"] = msg

PRESET_KEYS = {
    "综合对标": ["营业收入", "净利润", "毛利率%", "ROE%", "资产负债率%"],
    "盈利能力": ["营业收入", "净利润", "归母净利润", "毛利率%", "净利率%", "ROE%"],
    "偿债风险": ["总资产", "总负债", "资产负债率%", "流动比率"],
    "现金流质量": ["经营现金流净额", "净利润", "营业收入"],
}

if not uploaded:
    # P2-a：首页引导区 + 空状态
    st.markdown("### 三步完成一份年报分析")
    c1, c2, c3 = st.columns(3)
    for col, (t, d, c) in zip([c1, c2, c3], [
        ("1️⃣ 上传年报", "拖入上市公司年报 PDF，可多选；支持制造业、银行等格式", "#0958D9"),
        ("2️⃣ AI 提取与校验", "自动提取 20+ 指标、勾稽自检、任意关键词全文搜索", "#13C2C2"),
        ("3️⃣ 对比与导出", "多年报对标 + 按指标自动选图，报告/数据一键导出", "#722ED1")]):
        col.markdown(f'<div class="card" style="border-top:3px solid {c}">'
                     f'<div style="font-weight:700;margin-bottom:6px;color:var(--text-1)">{t}</div>'
                     f'<div style="color:var(--text-2);font-size:.85rem;line-height:1.6">{d}</div></div>',
                     unsafe_allow_html=True)

    st.markdown("### 核心能力")
    feat_rows = [
        [("20+ 指标自动提取", "单位自适应 · 繁体转简体 · 制造业/银行通吃"), ("任意指标全文搜索", "关键词即查 · 返回原文 + 行号")],
        [("勾稽自检 · 人工兜底", "总资产≈负债+权益 · AI 初稿须人工复核"), ("AI 资深专家报告", "多模型可选 · 四段式 · 禁臆造")],
        [("多年报对标", "分组 Tab 查看 · 固定色板自动选图"), ("一键导出交付", "报告 Markdown · 数据 CSV")],
    ]
    for (t1, d1), (t2, d2) in feat_rows:
        ca, cb = st.columns(2)
        ca.markdown(f'<div class="card"><div style="font-weight:600;color:var(--primary);margin-bottom:4px">{t1}</div>'
                    f'<div style="color:var(--text-2);font-size:.82rem;line-height:1.6">{d1}</div></div>', unsafe_allow_html=True)
        cb.markdown(f'<div class="card"><div style="font-weight:600;color:var(--primary);margin-bottom:4px">{t2}</div>'
                    f'<div style="color:var(--text-2);font-size:.82rem;line-height:1.6">{d2}</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:var(--text-3);font-size:.85rem;margin:.6rem 0 1.2rem">'
                '上传 1 份 = 单份深度分析 ｜ 上传 ≥2 份 = 多年报对标</div>', unsafe_allow_html=True)

if uploaded:
    if len(uploaded) == 1:
        f0 = uploaded[0]
        with st.spinner("正在提取 20 项指标…（约 10-30 秒）"):
            D, checks = analyze_pdf(BytesIO(f0.getvalue()))

        st.success("✅ 提取完成，请人工核对")

        # KPI 卡片
        c1, c2, c3, c4 = st.columns(4)
        for col, (label, key, fmt) in zip([c1, c2, c3, c4], [
            ("营业收入", "营业收入", "{:,.2f} 亿"), ("净利润", "净利润", "{:,.2f} 亿"),
            ("毛利率", "毛利率%", "{:.2f}%"), ("ROE", "ROE%", "{:.2f}%")]):
            v = D.get(key)
            col.markdown(f'<div class="card"><div class="metric-label">{label}</div>'
                         f'<div class="metric-value">{fmt.format(v/1e8) if "亿" in fmt else fmt.format(v)}</div></div>'
                         if v is not None else f'<div class="card"><div class="metric-label">{label}</div><div class="metric-value">—</div></div>',
                         unsafe_allow_html=True)
    
        # 勾稽自检
        st.markdown("### 勾稽自检")
        for desc, val, status in checks:
            icon = {"ok": "✅", "warn": "⚠️", "err": "❌"}[status]
            st.markdown(f"{icon} **{desc}**：{val:.2f}")
    
        # 20 指标表格
        st.markdown("### 20 项指标明细")
        labels = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润", "扣非净利润",
                  "总资产", "总负债", "归母净资产", "少数股东权益", "总股本", "流动资产", "流动负债","货币资金",
                  "基本每股收益", "经营现金流净额", "营收同比%", "净利同比%", "毛利率%", "净利率%",
                  "ROE%", "资产负债率%", "流动比率"]
        missing = [k for k in labels if D.get(k) is None]
        df_raw = pd.DataFrame([{"指标": k, "数值": D.get(k)} for k in labels])
        df = fmt_single_df(df_raw)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**覆盖率：{len(labels)-len(missing)}/{len(labels)}**"
                    + (f" ｜ 未提取到：{'、'.join(missing)}" if missing else " ｜ 全部提取成功 ✅"))
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("导出指标数据（CSV）", csv_bytes, file_name="财务指标明细.csv",
                           mime="text/csv", key="dl_csv", on_click=_mark_dl, args=("✅ 指标数据已导出",))

        # 人工补充（覆盖率的兜底）
        if missing:
            st.markdown("### 人工补充缺失指标")
            manual = {}
            for k in missing:
                v = st.text_input(f"{k}（未提取到，可手动填写数值）", key=f"m_{k}")
                if v:
                    try:
                        manual[k] = float(v.replace(",", ""))
                    except ValueError:
                        pass
            if manual:
                D.update(manual)
                st.success("已更新，生成报告时将使用补充后的数据")
    
        # 自定义指标搜索（台阶 4.7）
        st.markdown("### 自定义指标搜索")
        kw = st.text_input("输入任意指标关键词，引擎在全文检索并返回数值（如：研发费用、存货、应收账款、利息收入）",
                           placeholder="例如：研发费用", key="kw_search")
        if kw and kw.strip():
            with st.spinner("全文搜索中…"):
                results, suggestions = search_keyword(f0.getvalue(), kw)
            if results:
                st.success(f"✅ 找到 {len(results)} 处匹配，请人工核对数值（**单位以年报原表为准**）")
                rows = [{
                    "类型": "表头/叙述" if (not r["nums"]) else "数据行",
                    "原文": r["text"],
                    "提取到数值": ", ".join(f"{x:,.2f}" for x in r["nums"][:4]) if r["nums"] else "（本行无数值，请看上/下一行）",
                    "所在行": r["line"],
                } for r in results]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.warning(f"未找到「{kw.strip()}」的精确匹配")
                if suggestions:
                    st.markdown("**可能包含该指标的相似表述（请人工确认）：**")
                    for s in suggestions[:8]:
                        st.markdown(f"- {s}")
                else:
                    st.markdown("没有找到相似表述。建议：换更简短的关键词，或在年报目录中确认该指标的标准叫法后再搜。")
    
        # AI 报告（台阶4.9：资深专家模式 + 防臆造 + 导出）
        st.markdown("### AI 分析报告")
        if st.button("生成 AI 分析报告（资深专家模式）", type="primary", use_container_width=True):
            if not api_key:
                st.warning("请先在左侧填写 DeepSeek API Key")
            else:
                parts = [f"{k}：{v:,.2f}" for k, v in D.items() if isinstance(v, (int, float))]
                prompt = (
                    "请以资深金融分析专家身份，对以下上市公司年报核心财务数据进行专业分析。\n\n"
                    "【核心数据】\n" + "\n".join(parts) + "\n\n"
                    "【报告结构】\n"
                    "一、经营表现：分析营收规模与同比趋势，结合数据判断增长质量；\n"
                    "二、盈利能力：分析毛利率、净利率、ROE，指出盈利质量与定价能力；\n"
                    "三、偿债与资产结构：分析资产负债率、流动比率等，评估偿债风险；\n"
                    "四、风险提示：列出基于数据可见的潜在风险点。\n\n"
                    "【硬性要求】\n"
                    "1. 所有结论必须严格基于以上数据，禁止编造任何未提供的数据或指标；\n"
                    "2. 引用具体数字时标注数值，如：营业收入 1688.38 亿元（同比 -1.21%）；\n"
                    "3. 避免空泛套话，每段给出有信息量的判断；\n"
                    "4. 使用清晰的 Markdown 格式输出，小标题加粗。"
                )
                client = OpenAI(api_key=api_key, base_url=base_url)
                with st.spinner(f"AI 正在深度分析…（{provider_name} · 资深专家模式）"):
                    try:
                        resp = client.chat.completions.create(
                            model=model_name.strip(),
                            messages=[{"role": "system", "content": "你是资深金融分析专家，熟悉A股上市公司财报分析，擅长从财务数据中提炼可靠结论。"},
                                      {"role": "user", "content": prompt}])
                        report_text = resp.choices[0].message.content
                        st.markdown(report_text)
                        st.download_button("下载分析报告（Markdown）", report_text,
                                           file_name="AI财报分析报告.md", mime="text/markdown", key="dl_report", on_click=_mark_dl, args=("✅ 分析报告已导出",))
                    except Exception as e:
                        st.error(f"调用 AI 失败：{e}")
    
    else:
        # ============ 台阶 4.8：多年报对比 + 自动选图 ============
        st.markdown("### 多份年报对比（台阶 4.8）")
        prog = st.progress(0, text="准备解析年报…")
        records = []
        total = len(uploaded)
        for idx, f in enumerate(uploaded):
            prog.progress(idx / total, text=f"正在解析 {f.name}（{idx + 1}/{total}）…")
            try:
                D, checks = analyze_pdf(BytesIO(f.getvalue()))
                records.append({"file": f.name, "D": D, "checks": checks})
                prog.progress((idx + 1) / total, text=f"✅ {f.name} 提取完成")
            except Exception as e:
                st.error(f"{f.name} 提取失败：{e}")
        prog.empty()

        if not records:
            st.warning("没有成功提取到任何年报，请检查文件是否为有效 PDF")
        else:
            # 覆盖率汇总
            st.markdown("#### 提取覆盖率")
            cov_rows = []
            for r in records:
                got = [k for k in LABELS if r["D"].get(k) is not None]
                cov_rows.append({"公司/年报": r["file"], "提取指标": f"{len(got)}/{len(LABELS)}",
                                 "缺失": "、".join([k for k in LABELS if r["D"].get(k) is None]) or "无"})
            st.dataframe(pd.DataFrame(cov_rows), use_container_width=True, hide_index=True)

            # 对比表格（公司 × 指标，金额转亿）
            st.markdown("#### 指标对比明细（金额单位：亿元）")
            df_cmp = pd.DataFrame({r["file"]: [fmt_val(r["D"].get(k), k) for k in LABELS] for r in records},
                                  index=LABELS).T
            # 指标分组 Tab（P0-4：解决 15+ 列横向滚动，按财务维度分组）
            TAB_GROUPS = {
                "盈利能力": ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润",
                             "扣非净利润", "毛利率%", "净利率%", "ROE%", "基本每股收益"],
                "偿债能力": ["总资产", "总负债", "归母净资产", "少数股东权益", "资产负债率%", "流动比率"],
                "营运与现金流": ["总股本", "流动资产", "流动负债", "货币资金", "经营现金流净额"],
                "成长能力": ["营收同比%", "净利同比%"],
            }
            grouped_cols = [c for cols in TAB_GROUPS.values() for c in cols]
            if set(grouped_cols) != set(LABELS):
                st.warning("⚠️ 指标分组未覆盖全部指标，请检查 TAB_GROUPS 配置")
            tabs = st.tabs([name for name in TAB_GROUPS.keys()])
            for tab, (name, cols) in zip(tabs, TAB_GROUPS.items()):
                with tab:
                    avail = [c for c in cols if c in df_cmp.columns]
                    st.dataframe(fmt_styler(df_cmp[avail]), use_container_width=True, height=380)
            with st.expander("查看全部指标（宽表，仅供高级用户）"):
                st.dataframe(fmt_styler(df_cmp), use_container_width=True, height=420)
            csv_cmp = df_cmp.to_csv().encode("utf-8-sig")
            st.download_button("导出对比数据（CSV）", csv_cmp, file_name="多年报指标对比.csv",
                               mime="text/csv", key="dl_cmp_csv", on_click=_mark_dl, args=("✅ 对比数据已导出",))

            # 指标多选 + 图表（台阶4.8优化版：Plotly + 多图表类型 + Excel简洁风）
            st.markdown("#### 指标对比图表")
            default_keys = [k for k in PRESET_KEYS.get(preset, PRESET_KEYS["综合对标"]) if k in LABELS]
            sel_keys = st.multiselect("选择要对比的指标（柱状/条形/折线按每个指标出图；饼图/圆环/直方图取第一个指标；散点图需另选X/Y）",
                                      LABELS, default=default_keys, key=f"cmp_sel_{preset}")
            chart_mode = st.selectbox("图表类型", ["自动（按指标类型）", "柱状图", "条形图（横向）", "折线图",
                                                  "饼图（占比）", "圆环图（占比）", "直方图（分布）", "散点图（相关性）",
                                                  "雷达图（财务画像）", "热力图（指标矩阵）", "股价图"],
                                      key="cmp_mode")
            st.caption("提示：自动模式按指标类型选图；雷达/热力图适合看整体画像；股价图需多期行情数据，此处自动降级为折线")

            # 公司名清洗：去掉编号/年份/扩展名，图表横坐标短标签
            clean_df = df_cmp.copy()
            clean_df.index = [clean_name(x) for x in df_cmp.index]

            # 多公司固定区分色板（P0-5）：与品牌色一致，所有图表统一
            COMPANY_PALETTE = ["#0958D9", "#13C2C2", "#722ED1", "#FA8C16", "#52C41A", "#EB2F96", "#2F54EB", "#F5222D"]
            cmap = {name: COMPANY_PALETTE[i % len(COMPANY_PALETTE)] for i, name in enumerate(clean_df.index)}

            def render_bar(key, horizontal=False):
                d = clean_df[[key]].dropna()
                if d.empty:
                    return False
                unit_txt = "%" if key in PERCENT_COLS else ("亿元" if key in AMOUNT_KEYS else "")
                title = f"{key}（{unit_txt}）" if unit_txt else key
                if horizontal:
                    fig = px.bar(d, y=d.index, x=key, color=d.index, orientation="h", title=title,
                                 color_discrete_map=cmap)
                    fig.update_traces(texttemplate='%{x:,.2f}', textposition='outside', width=0.55,
                                      textfont=dict(size=10))
                    fig.update_layout(template="plotly_white", height=340, showlegend=True,
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                      xaxis_title="", xaxis=dict(ticksuffix=unit_txt),
                                      margin=dict(l=10, r=20, t=55, b=10))
                else:
                    fig = px.bar(d, x=d.index, y=key, color=d.index, title=title,
                                 color_discrete_map=cmap)
                    fig.update_traces(texttemplate='%{y:,.2f}', textposition='outside', width=0.55,
                                      textfont=dict(size=10))
                    fig.update_layout(template="plotly_white", xaxis_tickangle=0, height=340, showlegend=True,
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                      yaxis_title="", yaxis=dict(ticksuffix=unit_txt),
                                      xaxis_title="", hovermode="x unified",
                                      margin=dict(l=10, r=10, t=55, b=10))
                st.plotly_chart(fig, use_container_width=True)
                return True

            if chart_mode == "散点图（相关性）":
                xk = st.selectbox("X 轴指标", LABELS, index=LABELS.index("营业收入"), key="cmp_xk")
                yk = st.selectbox("Y 轴指标", LABELS, index=LABELS.index("净利润"), key="cmp_yk")
                d = clean_df[[xk, yk]].dropna()
                if d.empty:
                    st.info("所选两个指标没有同时提取到的公司，无法画散点图")
                else:
                    fig = px.scatter(d, x=xk, y=yk, color=d.index, text=d.index, title=f"{xk} vs {yk} 相关关系",
                                     color_discrete_map=cmap)
                    fig.update_traces(textposition="top center")
                    fig.update_layout(template="plotly_white", height=420, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
            elif chart_mode == "雷达图（财务画像）":
                radar_keys = [k for k in ["毛利率%", "净利率%", "ROE%", "资产负债率%", "营收同比%"] if k in LABELS]
                radar_keys = st.multiselect("选择雷达维度指标（3-6 个，建议比率/同比类）", LABELS,
                                            default=radar_keys, key="radar_sel")
                radar_keys = [k for k in radar_keys if k in clean_df.columns]
                if len(radar_keys) < 3:
                    st.info("请至少选择 3 个可比较的指标作为雷达维度")
                else:
                    st.caption("各指标已按公司间 min-max 归一化到 0-100（相对强弱），不同量纲可同图比较")
                    d = clean_df[radar_keys].dropna(how="all")
                    fig = go.Figure()
                    for comp in d.index:
                        vals = []
                        for k in radar_keys:
                            v = d.loc[comp, k]
                            vals.append(float(v) if pd.notna(v) else float("nan"))
                        norm = []
                        for i, k in enumerate(radar_keys):
                            col_vals = [d.loc[c, k] for c in d.index if pd.notna(d.loc[c, k])]
                            if not col_vals or pd.isna(vals[i]):
                                norm.append(0); continue
                            lo, hi = min(col_vals), max(col_vals)
                            norm.append(100 if hi == lo else (vals[i] - lo) / (hi - lo) * 100)
                        fig.add_trace(go.Scatterpolar(r=norm, theta=radar_keys, fill="toself",
                                                      name=comp, opacity=0.5,
                                                      line_color=cmap.get(comp, "#0958D9")))
                    fig.update_layout(template="plotly_white", height=460, showlegend=True,
                                      title="财务能力画像（雷达图 · 相对水平）",
                                      polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
                    st.plotly_chart(fig, use_container_width=True)
            elif chart_mode == "热力图（指标矩阵）":
                hm_cols = [c for c in LABELS if c in clean_df.columns]
                d = clean_df[hm_cols]
                norm = (d - d.min()) / (d.max() - d.min())
                fig = px.imshow(norm, x=hm_cols, y=d.index, aspect="auto",
                                color_continuous_scale=["#E6F4FF", "#FFFFFF", "#0958D9"],
                                title="指标矩阵热力图（按列归一化 0-1，蓝深=相对更高）")
                fig.update_layout(template="plotly_white", height=460, margin=dict(l=10, r=10, t=50, b=10))
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            elif chart_mode == "股价图":
                st.info("股价图（K线）需要多期行情的开盘/收盘/最高/最低数据，当前为年报指标对比数据暂不适用；已用折线图展示指标趋势。")
                cols3 = st.columns(3)
                for idx, key in enumerate(sel_keys):
                    with cols3[idx % 3]:
                        d = clean_df[[key]].dropna()
                        if not d.empty:
                            u2 = "%" if key in PERCENT_COLS else ("亿元" if key in AMOUNT_KEYS else "")
                            fig = px.line(d, x=d.index, y=key, markers=True, title=f"{key} 趋势" + (f"（{u2}）" if u2 else ""))
                            fig.update_traces(line_color="#0958D9",
                                              marker=dict(color=[cmap.get(n, "#0958D9") for n in d.index], size=8))
                            fig.update_layout(template="plotly_white", height=340, xaxis_tickangle=0,
                                              hovermode="x unified", yaxis=dict(ticksuffix=u2),
                                              margin=dict(l=10, r=10, t=45, b=10))
                            st.plotly_chart(fig, use_container_width=True)
            elif chart_mode in ("饼图（占比）", "圆环图（占比）", "直方图（分布）"):
                key = sel_keys[0] if sel_keys else None
                if key is None:
                    st.info("请至少选择一个指标")
                else:
                    d = clean_df[[key]].dropna()
                    if d.empty:
                        st.info(f"「{key}」多家均未提取到，无法绘图")
                    elif "饼图" in chart_mode or "圆环" in chart_mode:
                        fig = px.pie(d, names=d.index, values=key, color=d.index,
                                     hole=(0.5 if "圆环" in chart_mode else 0), title=f"{key} 占比分布",
                                     color_discrete_map=cmap)
                        fig.update_traces(textinfo="label+percent", textposition="inside")
                        fig.update_layout(template="plotly_white", height=360, showlegend=True,
                                          margin=dict(l=10, r=10, t=45, b=10))
                        col_mid = st.columns([1, 2, 1])[1]
                        with col_mid:
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig = px.histogram(d, x=key, nbins=8, title=f"{key} 分布",
                                           color=d.index, color_discrete_map=cmap)
                        fig.update_layout(template="plotly_white", height=380)
                        st.plotly_chart(fig, use_container_width=True)
            else:
                if not sel_keys:
                    st.info("请至少选择一个指标")
                else:
                    horizontal = (chart_mode == "条形图（横向）")
                    line_mode = (chart_mode == "折线图")
                    cols3 = st.columns(3)
                    for idx, key in enumerate(sel_keys):
                        with cols3[idx % 3]:
                            if line_mode:
                                d = clean_df[[key]].dropna()
                                if d.empty:
                                    continue
                                u3 = "%" if key in PERCENT_COLS else ("亿元" if key in AMOUNT_KEYS else "")
                                fig = px.line(d, x=d.index, y=key, markers=True, title=f"{key}" + (f"（{u3}）" if u3 else ""))
                                fig.update_traces(line_color="#0958D9",
                                                  marker=dict(color=[cmap.get(n, "#0958D9") for n in d.index], size=8))
                                fig.update_layout(template="plotly_white", xaxis_tickangle=0, height=340,
                                                  xaxis_title="", yaxis_title="", yaxis=dict(ticksuffix=u3),
                                                  hovermode="x unified",
                                                  margin=dict(l=10, r=10, t=45, b=10))
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                if not render_bar(key, horizontal=horizontal):
                                    st.markdown(f"**{key}**：多家均未提取到，跳过")

if st.session_state.get("_dl_msg"):
    st.toast(st.session_state.pop("_dl_msg"))

st.markdown('''
<div class="legal-footer">
  数据仅本地处理 · AI 初稿需人工复核 ｜ 演示数据来自上市公司公开年报，不涉及实习单位内部数据<br>
  © 2026 AI 财报分析工具 · jonychu05@gmail.com
</div>
''', unsafe_allow_html=True)

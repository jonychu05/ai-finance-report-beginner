# AI 财报分析工具 v1.5（台阶 4.9：AI 专家报告 + 导出）
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
    .hero-title{font-size:2.2rem;font-weight:700;background:linear-gradient(90deg,#4C8BF5,#7B6CF6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.2rem}
    .hero-sub{color:#9AA4B2;font-size:1rem;margin-bottom:1rem}
    .card{background:#161B22;border:1px solid #232A35;border-radius:12px;padding:1rem 1.2rem}
    .metric-label{color:#9AA4B2;font-size:.8rem}
    .metric-value{color:#E8EAF0;font-size:1.4rem;font-weight:700}
    .ok{color:#10B981}.warn{color:#F59E0B}.err{color:#EF4444}
    .footer{color:#6B7280;font-size:.75rem;text-align:center;margin-top:2rem}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero-title">📊 AI 财报分析工具</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">20 项核心指标 · 同比 · 勾稽自检 · 关键词搜索 · 多年报对比 · 报告导出 · v1.5</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🔑 配置")
    api_key = st.text_input("DeepSeek API Key", type="password", help="只在本地使用，不会上传")

# ================= 页面 =================
uploaded = st.file_uploader("📄 上传年报 PDF（可多选，≥2 份进入对比模式）", type=["pdf"], accept_multiple_files=True)

# ============ 指标标签 ============
LABELS = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润", "扣非净利润",
          "总资产", "总负债", "归母净资产", "少数股东权益", "总股本", "流动资产", "流动负债", "货币资金",
          "基本每股收益", "经营现金流净额", "营收同比%", "净利同比%", "毛利率%", "净利率%",
          "ROE%", "资产负债率%", "流动比率"]
RATIO_KEYS = {"毛利率%", "净利率%", "ROE%", "资产负债率%", "流动比率"}
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
        st.markdown("### 🔍 勾稽自检")
        for desc, val, status in checks:
            icon = {"ok": "✅", "warn": "⚠️", "err": "❌"}[status]
            st.markdown(f"{icon} **{desc}**：{val:.2f}")
    
        # 20 指标表格
        st.markdown("### 📋 20 项指标明细")
        labels = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润", "归母净利润", "扣非净利润",
                  "总资产", "总负债", "归母净资产", "少数股东权益", "总股本", "流动资产", "流动负债","货币资金",
                  "基本每股收益", "经营现金流净额", "营收同比%", "净利同比%", "毛利率%", "净利率%",
                  "ROE%", "资产负债率%", "流动比率"]
        missing = [k for k in labels if D.get(k) is None]
        df = pd.DataFrame([{"指标": k, "数值": D.get(k)} for k in labels])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**覆盖率：{len(labels)-len(missing)}/{len(labels)}**"
                    + (f" ｜ 未提取到：{'、'.join(missing)}" if missing else " ｜ 全部提取成功 ✅"))
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 导出指标数据（CSV）", csv_bytes, file_name="财务指标明细.csv",
                           mime="text/csv", key="dl_csv")

        # 人工补充（覆盖率的兜底）
        if missing:
            st.markdown("### ✍️ 人工补充缺失指标")
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
        st.markdown("### 🔎 自定义指标搜索")
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
        st.markdown("### 🤖 生成 AI 分析报告")
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
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                with st.spinner("AI 正在深度分析…（资深专家模式）"):
                    try:
                        resp = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "system", "content": "你是资深金融分析专家，熟悉A股上市公司财报分析，擅长从财务数据中提炼可靠结论。"},
                                      {"role": "user", "content": prompt}])
                        report_text = resp.choices[0].message.content
                        st.markdown(report_text)
                        st.download_button("⬇️ 下载分析报告（Markdown）", report_text,
                                           file_name="AI财报分析报告.md", mime="text/markdown", key="dl_report")
                    except Exception as e:
                        st.error(f"调用 AI 失败：{e}")
    
    else:
        # ============ 台阶 4.8：多年报对比 + 自动选图 ============
        st.markdown("### 📊 多份年报对比（台阶 4.8）")
        with st.spinner(f"正在提取 {len(uploaded)} 份年报指标…（每份约 10-30 秒）"):
            records = []
            for f in uploaded:
                try:
                    D, checks = analyze_pdf(BytesIO(f.getvalue()))
                    records.append({"file": f.name, "D": D, "checks": checks})
                except Exception as e:
                    st.error(f"{f.name} 提取失败：{e}")

        if not records:
            st.warning("没有成功提取到任何年报，请检查文件是否为有效 PDF")
        else:
            # 覆盖率汇总
            st.markdown("#### ✅ 提取覆盖率")
            cov_rows = []
            for r in records:
                got = [k for k in LABELS if r["D"].get(k) is not None]
                cov_rows.append({"公司/年报": r["file"], "提取指标": f"{len(got)}/{len(LABELS)}",
                                 "缺失": "、".join([k for k in LABELS if r["D"].get(k) is None]) or "无"})
            st.dataframe(pd.DataFrame(cov_rows), use_container_width=True, hide_index=True)

            # 对比表格（公司 × 指标，金额转亿）
            st.markdown("#### 📋 指标对比明细（金额单位：亿元）")
            df_cmp = pd.DataFrame({r["file"]: [fmt_val(r["D"].get(k), k) for k in LABELS] for r in records},
                                  index=LABELS).T
            st.dataframe(df_cmp, use_container_width=True)
            csv_cmp = df_cmp.to_csv().encode("utf-8-sig")
            st.download_button("⬇️ 导出对比数据（CSV）", csv_cmp, file_name="多年报指标对比.csv",
                               mime="text/csv", key="dl_cmp_csv")

            # 指标多选 + 图表（台阶4.8优化版：Plotly + 多图表类型 + Excel简洁风）
            st.markdown("#### 📈 指标对比图表")
            default_keys = [k for k in ["营业收入", "净利润", "毛利率%", "ROE%", "资产负债率%"]]
            sel_keys = st.multiselect("选择要对比的指标（柱状/条形/折线按每个指标出图；饼图/圆环/直方图取第一个指标；散点图需另选X/Y）",
                                      LABELS, default=default_keys, key="cmp_sel")
            chart_mode = st.selectbox("图表类型", ["自动（按指标类型）", "柱状图", "条形图（横向）", "折线图",
                                                  "饼图（占比）", "圆环图（占比）", "直方图（分布）", "散点图（相关性）", "股价图"],
                                      key="cmp_mode")

            # 公司名清洗：去掉编号/年份/扩展名，图表横坐标短标签
            clean_df = df_cmp.copy()
            clean_df.index = [clean_name(x) for x in df_cmp.index]

            def render_bar(key, horizontal=False):
                d = clean_df[[key]].dropna()
                if d.empty:
                    return False
                if horizontal:
                    fig = px.bar(d, y=d.index, x=key, orientation="h", title=f"{key}",
                                 color_discrete_sequence=["#4C8BF5"])
                    fig.update_traces(texttemplate='%{x:,.2f}', textposition='outside', width=0.55)
                    fig.update_layout(template="plotly_white", height=340,
                                      margin=dict(l=10, r=20, t=45, b=10))
                else:
                    fig = px.bar(d, x=d.index, y=key, title=f"{key}",
                                 color_discrete_sequence=["#4C8BF5"])
                    fig.update_traces(texttemplate='%{y:,.2f}', textposition='outside', width=0.55)
                    fig.update_layout(template="plotly_white", xaxis_tickangle=0, height=340,
                                      margin=dict(l=10, r=10, t=45, b=10), xaxis_title="", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)
                return True

            if chart_mode == "散点图（相关性）":
                xk = st.selectbox("X 轴指标", LABELS, index=LABELS.index("营业收入"), key="cmp_xk")
                yk = st.selectbox("Y 轴指标", LABELS, index=LABELS.index("净利润"), key="cmp_yk")
                d = clean_df[[xk, yk]].dropna()
                if d.empty:
                    st.info("所选两个指标没有同时提取到的公司，无法画散点图")
                else:
                    fig = px.scatter(d, x=xk, y=yk, text=d.index, title=f"{xk} vs {yk} 相关关系",
                                     color_discrete_sequence=["#4C8BF5"])
                    fig.update_traces(textposition="top center")
                    fig.update_layout(template="plotly_white", height=420)
                    st.plotly_chart(fig, use_container_width=True)
            elif chart_mode == "股价图":
                st.info("股价图（K线）需要多期行情的开盘/收盘/最高/最低数据，当前为年报指标对比数据暂不适用；已用折线图展示指标趋势。")
                cols3 = st.columns(3)
                for idx, key in enumerate(sel_keys):
                    with cols3[idx % 3]:
                        d = clean_df[[key]].dropna()
                        if not d.empty:
                            fig = px.line(d, x=d.index, y=key, markers=True, title=f"{key} 趋势")
                            fig.update_layout(template="plotly_white", height=340, xaxis_tickangle=0,
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
                        fig = px.pie(d, names=d.index, values=key, hole=(0.5 if "圆环" in chart_mode else 0),
                                     title=f"{key} 占比分布")
                        fig.update_traces(textinfo="label+percent", textposition="inside")
                        fig.update_layout(template="plotly_white", height=360, showlegend=True,
                                          margin=dict(l=10, r=10, t=45, b=10))
                        col_mid = st.columns([1, 2, 1])[1]
                        with col_mid:
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig = px.histogram(d, x=key, nbins=8, title=f"{key} 分布",
                                           color_discrete_sequence=["#4C8BF5"])
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
                                fig = px.line(d, x=d.index, y=key, markers=True, title=f"{key}")
                                fig.update_layout(template="plotly_white", xaxis_tickangle=0, height=340,
                                                  xaxis_title="", yaxis_title="",
                                                  margin=dict(l=10, r=10, t=45, b=10))
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                if not render_bar(key, horizontal=horizontal):
                                    st.markdown(f"**{key}**：多家均未提取到，跳过")

st.markdown('<div class="footer">数据仅本地处理 · AI 初稿需人工复核</div>', unsafe_allow_html=True)

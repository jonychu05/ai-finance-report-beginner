# indicators.py —— 通用化提取引擎 v4.2
# 支持：制造业"主要会计数据"表 + 银行"财务概要/财务摘要"表
# 处理：单位(元/千元/万元/百万元)、跨行、指标名变体、编号干扰、目录锚点、同比计算兜底

import re

def nums(ln):
    return [float(x.replace(",", "")) for x in re.findall(r"[-]?[0-9][0-9,\.]*", ln)]

def find_line(lines, keyword, start=0):
    for i in range(start, len(lines)):
        if keyword in lines[i]:
            return i
    return -1

def _is_toc_line(ln):
    """判断是否目录行：含点线，或以"中文+空格+页码数字"结尾"""
    if "……" in ln or "..." in ln or "·" in ln:
        return True
    return bool(re.search(r"[\u4e00-\u9fa5][\u4e00-\u9fa5（）()、]*\s+\d{1,3}$", ln.strip()))

def find_anchor(lines):
    """多锚点：制造业"主要会计数据"、银行"财务概要/财务摘要"；跳过目录"""
    for kw in ["主要会计数据 2025年", "主要会计数据 2024年", "主要会计数据",
               "主要会计数据和财务指标", "财务概要", "财务摘要"]:
        for i in range(len(lines)):
            if kw in lines[i] and not _is_toc_line(lines[i]):
                return i
    return -1

_DISTRACT = ["营业收入", "营业成本", "营业利润", "利润总额", "净利润",
              "总资产", "总负债", "现金流", "股本"]

def _look_around(lines, i, max_span=3):
    """邻域搜索：先同行，再上一行→下一行交替向外；数字行含其他指标名则跳过"""
    for d in range(0, max_span + 1):
        for j in (i - d, i + d):
            if 0 <= j < len(lines):
                ln = lines[j]
                n = nums(ln)
                if n:
                    if d > 0 and any(dk in ln for dk in _DISTRACT):
                        continue
                    return n
    return []

def _skip(ln, skip_keyword):
    if not skip_keyword:
        return False
    if isinstance(skip_keyword, (list, tuple)):
        return any(sk in ln for sk in skip_keyword)
    return skip_keyword in ln

def zone_val(lines, zone, keywords, idx=0, skip_keyword=None, min_val=None):
    """区域内找关键词；min_val 时取第一个大于该值的数字（跳过编号干扰）"""
    for i in zone:
        if any(kw in lines[i] for kw in keywords):
            if _skip(lines[i], skip_keyword):
                continue
            n = _look_around(lines, i)
            if min_val:
                for x in n:
                    if x > min_val:
                        return x
                continue
            if len(n) > idx:
                return n[idx]
    return None

def zone_pct(lines, zone, keywords, skip_keyword=None):
    """同比%：优先增减列，无则用两年数据计算；跳过行首编号"""
    for i in zone:
        if any(kw in lines[i] for kw in keywords):
            if _skip(lines[i], skip_keyword):
                continue
            n = _look_around(lines, i)
            if n and n[0] < 100:          # 行首编号（如"营业收入1"的1）→ 去掉
                n = n[1:]
            for x in n[2:]:
                if -1000 <= x <= 1000:     # 增减%列
                    return x
            if len(n) >= 2 and n[1] != 0:
                return (n[0] - n[1]) / n[1] * 100
    return None

# 特征词自判断（第二层）：精确匹配失败时，按"命中特征词数量"找最像的行
# 收集了各指标在 A 股年报中常见的其他叫法/表述
FEATURES = {
    "营业收入":     ["营业收入", "营业总收入", "主营业务收入"],
    "营业成本":     ["营业成本"],
    "营业利润":     ["营业利润"],
    "利润总额":     ["利润总额", "税前利润"],
    "净利润":       ["净利润"],
    "归母净利润":   ["归属于", "股东", "净利润"],
    "扣非净利润":   ["扣除非", "净利润"],
    "总资产":       ["资产总额", "总资产", "资产总计"],
    "总负债":       ["负债总额", "负债合计", "负债总计"],
    "归母净资产":   ["归属于", "股东", "权益", "净资产"],
    "总股本":       ["总股本", "股本"],
    "基本每股收益": ["每股收益"],
    "经营现金流净额": ["经营活动", "现金流量", "经营性现金流"],
    "毛利率":       ["毛利率"],
    "净利率":       ["净利率"],
    "ROE":          ["净资产收益率"],
    "资产负债率":   ["资产负债率"],
    "流动比率":     ["流动比率"],
}

def smart_match(lines, zone, key, min_hits=2, min_val=1000):
    """在区域内找同时命中多个特征词的行，按命中数排序取最佳"""
    feats = FEATURES.get(key)
    if not feats:
        return None
    best_val, best_hits = None, 0
    for i in zone:
        ln = lines[i]
        hits = sum(1 for f in feats if f in ln)
        if hits >= min_hits and hits > best_hits:
            n = _look_around(lines, i)
            for x in n:
                if x > min_val:
                    best_val, best_hits = x, hits
                    break
    return best_val

def global_val(lines, keywords, skip_keywords=None, min_val=None):
    """全文行匹配；min_val 时取第一个大数字，否则该行无大数字则跳过"""
    skips = skip_keywords or []
    for ln in lines:
        if any(kw in ln for kw in keywords):
            if any(sk in ln for sk in skips):
                continue
            n = nums(ln)
            if n:
                if min_val:
                    big = [x for x in n if x > min_val]
                    if big:
                        return big[0]
                    continue
                return n[0]
    return None

def detect_unit(lines, anchor):
    """单位自适应：主表附近优先，再全文找 人民币百万元/万元/千元 标注"""
    def parse(ln):
        if "百万元" in ln:
            return 1_000_000
        if "万元" in ln:
            return 10_000
        if "千元" in ln:
            return 1_000
        return 1
    lo, hi = max(0, anchor - 30), min(len(lines), anchor + 40)
    for i in range(lo, hi):
        if "单位" in lines[i]:
            return parse(lines[i])
    for ln in lines:
        if ("单位" in ln or "金额单位" in ln or "人民币" in ln) and ("百万元" in ln or "万元" in ln or "千元" in ln):
            return parse(ln)
    return 1

def _to_simplified(text):
    """繁体 → 简体（A+H 股公司年报可能用繁体）"""
    try:
        from opencc import OpenCC
        cc = OpenCC('t2s')
        return cc.convert(text)
    except Exception:
        return text

def analyze_pdf(file_bytes):
    """主入口：返回指标字典 + 勾稽检查"""
    import pdfplumber
    with pdfplumber.open(file_bytes) as pdf:
        pages_text = [p.extract_text() or "" for p in pdf.pages]
    text = "\n".join(pages_text)
    if any(ord(ch) > 0x4E00 and ch in "營業歸屬資產負債額萬億元淨損營經現金流量" for ch in text[:5000]):
        text = _to_simplified(text)
    lines = text.split("\n")

    anchor = find_anchor(lines)
    if anchor == -1:
        zone = range(0, len(lines))
    else:
        end_zone = find_line(lines, "主要财务指标", anchor + 1)
        if end_zone == -1 or end_zone - anchor < 30:
            end_zone = min(anchor + 60, len(lines))
        zone = range(anchor, end_zone)

    unit = detect_unit(lines, anchor)
    MV = 1000  # 金额提取最小阈值（跳过编号/序号干扰）

    D = {}
    D["营业收入"]   = zone_val(lines, zone, ["营业收入", "营业总收入", "主营业务收入"], min_val=MV) \
                      or smart_match(lines, zone, "营业收入") \
                      or global_val(lines, ["营业收入", "营业总收入", "主营业务收入"], min_val=MV)
    D["营业成本"]   = zone_val(lines, zone, ["营业成本"], min_val=MV) \
                      or global_val(lines, ["其中：营业成本", "减：营业成本", "营业成本"],
                                    skip_keywords=["构成", "同比", "占"], min_val=MV)
    D["营业利润"]   = zone_val(lines, zone, ["营业利润"], min_val=MV) \
                      or smart_match(lines, zone, "营业利润") \
                      or global_val(lines, ["营业利润"], skip_keywords=["%"], min_val=MV)
    D["利润总额"]   = zone_val(lines, zone, ["利润总额", "税前利润"], min_val=MV) \
                      or smart_match(lines, zone, "利润总额") \
                      or global_val(lines, ["利润总额", "税前利润"], skip_keywords=["%"], min_val=MV)
    D["归母净利润"] = zone_val(lines, zone, ["归属于上市公司股东", "归属于母公司股东", "归属于本行股东"], min_val=MV) \
                      or smart_match(lines, zone, "归母净利润") \
                      or global_val(lines, ["归属于上市公司股东的净利润", "归属于母公司股东的净利润", "归属于本行股东的净利润"], min_val=MV)
    D["扣非净利润"] = zone_val(lines, zone, ["扣除非经常性损益", "扣非净利润", "扣除非"], min_val=MV) or smart_match(lines, zone, "扣非净利润")
    D["经营现金流净额"] = zone_val(lines, zone, ["经营活动产生的现金", "经营活动现金流量净额", "经营性现金流量"], min_val=MV) \
                      or smart_match(lines, zone, "经营现金流净额") \
                      or global_val(lines, ["经营活动产生的现金流量净额", "经营活动现金流量净额", "经营性现金流量净额"], min_val=MV)
    D["归母净资产"] = zone_val(lines, zone, ["归属于上市公司股东的净资产", "归属于母公司股东权益", "归属于母公司股东的权益", "归属于本行股东权益",
                                           "的净资产", "净资产"], skip_keyword=["每股", "净资产收益", "少数"], min_val=MV) \
                      or zone_val(lines, zone, ["股东权益"], skip_keyword=["每股", "净资产收益", "少数"], min_val=MV) \
                      or smart_match(lines, zone, "归母净资产", min_hits=3) \
                      or global_val(lines, ["归属于上市公司股东的净资产", "归属于母公司股东的权益", "归属于本行股东权益"],
                                    skip_keywords=["每股", "少数"], min_val=MV)
    D["总资产"]     = zone_val(lines, zone, ["总资产", "资产总额", "资产总计"], min_val=MV) \
                      or smart_match(lines, zone, "总资产") \
                      or global_val(lines, ["总资产", "资产总额", "资产总计"], skip_keywords=["回报率", "比率", "占比"], min_val=MV)
    D["总负债"]     = zone_val(lines, zone, ["负债总额", "负债合计", "负债总计"], skip_keyword="流动", min_val=MV) \
                      or smart_match(lines, zone, "总负债") \
                      or global_val(lines, ["负债总额", "负债合计", "负债总计"], skip_keywords=["流动"], min_val=MV)
    D["总股本"]     = zone_val(lines, zone, ["股本"], min_val=MV) \
                      or smart_match(lines, zone, "总股本") \
                      or global_val(lines, ["总股本", "股本", "股份总数"], skip_keywords=["转增", "变动"], min_val=MV)
    D["流动资产"]   = global_val(lines, ["流动资产合计"], min_val=MV)
    D["流动负债"]   = global_val(lines, ["流动负债合计"], min_val=MV)
    D["少数股东权益"] = global_val(lines, ["少数股东权益"], skip_keywords=["影响额"], min_val=MV)

    # 每股收益：在关键词行及相邻行用正则找第一个带小数的数字（跳过编号/跨行）
    eps_line = find_line(lines, "基本每股收益")
    if eps_line == -1:
        eps_line = find_line(lines, "每股收益")
    D["基本每股收益"] = None
    if eps_line != -1:
        for j in (eps_line, eps_line + 1, eps_line - 1, eps_line + 2, eps_line - 2):
            if 0 <= j < len(lines):
                m = re.search(r"[-]?[0-9]+\.[0-9]+", lines[j])
                if m:
                    D["基本每股收益"] = float(m.group())
                    break
    D["净利润"] = D["归母净利润"]

    D["营收同比%"] = zone_pct(lines, zone, ["营业收入"])
    D["净利同比%"] = zone_pct(lines, zone, ["归属于上市公司股东", "归属于母公司股东", "归属于本行股东"])

    if unit != 1:
        for k in ["营业收入", "营业成本", "营业利润", "利润总额", "归母净利润", "扣非净利润",
                  "总资产", "总负债", "归母净资产", "少数股东权益", "流动资产", "流动负债",
                  "经营现金流净额", "净利润", "总股本"]:
            if D.get(k) is not None:
                D[k] = D[k] * unit

    # 错误值校验：宁缺毋错
    rev = D["营业收入"]
    if D["营业成本"] and rev and D["营业成本"] >= rev:
        D["营业成本"] = None
    for k in ["营业利润", "利润总额"]:
        v = D.get(k)
        if v is not None and rev:
            if not (0.001 * rev < v < rev):
                D[k] = None

    rev, cost = D["营业收入"], D["营业成本"]
    net, eq = D["净利润"], D["归母净资产"]
    ta, tl = D["总资产"], D["总负债"]
    ca, cl = D["流动资产"], D["流动负债"]
    D["毛利率%"]     = (rev - cost) / rev * 100 if rev and cost else None
    D["净利率%"]     = net / rev * 100 if rev and net else None
    D["ROE%"]        = net / eq * 100 if net and eq else None
    D["资产负债率%"] = tl / ta * 100 if tl and ta else None
    D["流动比率"]    = ca / cl if ca and cl else None

    checks = []
    if ta and tl and eq:
        total_eq = eq + (D["少数股东权益"] or 0)
        diff = abs(ta - (tl + total_eq)) / ta * 100
        checks.append(("总资产 ≈ 负债 + 权益（含少数股东）", diff, "ok" if diff < 1 else "warn"))
    if D["毛利率%"] is not None:
        g = D["毛利率%"]
        checks.append(("毛利率合理区间 0-100%", g, "ok" if 0 <= g <= 100 else "err"))
    if D["资产负债率%"] is not None:
        d = D["资产负债率%"]
        checks.append(("资产负债率合理区间 0-100%", d, "ok" if 0 <= d <= 100 else "err"))

    return D, checks

# ================= 台阶 4.7：自定义关键词全文搜索 =================
def search_keyword(file_bytes, keyword, max_results=15):
    """在年报全文中搜索任意指标关键词。
    返回 (results, suggestions)：
      results    命中列表，每项含 line(行号)、text(原文)、nums(该行全部数字)、ctx_before(上一行)
      suggestions 无精确命中时的相似表述候选
    注意：自定义指标单位无法统一，数值请以年报原表单位为准。
    """
    import pdfplumber
    import io
    keyword = (keyword or "").strip()
    if not keyword:
        return [], []

    # 兼容 bytes 与文件对象两种输入
    if isinstance(file_bytes, (bytes, bytearray)):
        file_bytes = io.BytesIO(file_bytes)
    with pdfplumber.open(file_bytes) as pdf:
        pages_text = [p.extract_text() or "" for p in pdf.pages]
    text = "\n".join(pages_text)
    if any(ord(ch) > 0x4E00 and ch in "營業歸屬資產負債額萬億元淨損營經現金流量" for ch in text[:5000]):
        text = _to_simplified(text)
    lines = text.split("\n")

    def _noise(ln):
        """干扰行：目录、太短、单位标注、纯表头"""
        if _is_toc_line(ln):
            return True
        if len(ln) < 4:
            return True
        if re.search(r"单位[:：]?.*(元|万元|千元|百万元)", ln):
            return True
        return False

    results = []
    for i, ln in enumerate(lines):
        if keyword in ln and not _noise(ln):
            n = nums(ln)
            # 表头/叙述行判断：无数值；或关键词重复出现（列标题，如"利息收入/平均收益率/利息收入"）
            head_like = (not n) and (ln.count(keyword) >= 2 or "/" in ln)
            results.append({
                "line": i + 1,
                "text": ln.strip(),
                "nums": n,
                "has_num": len(n) > 0,
                "head_like": head_like,
                "ctx_before": lines[i - 1].strip() if i > 0 else "",
            })
            if len(results) >= max_results:
                break

    # 通用性优化：有数值的数据行排前面，表头/叙述行排后面（稳定排序，保持原文顺序）
    results.sort(key=lambda x: (x["head_like"] or not x["has_num"]))

    # 无精确命中 → 相似候选：统计每行命中关键词字符的个数
    suggestions = []
    if not results:
        key_chars = set(keyword)
        min_hit = max(2, int(len(key_chars) * 0.6))
        scored = {}
        for ln in lines:
            if _noise(ln):
                continue
            hit = sum(1 for ch in key_chars if ch in ln)
            if hit >= min_hit:
                scored.setdefault(ln.strip(), hit)
        for t in sorted(scored, key=lambda x: -scored[x])[:8]:
            suggestions.append(t)
    return results, suggestions

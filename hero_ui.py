# -*- coding: utf-8 -*-
"""
AI 财报分析工具 —— Apogee 深色玻璃拟态 Hero 首屏（Streamlit 注入版）
设计规范来源：用户提供的《网页美化prompt.md》（Apogee Hero Section）
实现方式：单文件 HTML + CSS + JS，经 st.markdown(unsafe_allow_html=True) 注入。
说明：所有 CSS 选择器都加了 .apogee-hero 前缀做样式隔离，避免污染 Streamlit 其余组件；
      keyframes 动画名加了 apo- 前缀防冲突；数值（px/hex/延迟/缓动）按规范保留。
"""
import re
import streamlit as st

_BAR_HEIGHTS = [23, 40, 53, 40, 33, 14, 7, 17, 75, 65, 88, 75, 65, 47, 33, 88,
                4, 7, 9, 14, 95, 65, 79, 37, 7, 40, 17, 20, 62, 47, 92, 72]

_VIDEO_SRC = ("https://d8j0ntlcm91z4.cloudfront.net/"
              "user_38xzZboKViGWJOttwIXH07lWA1P/"
              "hf_20260813_092641_de52eb87-daf2-41db-92cb-7a56eae012a5.mp4")


def _build_bars():
    mh = max(_BAR_HEIGHTS)
    parts = []
    for i, h in enumerate(_BAR_HEIGHTS):
        pct = round(h / mh * 100, 4)
        color = "rgba(255,255,255,0.1)" if i >= 28 else "#ffffff"
        delay = 1100 + i * 30
        parts.append(
            f'<div class="apo-bar" style="height:{pct}%;background:{color};'
            f'animation-delay:{delay}ms;"></div>'
        )
    return "\n".join(parts)


_HERO_CSS = """
.apogee-hero, .apogee-hero *, .apogee-hero *::before, .apogee-hero *::after {margin:0;padding:0;box-sizing:border-box;}
.apogee-hero{container-type:inline-size;position:relative;width:100%;min-height:100vh;overflow:hidden;background:#080A19;color:#fff;isolation:isolate;font-family:'Suisse Intl',-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;}
.apogee-hero a{color:inherit;text-decoration:none;}
html{scroll-behavior:smooth;}
.apo-hero-video{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:0;}

@keyframes apo-fade-up{from{opacity:0;transform:translateY(24px);}to{opacity:1;transform:translateY(0);}}
@keyframes apo-fade-down{from{opacity:0;transform:translateY(-16px);}to{opacity:1;transform:translateY(0);}}
@keyframes apo-fade-left{from{opacity:0;transform:translateX(-20px);}to{opacity:1;transform:translateX(0);}}
@keyframes apo-fade-right{from{opacity:0;transform:translateX(20px);}to{opacity:1;transform:translateX(0);}}
@keyframes apo-fade-scale{from{opacity:0;transform:scale(.92);}to{opacity:1;transform:scale(1);}}
@keyframes apo-bar-grow{from{transform:scaleY(0);opacity:0;}to{transform:scaleY(1);opacity:1;}}
.apo-anim{opacity:0;}
.apo-fd0{animation:apo-fade-down .7s cubic-bezier(.16,1,.3,1) 0ms forwards;}
.apo-fd100{animation:apo-fade-down .7s cubic-bezier(.16,1,.3,1) 100ms forwards;}
.apo-fd200{animation:apo-fade-down .7s cubic-bezier(.16,1,.3,1) 200ms forwards;}
.apo-fu300{animation:apo-fade-up .8s cubic-bezier(.16,1,.3,1) 300ms forwards;}
.apo-fu500{animation:apo-fade-up .8s cubic-bezier(.16,1,.3,1) 500ms forwards;}
.apo-fu700{animation:apo-fade-up .8s cubic-bezier(.16,1,.3,1) 700ms forwards;}
.apo-fs900{animation:apo-fade-scale .9s cubic-bezier(.16,1,.3,1) 900ms forwards;}

.apo-inner{position:relative;z-index:10;display:flex;flex-direction:column;width:100%;min-height:100vh;max-width:1800px;margin:0 auto;}
.apo-nav{position:relative;z-index:50;display:flex;align-items:center;justify-content:space-between;width:100%;padding:20px 20px 0;}
@container (min-width:640px){.apo-nav{padding:30px 32px 0;}}
@container (min-width:768px){.apo-nav{padding:30px 82px 0;}}

.apo-logo{display:flex;align-items:center;gap:10px;}
.apo-logo svg{width:28px;height:28px;flex:none;}
.apo-logo-text{color:#fff;font-size:22px;font-weight:450;line-height:1;letter-spacing:-0.02em;white-space:nowrap;}
@container (min-width:640px){.apo-logo svg{width:32px;height:32px;}.apo-logo-text{font-size:26px;}}

.apo-nav-mid{display:none;align-items:center;gap:30px;height:52px;padding:0 24px;background:rgba(10,7,7,.35);border-radius:11px;backdrop-filter:blur(17px);-webkit-backdrop-filter:blur(17px);}
.apo-nav-mid a{display:flex;align-items:center;gap:5px;color:rgba(255,255,255,.8);font-size:14px;font-weight:450;line-height:14px;white-space:nowrap;transition:color .2s;}
.apo-nav-mid a:hover{color:#fff;}
.apo-nav-mid svg{width:10px;height:10px;opacity:.8;}
@container (min-width:1024px){.apo-nav-mid{display:flex;position:absolute;left:50%;translate:-50% 0;}}

.apo-nav-right{display:none;align-items:center;gap:5px;height:52px;padding:3px;background:rgba(0,0,0,.35);border-radius:13px;backdrop-filter:blur(17px);-webkit-backdrop-filter:blur(17px);}
.apo-nav-right a{display:flex;align-items:center;justify-content:center;height:46px;padding:0 24px;border-radius:11px;white-space:nowrap;font-size:14px;font-weight:450;line-height:14px;transition:background .2s;}
.apo-btn-login{color:#fff;}
.apo-btn-login:hover{background:rgba(255,255,255,.05);}
.apo-btn-light{background:#E9E9E9;color:#0A0707;}
.apo-btn-light:hover{background:#fff;}
@container (min-width:1024px){.apo-nav-right{display:flex;}}

.apo-burger{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:11px;background:rgba(10,7,7,.35);backdrop-filter:blur(17px);-webkit-backdrop-filter:blur(17px);cursor:pointer;border:0;transition:background .2s;color:#fff;text-decoration:none;user-select:none;-webkit-user-select:none;}
.apo-burger:hover{background:rgba(255,255,255,.1);}
.apo-ic{position:relative;width:20px;height:20px;}
.apo-ic svg{position:absolute;inset:0;margin:auto;transition:opacity .3s ease-out,transform .3s ease-out;}
.apo-ic-x{opacity:0;transform:rotate(-90deg) scale(.75);}
.apogee-hero:has(.apo-overlay:target) .apo-ic-menu{opacity:0;transform:rotate(90deg) scale(.75);}
.apogee-hero:has(.apo-overlay:target) .apo-ic-x{opacity:1;transform:rotate(0) scale(1);}
@container (min-width:1024px){.apo-burger{display:none;}}

.apo-hero-body{flex:1;display:flex;align-items:center;padding:32px 0;}
.apo-hero-row{display:flex;flex-direction:column;align-items:center;gap:40px;width:100%;max-width:1800px;margin:0 auto;padding:0 20px;}
@container (min-width:640px){.apo-hero-row{padding:0 32px;}}
@container (min-width:768px){.apo-hero-row{padding:0 82px;}}
@container (min-width:1024px){.apo-hero-row{flex-direction:row;align-items:center;justify-content:center;gap:48px;}}

.apo-copy{width:100%;max-width:780px;margin:0 auto;text-align:center;}
.apo-copy h1{color:#fff;font-size:36px;font-weight:400;line-height:.95;margin-bottom:20px;}
.apogee-hero h1{color:#fff !important;font-weight:400 !important;}
.apo-copy .apo-sub{color:rgba(255,255,255,.8);font-size:16px;font-weight:450;line-height:1.3;max-width:520px;margin:0 auto 28px;}
.apo-cta{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;}
.apo-cta a{display:flex;align-items:center;justify-content:center;height:46px;padding:0 20px;border-radius:12px;font-size:14px;font-weight:450;line-height:15.5px;white-space:nowrap;transition:opacity .2s;}
.apo-cta .apo-cta-primary{background:#E9E9E9;color:#0A0707;}
.apo-cta .apo-cta-primary:hover{opacity:.9;}
.apo-cta .apo-cta-ghost{border:1px solid #fff;color:#fff;}
.apo-cta .apo-cta-ghost:hover{opacity:.8;}
@container (min-width:640px){
  .apo-copy h1{font-size:52px;margin-bottom:32px;}
  .apo-copy .apo-sub{font-size:18px;margin-bottom:40px;}
  .apo-cta{gap:16px;}
  .apo-cta a{height:51px;padding:0 27px;font-size:15.5px;}
}
@container (min-width:768px){.apo-copy h1{font-size:64px;}}
@container (min-width:1024px){.apo-copy h1{font-size:72px;}}

.apo-card-label{color:#fff;font-size:16px;font-weight:450;line-height:20px;margin-bottom:12px;}
@container (min-width:640px){.apo-card-label{font-size:20px;margin-bottom:16px;}}
.apo-amount{display:flex;align-items:baseline;margin-bottom:8px;}
.apo-amount .apo-amt-main{color:#fff;font-size:28px;font-weight:450;line-height:1;}
.apo-amount .apo-amt-dim{color:rgba(255,255,255,.2);font-size:28px;font-weight:450;line-height:1;}
@container (min-width:640px){.apo-amount{margin-bottom:12px;}.apo-amount span{font-size:46px;}}
.apo-growth{display:flex;align-items:center;gap:10px;margin-bottom:24px;}
@container (min-width:640px){.apo-growth{margin-bottom:32px;}}
.apo-badge{background:rgba(255,255,255,.2);border-radius:6px;padding:7px 6px;color:#fff;font-size:12px;font-weight:450;line-height:14px;white-space:nowrap;}
.apo-growth-note{color:rgba(255,255,255,.8);font-size:12px;font-weight:450;line-height:14px;opacity:.7;white-space:nowrap;}
@container (min-width:640px){.apo-badge{font-size:14px;}.apo-growth-note{font-size:14px;}}
.apo-chart{position:relative;}
.apo-bars{display:flex;align-items:flex-end;gap:1.5px;height:80px;}
@container (min-width:640px){.apo-bars{height:100px;}}
.apo-bar{flex:1 1 0;min-width:0;border-radius:.5px;opacity:0;transform:scaleY(0);transform-origin:bottom;animation:apo-bar-grow .6s cubic-bezier(.16,1,.3,1) forwards;}
.apo-grid{position:absolute;inset:0;pointer-events:none;}
.apo-grid i{position:absolute;top:0;bottom:0;width:1px;background:rgba(255,255,255,.1);}
.apo-axis{display:flex;justify-content:space-between;margin-top:12px;color:rgba(255,255,255,.8);font-size:9px;font-weight:450;line-height:10px;}
@container (min-width:640px){.apo-axis{font-size:10px;}}
.apo-axis span:nth-child(n+4){opacity:.4;}

.apo-overlay{position:fixed;inset:0;z-index:40;visibility:hidden;opacity:0;transition:opacity .4s ease,visibility 0s linear .4s;}
.apo-overlay:target{visibility:visible;opacity:1;transition:opacity .4s ease,visibility 0s linear 0s;}
.apo-overlay-bg{position:absolute;inset:0;display:block;background:rgba(8,10,25,.9);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);opacity:0;transition:opacity .5s ease;}
.apo-overlay:target .apo-overlay-bg{opacity:1;}
.apo-panel{position:absolute;top:76px;left:16px;right:16px;background:rgba(17,16,15,.6);backdrop-filter:blur(30px);-webkit-backdrop-filter:blur(30px);border-radius:20px;border:1px solid rgba(255,255,255,.06);padding:24px;opacity:0;transform:translateY(-16px) scale(.97);transition:opacity .5s cubic-bezier(.32,.72,0,1),transform .5s cubic-bezier(.32,.72,0,1);}
@container (min-width:640px){.apo-panel{top:86px;left:24px;right:24px;padding:32px;}}
.apo-overlay:target .apo-panel{opacity:1;transform:none;}
.apo-plinks{display:flex;flex-direction:column;gap:4px;}
.apo-mlink{display:flex;align-items:center;justify-content:space-between;padding:16px;border-radius:12px;color:rgba(255,255,255,.9);font-size:18px;font-weight:450;opacity:0;transform:translateX(-12px);transition:opacity .3s ease,transform .3s ease;}
.apo-mlink:hover{background:rgba(255,255,255,.06);}
.apo-overlay:target .apo-mlink{opacity:1;transform:none;}
.apo-overlay:target .apo-mlink:nth-child(1){transition-delay:.10s;}
.apo-overlay:target .apo-mlink:nth-child(2){transition-delay:.15s;}
.apo-overlay:target .apo-mlink:nth-child(3){transition-delay:.20s;}
.apo-overlay:target .apo-mlink:nth-child(4){transition-delay:.25s;}
.apo-divider{height:1px;background:rgba(255,255,255,.1);margin:20px 0;}
.apo-pctas{display:flex;flex-direction:column;gap:12px;}
.apo-pctas a{display:flex;align-items:center;justify-content:center;height:50px;border-radius:12px;font-size:15px;font-weight:450;opacity:0;transform:translateY(8px);transition:opacity .5s ease,transform .5s ease,background .2s;}
.apo-overlay:target .apo-pctas a{opacity:1;transform:none;}
.apo-overlay:target .apo-pctas a:nth-child(1){transition-delay:.35s;}
.apo-overlay:target .apo-pctas a:nth-child(2){transition-delay:.40s;}
.apo-btn-panel-light{background:#E9E9E9;color:#0A0707;}
.apo-btn-panel-light:hover{background:#fff;}
.apo-btn-panel-ghost{border:1px solid rgba(255,255,255,.3);color:#fff;}
.apo-btn-panel-ghost:hover{background:rgba(255,255,255,.05);}
"""

_LOGO_PATH = ("M 256 256 L 178 256 C 150.386 256 128 233.614 128 206 L 128 256 L 0 256 L 0 192 C 0 156.654 28.654 128 64 128 "
              "C 99.346 128 128 156.654 128 192 L 128 128 L 256 128 Z M 78 0 C 105.614 0 128 22.386 128 50 L 128 0 L 256 0 "
              "L 256 64 C 256 99.346 227.346 128 192 128 C 156.654 128 128 99.346 128 64 L 128 128 L 0 128 L 0 0 Z")

_CHEVRON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
            'stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>')

_MENU_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
              '<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>')

_X_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">'
           '<line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>')

_OPEN_JS = ("document.getElementById('apo-menu').classList.add('apo-open');"
             "document.getElementById('apo-burger').classList.add('apo-open');"
             "document.body.style.overflow='hidden';")

_CLOSE_JS = ("document.getElementById('apo-menu').classList.remove('apo-open');"
              "document.getElementById('apo-burger').classList.remove('apo-open');"
              "document.body.style.overflow='';")

_HERO_BODY = """
<div class="apogee-hero" id="apogee-hero">
  <video class="apo-hero-video" src="{video}" autoplay loop muted playsinline></video>
  <div class="apo-inner">
    <nav class="apo-nav">
      <div class="apo-logo apo-anim apo-fd0">
        <svg viewBox="0 0 256 256" fill="none" aria-hidden="true"><path d="{logo}" fill="#FFFFFF"/></svg>
        <span class="apo-logo-text">AI 财报分析</span>
      </div>
      <div class="apo-nav-mid apo-anim apo-fd100">
        <a href="#upload-anchor">功能介绍 {chevron}</a>
        <a href="#usage">使用指南</a>
      </div>
      <a class="apo-burger apo-anim apo-fd100" id="apo-burger" href="#apo-menu" aria-label="菜单">
        <span class="apo-ic"><span class="apo-ic-menu">{menu}</span><span class="apo-ic-x">{x}</span></span>
      </a>
    </nav>

    <div class="apo-hero-body">
      <div class="apo-hero-row">
        <div class="apo-copy">
          <h1 class="apo-anim apo-fu300">AI 驱动的财报分析，<br>洞察企业真实价值</h1>
          <p class="apo-sub apo-anim apo-fu500">上传年报 PDF，智能提取 20+ 核心财务指标，支持多公司横向对比与风险预警</p>
          <div class="apo-cta apo-anim apo-fu700">
            <a class="apo-cta-primary" href="#upload-anchor">上传年报开始分析</a>
            <a class="apo-cta-ghost" href="#usage">查看使用指南</a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="apo-overlay" id="apo-menu">
    <a class="apo-overlay-bg" id="apo-menu-bg" href="#" aria-label="关闭菜单"></a>
    <div class="apo-panel">
      <div class="apo-plinks">
        <a class="apo-mlink" href="#upload-anchor">功能介绍 {chevron}</a>
        <a class="apo-mlink" href="#usage">使用指南</a>
      </div>
      <div class="apo-divider"></div>
      <div class="apo-pctas">
        <a class="apo-btn-panel-light" href="#upload-anchor">上传年报开始分析</a>
        <a class="apo-btn-panel-ghost" href="#usage">查看使用指南</a>
      </div>
    </div>
  </div>
</div>

<script>
(function(){{
  var hero = document.getElementById('apogee-hero');
  if (!hero) return;
  var burger = document.getElementById('apo-burger');
  var overlay = document.getElementById('apo-menu');
  function setOpen(open){{
    overlay.classList.toggle('apo-open', open);
    burger.classList.toggle('apo-open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  }}
  burger.addEventListener('click', function(e){{
    e.preventDefault();
    e.stopPropagation();
    setOpen(!overlay.classList.contains('apo-open'));
  }});
  overlay.addEventListener('click', function(e){{
    if (e.target === overlay || e.target.classList.contains('apo-overlay-bg')) setOpen(false);
  }});
  overlay.querySelectorAll('a').forEach(function(a){{
    a.addEventListener('click', function(){{ setOpen(false); }});
  }});
}})();
</script>
"""


def render_hero():
    """在页面最顶部渲染 Apogee 深色 Hero 首屏。

    Streamlit 的 markdown 渲染器遵循 CommonMark：HTML 块遇到「空行」就会中断，
    中断后其余内容会被当成代码块/普通 markdown，导致大段 HTML 结构碎裂。
    因此这里把最终 HTML 压成「无空行 + 行首无缩进」的形态再交给 st.markdown，
    保证整段被当作一个连续 raw HTML 块透传。
    """
    html = "<link href='https://db.onlinewebfonts.com/c/13ab13418f633c1b0516fed6e30bedbc?family=Suisse+Int%27l' rel='stylesheet'>"
    html += "<style>" + _HERO_CSS + "</style>"
    html += _HERO_BODY.format(
        video=_VIDEO_SRC,
        logo=_LOGO_PATH,
        chevron=_CHEVRON,
        menu=_MENU_ICON,
        x=_X_ICON,
        bars=_build_bars(),
    )
    html = html.replace("__OPEN__", _OPEN_JS).replace("__CLOSE__", _CLOSE_JS)
    lines = [ln.strip() for ln in html.split("\n") if ln.strip()]
    html = "\n".join(lines)
    st.markdown(html, unsafe_allow_html=True)

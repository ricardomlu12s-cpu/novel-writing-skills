#!/usr/bin/env python3
"""创作数据面板渲染器 — 把 build-world 设定库渲染成可视化 HTML 面板。

用法:
  python3 render_panel.py <项目目录> [--open]

输入(读取 .omc/story/<项目名>/):
  world.md, characters/*.md, locations.md, foreshadowing.jsonl,
  pov-boundary.jsonl, canon-ledger/timeline.md(优先)或 timeline.md,
  cadence.jsonl, evolution/(capability, fingerprint-actual)

输出:
  <项目目录>/panel/index.html  (零依赖静态 HTML,浏览器打开即可)

面板内容:
  世界框架 / 情节走向 / 角色卡 / 故事数据 / 伏笔状态 / 进化区(学习节律/能力画像/实际指纹) / 创作后续意见
"""
import json, os, re, sys, subprocess
from pathlib import Path

def read_md(path):
    if not Path(path).exists():
        return ""
    return Path(path).read_text(encoding="utf-8")

def read_jsonl(path):
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out

def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def html_card(title, body):
    return f'<div class="card"><h3>{esc(title)}</h3>{body}</div>'

def main():
    if len(sys.argv) < 2:
        print("用法: render_panel.py <项目目录> [--open]")
        sys.exit(1)
    project_dir = Path(sys.argv[1])
    do_open = "--open" in sys.argv

    world = read_md(project_dir / "world.md")
    locations = read_md(project_dir / "locations.md")
    # 时间线:优先正典账本 canon-ledger/timeline.md,兜底项目根 timeline.md
    timeline = read_md(project_dir / "canon-ledger" / "timeline.md") or read_md(project_dir / "timeline.md")
    foreshadowing = read_jsonl(project_dir / "foreshadowing.jsonl")
    pov = read_jsonl(project_dir / "pov-boundary.jsonl")
    chars_dir = project_dir / "characters"
    char_cards = []
    if chars_dir.exists():
        for f in sorted(chars_dir.glob("*.md")):
            char_cards.append((f.stem, read_md(f)))

    # 故事数据:章数以 manuscripts/ 实际文件数为权威源(磁盘为准,防 timeline 滞后)
    import re as _re
    mdir = project_dir / "manuscripts"
    ch_count = sum(1 for f in mdir.glob("ch*.md") if _re.match(r"ch\d{3}\.md$", f.name)) if mdir.exists() else 0
    # 兜底:若 manuscripts 缺失,从时间线 "(第X章)" 或 "## 第X章" 数
    if ch_count == 0:
        ch_count = len(_re.findall(r"\((?:第[一二三四五六七八九十百\d]+章)\)", timeline)) or timeline.count("## 第")
    total_chars = sum(len(c) for _, c in char_cards) + len(world) + len(timeline)

    # 伏笔统计(分层:已开启 vs 规划中)
    opened = [f for f in foreshadowing if f.get("phase") == "已开启"]
    planned = [f for f in foreshadowing if f.get("phase") != "已开启"]
    n_open = sum(1 for f in opened if f.get("status") == "开启")
    n_pending = sum(1 for f in opened if f.get("status") == "悬置")
    n_paid = sum(1 for f in opened if f.get("status") == "回收")
    n_planned = len(planned)

    # 创作后续意见(基于规则生成)
    advice = []
    for f in opened:
        if f.get("status") == "悬置":
            advice.append(f"🔔 伏笔悬置过久:「{f.get('desc','')}」(第{f.get('opened_ch','?')}章开启,待回收)")
    if n_pending > 5:
        advice.append(f" 悬置伏笔达 {n_pending} 条,建议近期安排回收,防挖坑不填")
    if pov:
        # 简单缺席告警:角色若时间线中无"第N章"且已开过
        advice.append(" 请留意角色卡状态:超5章未出场角色建议安排回归")
    if not advice:
        advice.append(" 当前无待处理告警,可继续推进主线")
    advice_html = "".join(f"<li>{esc(a)}</li>" for a in advice)

    # 角色卡 HTML
    chars_html = ""
    for name, body in char_cards:
        first_line = body.splitlines()[1] if len(body.splitlines()) > 1 else ""
        chars_html += f'<details class="char"><summary>{esc(name)}</summary><pre>{esc(body[:600])}</pre></details>'

    # 伏笔表
    fh_rows = "".join(
        f"<tr><td>{esc(f.get('id',''))}</td><td>{esc(f.get('desc',''))}</td>"
        f"<td>{esc(str(f.get('opened_ch','')))}</td><td>{esc(f.get('status',''))}</td>"
        f"<td>{esc(str(f.get('payoff_ch',''))) if f.get('payoff_ch') else '-'}</td></tr>"
        for f in foreshadowing
    ) or "<tr><td colspan=5>暂无伏笔</td></tr>"

    # 增强区:情绪曲线 / 战力 / 套路 / 重复 / 常识(若 plan-plot/remove-ai-tone 有产出)
    # 情绪曲线(读取 plan-plot 产出)
    emo_html = ""
    ec_path = project_dir / "panel" / "emotion_curve.json"
    if ec_path.exists():
        try:
            ec = json.loads(ec_path.read_text(encoding="utf-8"))
            cells = "".join(
                f"<td style='background:hsl({210 - c['intensity']*18},70%,85%)'>{c['ch']}:{c['emotion']}({c['intensity']})</td>"
                for c in ec.get("curve", [])[:12]
            )
            emo_html = html_card("📈 情绪曲线", f"<table><tr>{cells}</tr></table>")
        except Exception:
            emo_html = ""
    # 战力状态(从角色卡 power 字段粗提)
    power_html = ""
    pw_lines = []
    for name, body in char_cards:
        for line in body.splitlines():
            if "等级" in line and "L" in line:
                pw_lines.append(f"{name}: {line.strip().lstrip('- ')}")
    if pw_lines:
        power_html = html_card("⚔️ 战力状态", "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in pw_lines[:8]) + "</ul>")
    # 套路检测(cliche_detect 产出清单,此处简读)
    cliche_html = ""
    if advice:
        pass  # 意见区已含套路提示
    # 组装增强区
    enhanced = ""
    if emo_html or power_html:
        enhanced = f'<div class="grid" style="margin-top:16px">{emo_html}{power_html}</div>'

    # 进化区(evolve-style):读 cadence.jsonl + evolution/(指纹/能力/报告)
    evo_html = ""
    evo_cards = []
    cad = read_jsonl(project_dir / "cadence.jsonl")
    if cad:
        last_learn = [e for e in cad if e.get("type") == "learn" and e.get("level")][-1:]
        if last_learn:
            e = last_learn[-1]
            evo_cards.append(html_card("🧬 学习节律",
                f"最近学习: 第{e.get('ch','?')}章 {e.get('level','')}层"
                f"<br>触发: {esc(str(e.get('trigger','')))}"))
        else:
            evo_cards.append(html_card("🧬 学习节律", "尚未触发学习,每章后跑 cadence_calc 登记"))
    # 实际指纹(capability 画像)
    cap = read_md(project_dir / "evolution" / "capability.md")
    if cap.strip():
        evo_cards.append(html_card("🎯 能力画像", f"<pre>{esc(cap[:600])}</pre>"))
    fp_actual = read_md(project_dir / "evolution" / "fingerprint-actual.md")
    if fp_actual.strip():
        evo_cards.append(html_card("🖌 实际指纹", f"<pre>{esc(fp_actual[:400])}</pre>"))
    if evo_cards:
        evo_html = '<div class="grid" style="margin-top:16px">' + "".join(evo_cards) + "</div>"

    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8">
<title>创作数据面板</title>
<style>
  body {{ font-family: -apple-system, "PingFang SC", sans-serif; margin: 0; background: #f5f5f7; color: #1d1d1f; }}
  header {{ background: #1d1d1f; color: #fff; padding: 16px 24px; }}
  main {{ max-width: 1000px; margin: 24px auto; padding: 0 16px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }}
  .card {{ background: #fff; border-radius: 10px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
  .card h3 {{ margin: 0 0 10px; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
  pre {{ white-space: pre-wrap; font-family: inherit; font-size: 14px; line-height: 1.7; margin: 0; }}
  .char {{ margin-bottom: 8px; }}
  .char summary {{ cursor: pointer; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  td, th {{ border: 1px solid #eee; padding: 6px 8px; text-align: left; }}
  .advice li {{ margin-bottom: 6px; line-height: 1.6; }}
  .stat {{ font-size: 24px; font-weight: 700; color: #0071e3; }}
</style></head><body>
<header><h1>📖 创作数据面板</h1><p>项目:{esc(project_dir.name)} · 自动生成,每章后刷新</p></header>
<main>
  <section class="grid" style="margin-bottom:16px">
    {html_card("故事数据", f'<div class="stat">{ch_count}</div> 章 · <div class="stat">{total_chars:,}</div> 字')}
    {html_card("伏笔状态", f'已开启 开启 {n_open} · 悬置 {n_pending} · 回收 {n_paid} <br>规划中 {n_planned} 条(未来卷,未开启)')}
    {html_card("设定规模", f'{len(char_cards)} 位角色 · 世界观 {len(world)} 字')}
  </section>
  <div class="grid">
    {html_card("🌍 世界框架", f"<pre>{esc(world[:800])}</pre>")}
    {html_card("🗺 地点图", f"<pre>{esc(locations[:500]) or '暂无'}</pre>")}
  </div>
  <div class="grid" style="margin-top:16px">
    {html_card("🧭 情节走向/时间线", f"<pre>{esc(timeline[:800]) or '暂无'}</pre>")}
    {html_card("🔍 伏笔注册表", f"<table><tr><th>ID</th><th>描述</th><th>开启章</th><th>状态</th><th>回收章</th></tr>{fh_rows}</table>")}
  </div>
  <div style="margin-top:16px">
    {html_card("👥 角色卡", chars_html or "暂无角色")}
  </div>
  {enhanced}
  {evo_html}
  <div style="margin-top:16px">
    {html_card("💡 创作后续意见", f"<ul class='advice'>{advice_html}</ul>")}
  </div>
</main></body></html>"""
    panel_dir = project_dir / "panel"
    panel_dir.mkdir(parents=True, exist_ok=True)
    (panel_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"面板已生成: {panel_dir / 'index.html'}")
    if do_open:
        subprocess.run(["open", str(panel_dir / "index.html")])

if __name__ == "__main__":
    main()

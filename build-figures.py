"""Render article figures with matplotlib; no generative imagery or network required.

python build-figures.py --refresh-metrics --metrics-root PATH
python build-figures.py                     # use the portable metrics snapshot
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
DATA = ASSETS / "data" / "metrics.json"
INK = "#20313F"
MUTED = "#61717B"
BLUE = "#27649A"
GREEN = "#237C68"
ORANGE = "#B96838"
PURPLE = "#736198"
BG = "#FCFCF9"


def setup_fonts():
    for candidate in [Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/simhei.ttf")]:
        if candidate.exists():
            font_manager.fontManager.addfont(str(candidate))
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(candidate)).get_name()
            break
    else:
        plt.rcParams["font.family"] = ["Noto Sans CJK SC", "Source Han Sans SC", "sans-serif"]
    plt.rcParams.update({
        "axes.unicode_minus": False,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "svg.fonttype": "path",
        "font.size": 14,
    })


def refresh_metrics(root):
    inputs = [("baseline", "无Skill", "token_noskill.jsonl", 88.84),
              ("old", "旧版Skill", "token_metrics.jsonl", 93.68),
              ("new", "新版Skill", "token_newskill.jsonl", 94.03)]
    groups, rows_by_key = [], {}
    for key, label, filename, score in inputs:
        rows = [json.loads(line) for line in (root / filename).read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        ids = [r["external_id"] for r in rows]
        assert len(rows) == len(set(ids)) == 140, f"Unexpected/duplicate tasks in {filename}"
        assert len({r["repo"] for r in rows}) == 7
        assert all(r["session_total_tokens"] == r["session_total_input_tokens"] + r["session_total_output_tokens"] for r in rows)
        rows_by_key[key] = {r["external_id"]: r for r in rows}
        total_tokens = sum(r["session_total_tokens"] for r in rows)
        total_seconds = sum(r["duration_seconds"] for r in rows)
        groups.append({"key": key, "label": label, "tasks": len(rows),
                       "quality_score": score, "total_tokens": total_tokens,
                       "total_input_tokens": sum(r["session_total_input_tokens"] for r in rows),
                       "total_output_tokens": sum(r["session_total_output_tokens"] for r in rows),
                       "mean_tokens": total_tokens / len(rows),
                       "total_seconds": total_seconds,
                       "mean_minutes": total_seconds / len(rows) / 60,
                       "models": sorted({r["model_id"] for r in rows})})
    assert set(rows_by_key["baseline"]) == set(rows_by_key["old"]) == set(rows_by_key["new"])
    assert groups[0]["models"] == groups[1]["models"] == groups[2]["models"]
    old, new = rows_by_key["old"], rows_by_key["new"]
    metrics = {
        "groups": groups,
        "paired": {
            "token_decreased": sum(new[k]["session_total_tokens"] < old[k]["session_total_tokens"] for k in old),
            "duration_decreased": sum(new[k]["duration_seconds"] < old[k]["duration_seconds"] for k in old),
            "token_increased": sum(new[k]["session_total_tokens"] > old[k]["session_total_tokens"] for k in old),
            "duration_increased": sum(new[k]["duration_seconds"] > old[k]["duration_seconds"] for k in old),
            "input_share_of_token_savings_percent": (groups[1]["total_input_tokens"] - groups[2]["total_input_tokens"]) / (groups[1]["total_tokens"] - groups[2]["total_tokens"]) * 100,
            "token_reduction_percent": (1 - groups[2]["total_tokens"] / groups[1]["total_tokens"]) * 100,
            "duration_reduction_percent": (1 - groups[2]["total_seconds"] / groups[1]["total_seconds"]) * 100,
        },
        "notes": [
            "质量评分沿用既有报告汇总，逐任务原始记录中的score为空。",
            "开销按session_total_tokens和duration_seconds汇总，不使用末次调用total_tokens。",
            "三组各140个对应任务，使用相同模型标识，运行日期不同。",
            "Token不等于账单；平均任务耗时不等于批次墙钟时间；部分失败重试的完整开销不可确认。",
        ],
    }
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text(ax, x, y, value, size=16, color=INK, weight="normal", ha="left", va="center", **kwargs):
    return ax.text(x, y, value, fontsize=size, color=color, weight=weight,
                   ha=ha, va=va, linespacing=1.6, **kwargs)


def canvas(number, title, subtitle):
    fig = plt.figure(figsize=(16, 9), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 16), ylim=(0, 9))
    ax.axis("off")
    text(ax, .65, 8.48, f"{number:02d} / SKILL SELF-EVOLUTION", 12, GREEN, "bold")
    text(ax, .65, 7.93, title, 27, weight="bold")
    text(ax, .65, 7.35, subtitle, 14, MUTED)
    ax.plot([.65, 15.35], [6.96, 6.96], color="#D6DEDD", lw=1)
    return fig, ax


def card(ax, x, y, w, h, title, body, color=BLUE, fill="#F2F6F8", title_size=19):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.025,rounding_size=0.14",
                          facecolor=fill, edgecolor=color, linewidth=1.6)
    patch.set_sketch_params(scale=.3, length=150, randomness=2)
    ax.add_patch(patch)
    text(ax, x + .22, y + h - .43, title, title_size, color, "bold")
    text(ax, x + .22, y + h - .97, body, 15, va="top")


def arrow(ax, start, end, label, lx, ly, color=BLUE, dashed=False, connection="arc3,rad=0"):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=17,
                                color=color, linewidth=1.8, linestyle="--" if dashed else "-",
                                connectionstyle=connection))
    text(ax, lx, ly, label, 11.5, color, ha="center",
         bbox={"facecolor": BG, "edgecolor": "none", "pad": 2})


def routed_arrow(ax, points, label, lx, ly, color=BLUE, dashed=False):
    """Orthogonal route with an arrowhead on the final segment."""
    xs, ys = zip(*points[:-1])
    ax.plot(xs, ys, color=color, lw=1.8, linestyle="--" if dashed else "-")
    arrow(ax, points[-2], points[-1], label, lx, ly, color, dashed)


def footer(ax, sentence, detail=None):
    ax.plot([.65, 15.35], [.95, .95], color="#D6DEDD", lw=1)
    text(ax, .65, .58, sentence, 15, GREEN, "bold")
    if detail:
        text(ax, 15.35, .58, detail, 11, MUTED, ha="right")


def save(fig, stem):
    ASSETS.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "svg"]:
        output_path = ASSETS / f"{stem}.{extension}"
        fig.savefig(output_path, dpi=150, facecolor=BG)
        if extension == "svg":
            output_path.write_text("\n".join(line.rstrip() for line in output_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    plt.close(fig)


def capability_boundary():
    fig, ax = canvas(1, "按增量价值，重新分配Skill的职责", "按收益、成本与适用条件，调整模型和Skill各自承担的工作。")
    cards = [
        (.8, "通用分析指导", "任务拆解、计划、自我检查\n模型已能稳定完成时\n尝试减少固定步骤", BLUE, "#F0F5FA"),
        (5.7, "稳定的重复操作", "读取环境、构建、执行测试\n操作稳定且反复发生时\n整合为可检查的脚本", GREEN, "#F0F7F3"),
        (10.6, "当前事实与交付证据", "需求、源码、实际运行结果\n通过读取与执行获取\n相关条件变化后重新确认", ORANGE, "#FBF3EB"),
    ]
    for x, title, body, color, fill in cards:
        card(ax, x, 4.02, 4.6, 2.5, title, body, color, fill, 20)
    text(ax, 8, 3.55, "分析方法可以调整；交付要求由任务目标决定。", 18, INK, "bold", ha="center")
    text(ax, .8, 2.93, "对每条规则，同时检查三个条件", 14, GREEN, "bold")
    for x, title, body in [(.8, "收益", "改善结果，或减少失败与返工"),
                           (5.7, "成本", "推理、工具往返与维护投入"),
                           (10.6, "适用范围", "模型、任务、环境与退出条件")]:
        card(ax, x, 1.24, 4.6, 1.35, title, body, GREEN, "#F5F8F4", 17)
    footer(ax, "模型、任务或环境变化后，让原有规则重新接受对照检验。")
    save(fig, "01-model-skill-boundary")


def evolution_path():
    fig, ax = canvas(3, "精简之后，还要从失败里补回约束", "六阶段概括优化重心的变化；整体收益不能拆成各阶段的独立贡献。")
    nodes = [
        (.8, 4.7, "一 / 能力构建", "生成、验证、分析、修复\n让一次任务能够闭环", BLUE, "#F0F5FA"),
        (6.05, 4.7, "二 / 问题发现", "重复读取、加载与报告\n检查过程负担", ORANGE, "#FBF3EB"),
        (11.3, 4.7, "三 / 流程精简", "减少通用流程的重复指导\n压缩说明、产物与执行链", "#95722B", "#FAF7E9"),
        (11.3, 1.72, "四 / 脚本整合", "集中获取信息与执行验证\n保留结果与失败的可观察性", GREEN, "#F0F7F3"),
        (6.05, 1.72, "五 / 稳定性补强", "交付可运行、测试真执行\n验证结果与当前代码一致", BLUE, "#EFF5FB"),
        (.8, 1.72, "六 / 评测迭代", "比较质量与执行开销\n决定保留、调整或删除", PURPLE, "#F5F2FA"),
    ]
    for x, y, title, body, color, fill in nodes:
        card(ax, x, y, 3.9, 1.87, title, body, color, fill, 18)
    arrow(ax, (4.75, 5.65), (5.99, 5.65), "投入运行", 5.36, 5.93, BLUE)
    arrow(ax, (10.0, 5.65), (11.24, 5.65), "定位冗余", 10.63, 5.93, ORANGE)
    arrow(ax, (13.25, 4.65), (13.25, 3.64), "收敛操作", 14.15, 4.15, GREEN)
    arrow(ax, (11.24, 2.66), (10.0, 2.66), "继续补强", 10.63, 2.94, ORANGE)
    arrow(ax, (5.99, 2.66), (4.75, 2.66), "比较效果", 5.36, 2.94, BLUE)
    routed_arrow(ax, [(2.75, 3.65), (2.75, 4.08), (8.0, 4.08), (8.0, 4.65)], "新反馈触发下一轮问题定位", 5.3, 4.32, PURPLE, True)
    text(ax, .8, 1.26, "实线：本轮调整顺序；虚线：后续复评。失败反馈来自整个运行过程。", 12, MUTED)
    footer(ax, "整体结果评价修改组合；单项收益需要另设对照。")
    save(fig, "03-evolution-path")


def comparison(metrics):
    fig, ax = canvas(2, "整体评分相近，执行开销明显下降", "三组各140个对应任务，比较无Skill、旧版Skill与新版Skill的质量和开销。")
    groups = metrics["groups"]
    colors = ["#ADB9BF", ORANGE, GREEN]
    panels = [
        ("整体质量评分（报告值）", "quality_score", 1, (0, 105), [0, 25, 50, 75, 100], "分", lambda v: f"{v:.2f}"),
        ("累计会话Token", "total_tokens", 1e8, (0, 6.3), [0, 2, 4, 6], "亿", lambda v: f"{v:.3f}"),
        ("平均任务耗时", "mean_minutes", 1, (0, 42), [0, 10, 20, 30, 40], "分钟", lambda v: f"{v:.1f}"),
    ]
    for index, (title, key, divisor, limits, ticks, unit, fmt) in enumerate(panels):
        panel = fig.add_axes([.072 + index * .321, .275, .252, .425], facecolor=BG)
        values = [g[key] / divisor for g in groups]
        bars = panel.bar(range(3), values, width=.55, color=colors, zorder=3)
        panel.set_xticks(range(3), [g["label"] for g in groups], fontsize=12)
        panel.set_ylim(*limits)
        panel.set_yticks(ticks)
        panel.tick_params(axis="both", length=0, labelsize=11, pad=9)
        panel.set_title(title, loc="left", fontsize=18, pad=29, weight="bold", color=INK)
        panel.text(0, 1.025, unit, transform=panel.transAxes, fontsize=11, color=MUTED)
        panel.grid(axis="y", color="#E3E8E7", zorder=0)
        for spine in panel.spines.values():
            spine.set_visible(False)
        for bar, value in zip(bars, values):
            panel.text(bar.get_x() + bar.get_width() / 2, value + limits[1] * .026, fmt(value), ha="center", fontsize=15, weight="bold")
    paired = metrics["paired"]
    delta = groups[2]["quality_score"] - groups[1]["quality_score"]
    for x, value, label in [(3.17, f"{delta:+.2f}分", "旧版 → 新版 / 整体评分"),
                             (8.30, f"−{paired['token_reduction_percent']:.1f}%", "旧版 → 新版 / 累计Token"),
                             (13.44, f"−{paired['duration_reduction_percent']:.1f}%", "旧版 → 新版 / 平均耗时")]:
        text(ax, x, 1.81, value, 22, MUTED if x < 4 else GREEN, "bold", ha="center")
        text(ax, x, 1.34, label, 12, MUTED, ha="center")
    footer(ax, f"Token：{paired['token_decreased']}个下降、{paired['token_increased']}个上升；耗时：{paired['duration_decreased']}个缩短、{paired['duration_increased']}个增加。")
    text(ax, 15.33, .18, "Token不等于账单；平均任务耗时不等于批次墙钟时间。", 10, MUTED, ha="right")
    save(fig, "02-quality-cost-comparison")


def information_lifecycle():
    fig, ax = canvas(4, "把有效改动写回Skill", "模型升级后重新评测，让已有流程跟着模型能力一起调整。")
    for x, title, body in [(.8, "当前Skill", "当前规则与配套脚本\n作为本轮调整的起点"),
                           (6.05, "重新评测", "使用升级后的模型\n比较无Skill与当前Skill"),
                           (11.3, "分析运行记录", "哪些步骤已经可以省去\n哪些指导仍然需要保留")]:
        card(ax, x, 4.7, 3.9, 1.87, title, body, BLUE, "#F0F5FA", 19)
    for x, title, body in [(.8, "写回有效改动", "更新规则与配套脚本\n保留旧版、理由和评测结果"),
                           (6.05, "比较新旧版本", "在同一模型上执行同组任务\n检查质量、Token与耗时"),
                           (11.3, "修改Skill", "人工与模型协同调整\n精简步骤、整合脚本、补充要求")]:
        card(ax, x, 1.57, 3.9, 1.87, title, body, PURPLE, "#F5F2FA", 19)
    arrow(ax, (4.75, 5.65), (5.99, 5.65), "模型升级后", 5.36, 5.93, BLUE)
    arrow(ax, (10, 5.65), (11.24, 5.65), "检查执行过程", 10.63, 5.93, BLUE)
    arrow(ax, (13.25, 4.65), (13.25, 3.5), "根据问题调整", 14.15, 4.05, PURPLE)
    arrow(ax, (11.24, 2.5), (10, 2.5), "验证修改效果", 10.63, 2.8, PURPLE)
    arrow(ax, (5.99, 2.5), (4.75, 2.5), "保留有效改动", 5.36, 2.8, PURPLE)
    arrow(ax, (2.75, 3.5), (2.75, 4.65), "更新当前版本", 1.78, 4.05, GREEN)
    text(ax, 8.0, 4.32, "沿用原有交付要求", 17, ORANGE, "bold", ha="center")
    arrow(ax, (8, 4.04), (8, 3.5), "按相同标准检查", 9.25, 3.83, ORANGE)
    text(ax, .8, 1.18, "日常执行读取当前规则；修改Skill时查阅版本记录，出现问题时可以恢复旧版。", 12, MUTED)
    footer(ax, "模型继续进步，Skill继续调整：记录哪些经验要保留、哪些指导可以省去。")
    save(fig, "04-information-lifecycle")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-metrics", action="store_true")
    parser.add_argument("--metrics-root", type=Path, help="Directory containing the three token_*.jsonl files")
    args = parser.parse_args()
    if args.refresh_metrics:
        if args.metrics_root is None:
            parser.error("--refresh-metrics requires --metrics-root PATH")
        refresh_metrics(args.metrics_root)
    metrics = json.loads(DATA.read_text(encoding="utf-8"))
    setup_fonts()
    capability_boundary()
    evolution_path()
    comparison(metrics)
    information_lifecycle()
    print(json.dumps({"figures": 4, "formats": ["png", "svg"], "paired": metrics["paired"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

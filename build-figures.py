"""Render article figures with matplotlib; no generative imagery or network required.

python build-figures.py --refresh-metrics   # recompute from workspace inputs
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


def refresh_metrics():
    root = HERE.parent.parent
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
            "token_reduction_percent": (1 - groups[2]["total_tokens"] / groups[1]["total_tokens"]) * 100,
            "duration_reduction_percent": (1 - groups[2]["total_seconds"] / groups[1]["total_seconds"]) * 100,
        },
        "notes": [
            "质量分为既有整体评分，逐任务原始记录中的score为空；不得作显著性或逐任务质量判断。",
            "开销按session_total_tokens和duration_seconds汇总，不使用末次调用total_tokens。",
            "三组各140个对应任务；运行日期不同，同模型标识不代表所有实验条件完全固定。",
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


def footer(ax, sentence, detail=None):
    ax.plot([.65, 15.35], [.95, .95], color="#D6DEDD", lw=1)
    text(ax, .65, .58, sentence, 15, GREEN, "bold")
    if detail:
        text(ax, 15.35, .58, detail, 11, MUTED, ha="right")


def save(fig, stem):
    ASSETS.mkdir(parents=True, exist_ok=True)
    for extension in ["png", "svg"]:
        fig.savefig(ASSETS / f"{stem}.{extension}", dpi=150, facecolor=BG)
    plt.close(fig)


def capability_boundary():
    fig, ax = canvas(1, "模型学会流程以后，重新划分Skill的职责", "后训练可强化通用方法；当前项目的事实与交付结果，仍需在任务中获取。")
    card(ax, .8, 4.02, 6.65, 2.5, "模型可逐步内化", "通用推理与任务组织\n自我检查与策略调整\n已能稳定完成的步骤，减少重复规定", BLUE, "#F0F5FA", 22)
    card(ax, 8.55, 4.02, 6.65, 2.5, "Skill继续提供", "当前需求、项目事实与环境信息\n获取项目信息与执行验证的脚本\n明确的交付约束与有效验证入口", GREEN, "#F0F7F3", 22)
    text(ax, 8, 3.57, "学会怎样验证，仍需要运行才能知道当前代码是否通过。", 17, INK, "bold", ha="center")
    text(ax, .8, 3.02, "模型能力变化后，重新检查步骤的增量价值", 14, GREEN, "bold")
    for x, title, body in [(.8, "复测当前模型", "基线与现行Skill"),
                           (4.6, "识别冗余与缺口", "结合执行与失败"),
                           (8.4, "调整外部方法", "精简、脚本整合、补强"),
                           (12.2, "检验候选版本", "质量与执行开销")]:
        card(ax, x, 1.25, 3.0, 1.38, title, body, GREEN, "#F5F8F4", 16)
    arrow(ax, (3.85, 1.95), (4.54, 1.95), "运行反馈", 4.19, 2.28, GREEN)
    arrow(ax, (7.65, 1.95), (8.34, 1.95), "定向修改", 7.99, 2.28, GREEN)
    arrow(ax, (11.45, 1.95), (12.14, 1.95), "比较效果", 11.79, 2.28, GREEN)
    footer(ax, "模型能力 + 必要外部支持 + 持续复评 = 动态调整的工作方法")
    save(fig, "01-model-skill-boundary")


def evolution_path():
    fig, ax = canvas(3, "精简之后，还要从失败里补回约束", "六阶段概括优化重心的变化；整体收益不能拆成各阶段的独立贡献。")
    nodes = [
        (.8, 4.7, "一 / 能力构建", "生成、验证、分析、修复\n让一次任务能够闭环", BLUE, "#F0F5FA"),
        (6.05, 4.7, "二 / 问题发现", "重复读取、加载与报告\n检查过程负担", ORANGE, "#FBF3EB"),
        (11.3, 4.7, "三 / 流程精简", "减少通用流程的重复指导\n压缩说明、产物与执行链", "#95722B", "#FAF7E9"),
        (11.3, 1.72, "四 / 脚本整合", "用脚本获取信息与执行验证\n复用未变的项目证据", GREEN, "#F0F7F3"),
        (6.05, 1.72, "五 / 稳定性补强", "交付可运行、测试真执行\n验证结果与当前代码一致", BLUE, "#EFF5FB"),
        (.8, 1.72, "六 / 评测迭代", "比较质量与执行开销\n决定保留、调整或删除", PURPLE, "#F5F2FA"),
    ]
    for x, y, title, body, color, fill in nodes:
        card(ax, x, y, 3.9, 1.87, title, body, color, fill, 18)
    arrow(ax, (4.75, 5.65), (5.99, 5.65), "投入运行", 5.36, 5.93, BLUE)
    arrow(ax, (10.0, 5.65), (11.24, 5.65), "定位冗余", 10.63, 5.93, ORANGE)
    arrow(ax, (13.25, 4.65), (13.25, 3.64), "收敛操作", 14.15, 4.15, GREEN)
    arrow(ax, (11.24, 2.66), (10.0, 2.66), "失败反馈", 10.63, 2.94, ORANGE)
    arrow(ax, (5.99, 2.66), (4.75, 2.66), "比较效果", 5.36, 2.94, BLUE)
    text(ax, 7.95, 4.16, "精简与补强，都由实际问题推动", 17, GREEN, "bold", ha="center")
    text(ax, .8, 1.26, "新的运行反馈，继续决定下一轮优化方向。", 12, MUTED)
    footer(ax, "问题定位 + 定向修改 + 结果比较 = 下一版方法")
    save(fig, "03-evolution-path")


def comparison(metrics):
    fig, ax = canvas(2, "整体评分相近，执行开销明显下降", "三组各140个对应任务；质量分差只作描述性比较。")
    groups = metrics["groups"]
    colors = ["#ADB9BF", ORANGE, GREEN]
    panels = [
        ("整体质量评分", "quality_score", 1, (0, 105), [0, 25, 50, 75, 100], "分", lambda v: f"{v:.2f}"),
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
        text(ax, x, 1.81, value, 22, GREEN, "bold", ha="center")
        text(ax, x, 1.34, label, 12, MUTED, ha="center")
    footer(ax, f"{paired['token_decreased']}/140个任务Token下降；{paired['duration_decreased']}/140个任务耗时缩短。")
    text(ax, 15.33, .18, "Token不等于账单；平均任务耗时不等于批次墙钟时间。", 10, MUTED, ha="right")
    save(fig, "02-quality-cost-comparison")


def information_lifecycle():
    fig, ax = canvas(4, "经验留下来，信息按需进入", "其他Skill可参考的信息组织方式：分别支持任务执行与方法复盘。")
    boxes = [
        (.8, 4.33, "01 / 当前方法", "内容：规则、脚本、触发条件\n使用：执行相关任务时\n更新：方法版本变化时", BLUE, "#F0F5FA"),
        (8.35, 4.33, "02 / 任务信息", "内容：输入材料、需求、执行环境\n使用：当前决策需要时\n更新：材料或环境变化时", GREEN, "#F0F7F3"),
        (.8, 1.6, "03 / 验证结果", "内容：交付结果是否满足要求\n使用：确认适用于当前产物与条件\n更新：产物、输入或执行条件变化时", ORANGE, "#FBF3EB"),
        (8.35, 1.6, "04 / 迭代记录", "内容：修改理由、适用条件、评测结果\n使用：复盘与修改Skill时\n更新：完成一次版本比较后", PURPLE, "#F5F2FA"),
    ]
    for x, y, title, body, color, fill in boxes:
        card(ax, x, y, 6.8, 2.21, title, body, color, fill)
    text(ax, 7.99, 4.07, "日常执行使用当前有效的信息；方法复盘再读取迭代记录。", 15, GREEN, ha="center", weight="bold")
    text(ax, .8, 1.2, "任务材料、产物或环境变化后，重新确认相关验证结果。", 11.5, MUTED)
    footer(ax, "有效方法 + 按需事实 + 当前验证 = 更可靠的执行")
    save(fig, "04-information-lifecycle")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-metrics", action="store_true")
    args = parser.parse_args()
    if args.refresh_metrics:
        refresh_metrics()
    metrics = json.loads(DATA.read_text(encoding="utf-8"))
    setup_fonts()
    capability_boundary()
    evolution_path()
    comparison(metrics)
    information_lifecycle()
    print(json.dumps({"figures": 4, "formats": ["png", "svg"], "paired": metrics["paired"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

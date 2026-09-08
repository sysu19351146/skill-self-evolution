# Skill自进化文章包

`source.md`是正文，`review.md`记录本轮全文与配图审查、修改理由和证据边界。正文保留RQ/RA结构，主线是规则在当前模型、任务与环境下的增量价值，以及规则的加入、复用和退出条件。

RQ1比较完整Skill与无Skill的收益和成本；RQ2解释新版的组合改动与实测变化；RQ3提出执行反馈、独立验收与版本回退的更新机制。RQ3属于迁移建议，未写成已完成的跨Skill实验或全自动系统。同模型对照不用于证明后训练因果关系。

正文保留相对路径配图，不添加外部参考资料列表。头部YAML保存发布元信息；粘贴到不支持YAML的平台时，以`title`作为帖子标题并移除元信息，上传四张PNG后替换图片路径。

## 文件组织

- `source.md`：修订后的正文。
- `review.md`：审查结论、证据定位与尚缺的实验材料。
- `assets/01-model-skill-boundary.png / .svg`：职责与规则价值判断框架。
- `assets/02-quality-cost-comparison.png / .svg`：三组数值比较与开销负例。
- `assets/03-evolution-path.png / .svg`：六阶段顺序与后续复评路径。
- `assets/04-information-lifecycle.png / .svg`：执行反馈与独立验收机制。
- `assets/data/metrics.json`：可携带的数据快照与口径说明。
- `build-figures.py`：四图的Matplotlib源代码。
- `prompts/`：三张机制图的可选白板提示词，已同步当前内容，未调用AI绘图。

正文按keven-blog指南修订；备用提示词按whiteboard-infographic指南整理。实际PNG/SVG由脚本绘制，保留可编辑源代码；图2数值直接读取数据快照。

## 重建配图

需要Python、Matplotlib和中文字体。脚本在Windows上优先选择微软雅黑，也支持Noto Sans CJK SC。

```powershell
python -m pip install matplotlib
python build-figures.py
```

要从原始JSONL重新汇总，显式指定包含三个输入文件的目录：

```powershell
python build-figures.py --refresh-metrics --metrics-root 'D:\wzh\gitcode\paper-writing-9-4'
```

目录需要包含`token_noskill.jsonl`、`token_metrics.jsonl`和`token_newskill.jsonl`。不提供原始目录也可以用随包快照重建四图。

脚本核对三组各140个唯一任务、7个项目、配对集合、模型标识和会话输入输出字段，复算Token、耗时、上升/下降任务数及节省量的输入侧占比。质量评分沿用既有报告值，不从空的逐任务评分字段推算。过程指标与项目组评分的出处记录在`review.md`。

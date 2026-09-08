# Skill自进化文章包

`source.md`是最终正文，保留模型通过后训练逐步内化通用方法、Skill需要重新评估冗余这一主题。主体采用实证主线：RQ1比较完整Skill与无Skill的质量和成本，RQ2比较流程精简、脚本整合与约束补强后的变化，RQ3提炼可供其他Skill参考的自进化流程，说明如何建立对照、修改规则、验证效果并更新版本；这是方法推广建议，并非已完成的跨Skill实验。完整Skill明确指旧版完整流程。每个RQ先以RA给出回答，再展开证据与机制。现有数据是同模型标识下的Skill对比，没有被写成跨模型或后训练因果实验。头部YAML用于保存标题等发布元信息；粘贴到不支持YAML的论坛时，将`title`作为帖子标题，移除首尾`---`之间的元信息。

正文没有参考资料列表、脚注、数据来源段落或外部超链接；图片采用相对路径嵌入。发布到论坛时上传对应PNG，并替换图片位置即可。

## 文件组织

```text
skill-self-evolution/
├── source.md
├── assets/
│   ├── 01-model-skill-boundary.png / .svg
│   ├── 02-quality-cost-comparison.png / .svg
│   ├── 03-evolution-path.png / .svg
│   ├── 04-information-lifecycle.png / .svg
│   └── data/
│       └── metrics.json
├── prompts/
│   ├── 01-model-skill-boundary.md
│   ├── 03-evolution-path.md
│   └── 04-information-lifecycle.md
├── build-figures.py
└── README.md
```

## 两个Skill的应用

- `keven-blog`：使用用户更新并重新安装的版本；先给出判断，再由具体运行现象解释机制；限制对特定单测Skill的展开；清理中英文间空格、套话与否定式排比，并按新增P0规则检查意义拔高、模糊归因和机械节奏。
- `whiteboard-infographic`：为模型与Skill的职责划分、六阶段路径和信息使用机制分别编写完整白板提示词，包含布局、图标、配色、中文标注、箭头含义和总结公式。

正文已经嵌入四张实际PNG，不依赖后续生成。当前机制图由脚本绘制，白板提示词是可选的视觉替换方案，尚未用于调用AI绘图。数据图使用Matplotlib绘制，避免生成模型改动数值。SVG保留矢量输出，可用于后续排版。

## 重建配图

需要Python、Matplotlib和支持中文的字体。脚本在Windows上自动选用微软雅黑，也支持安装了Noto Sans CJK SC的环境。

```powershell
python -m pip install matplotlib
python build-figures.py
```

在原工作区内，可重新汇总三组会话数据：

```powershell
python build-figures.py --refresh-metrics
```

脚本核对140个唯一任务、三组配对集合和会话Token字段，质量评分使用既有整体结果。统计口径与局限保存在`assets/data/metrics.json`中，不作为正文数据来源段落发布。

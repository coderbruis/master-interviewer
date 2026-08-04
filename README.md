# 大师面试官（Master Interviewer）

一个由资料驱动、会追问、会纠错、会讲原理，也会持续追踪掌握度的 Codex Skill。

它不只适用于简历模拟面试。你也可以输入 JD、项目文档、技术文章、学习笔记或代码，让它把材料拆成原子知识点，再进行查漏、深挖、讲解和复习。

## 特点

- **资料驱动**：从简历、项目、JD、学习文档和代码中生成知识点目录。
- **自适应追问**：围绕回答中的真实缺口继续深挖，而不是随机背题。
- **诊断与原理**：明确指出对错、遗漏和因果问题，并给出自包含参考答案。
- **状态追踪**：记录覆盖度、掌握度、重点题和复习计划。
- **隐私优先**：状态只保存必要元数据，不保存原始简历或文档正文。

## 安装

将 Skill 目录复制到 Codex 的 skills 目录：

```bash
cp -R skills/master-interviewer ~/.codex/skills/master-interviewer
```

重新载入 Codex 后，可以这样开始：

```text
使用 $master-interviewer 根据这份简历做项目深挖。
使用 $master-interviewer 根据这篇技术文档帮我查漏补缺。
查看我的掌握度和重点错题。
```

## 仓库结构

```text
skills/master-interviewer/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── grading-and-review.md
│   └── source-model.md
└── scripts/progress_tracker.py
```

`examples/catalog.example.json` 是不含个人信息的目录示例。真实进度默认写入 `~/.codex/master-interviewer-state/`，不会存放在仓库中。

## 进度脚本

初始化一个演示档案：

```bash
python3 skills/master-interviewer/scripts/progress_tracker.py \
  --state-dir /tmp/master-interviewer-demo \
  init \
  --profile demo \
  --candidate "Demo User" \
  --role "Backend Engineer" \
  --catalog examples/catalog.example.json
```

查看报告：

```bash
python3 skills/master-interviewer/scripts/progress_tracker.py \
  --state-dir /tmp/master-interviewer-demo \
  report --profile demo
```

开发和测试时建议总是传入临时的 `--state-dir`，避免与真实学习数据混合。

## 隐私说明

本仓库不包含作者简历、项目资料或历史复习进度。使用时请不要把密钥、客户数据或公司内部资料提交到 Git；目录中的 `source` 字段应使用安全、抽象的来源定位。

## 当前阶段

这是可用的初始版本，重点先放在稳定的面试流程、原子知识点和本地进度追踪。后续可继续扩展资料导入器、更多可视化以及可配置的复习策略。

## License

[MIT](LICENSE)

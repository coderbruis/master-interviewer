# 大师面试官（Master Interviewer）

一个由资料驱动、会追问、会纠错、会讲原理，也会持续追踪掌握度的 Codex Skill。把简历、JD、项目文档、技术文章、学习笔记或代码交给它，就能开始一场有上下文、有记录、能复习的模拟面试。

它不只是一个随机出题器：Skill 会先把资料拆成原子知识点，再根据你的回答进行查漏、深挖、讲解和间隔复习。

## 特点

- **资料驱动**：从简历、项目、JD、学习文档和代码中生成知识点目录。
- **自适应追问**：围绕回答中的真实缺口继续深挖，而不是随机背题。
- **大厂风格**：支持京东、阿里、字节、腾讯和通用风格，并可与深挖、查漏策略组合。
- **诊断与原理**：明确指出对错、遗漏和因果问题，并给出自包含参考答案。
- **状态追踪**：记录覆盖度、掌握度、重点题和复习计划。
- **隐私优先**：状态只保存必要元数据，不保存原始简历或文档正文。

## 安装

将 Skill 目录复制到 Codex 的 skills 目录：

```bash
cp -R skills/master-interviewer ~/.codex/skills/master-interviewer
```

重新载入 Codex 后即可使用 `$master-interviewer` 显式唤起 Skill。

## 快速开始

### 1. 提供面试资料

上传文件、粘贴内容或让 Codex 读取当前工作区，然后直接说明目标：

```text
使用 $master-interviewer 根据这份简历做项目深挖。
使用 $master-interviewer 根据这篇技术文档帮我查漏补缺。
使用 $master-interviewer 对照这份 JD 和我的简历，找出能力缺口并开始提问。
使用 $master-interviewer 阅读当前项目代码，重点考察并发和数据库设计。
```

没有资料也可以开始。Skill 会询问必要信息；如果不影响出题，也可以先按岗位和经验级别建立临时知识目录。

### 2. 逐题作答

Skill 每次只问一个原子问题。你直接回答即可，它会给出明确结论、指出具体缺口、补充自包含的参考答案，并根据当前模式决定是否追问。

```text
候选人：线程池的核心参数包括 corePoolSize、maximumPoolSize……
候选人：我不确定，提示一下。
候选人：这题不会，给我参考答案。
```

### 3. 随时切换策略

不需要记复杂语法，直接输入下表中的短语即可。它们是对话快捷指令，不是需要组合按键的键盘快捷键。

| 快捷指令 | 作用 |
|---|---|
| `$master-interviewer` | 显式启动 Skill；未指定策略时，根据当前资料和目标开始 |
| `京东风格` / `阿里风格` / `字节风格` / `腾讯风格` | 切换公司面试风格，并保持当前策略 |
| `阿里 深挖` / `字节 查漏` | 同时切换公司风格与面试策略 |
| `当前模式` / `当前命令` | 查看当前顶层模式、策略、公司风格和可复现命令 |
| `查看命令` / `风格列表` | 查看完整命令速查或全部公司风格 |
| `查漏` / `广度扫描` / `高频题扫描` | 扩大覆盖面，优先发现未问和薄弱知识点 |
| `深挖` / `项目深挖` / `技术栈深挖` | 围绕一个项目主张或技术点连续追问事实、决策、原理、边界和验证 |
| `提示一下` | 只给当前题的最小必要提示，继续等待你作答 |
| `不会` / `不清楚` | 记录当前薄弱点，给出参考答案并加入复习队列 |
| `参考答案` / `讲解` / `分析原理` | 暂停评分式追问，完整讲清当前问题 |
| `复盘` | 暂停出题，复盘本轮回答、错误和后续建议 |
| `下一题` / `继续面试` | 结束当前讲解或恢复面试，按当前策略选择下一题 |
| `深挖这个问题` | 围绕当前暴露的知识点继续向下追问 |
| `错题复习` / `重点题` | 从重点题和到期复习队列中优先出题 |
| `查看进度` / `覆盖情况` / `掌握度` | 只读查看覆盖率、掌握度、重点题和修正进度，不改变成绩 |
| `日常` / `退出面试` | 停止模拟面试，恢复普通助手模式 |

这些指令可以带上下文，不必逐字照抄。例如：

```text
先查漏，重点扫 Java 并发、JVM 和 MySQL，每次只问一题。
这个问题继续深挖，重点问异常场景和方案取舍。
查看进度，只展示还没覆盖和需要修正的知识点。
错题复习，换一种问法，不要重复原题。
```

公司名称表示可复用的模拟面试风格，不是对应公司的官方题库或录用标准。默认风格为京东，旧档案会自动获得兼容配置。风格和策略会随候选人档案持久化。

## 常见使用方式

### 简历项目深挖

```text
使用 $master-interviewer 阅读我的简历，先确认你理解的项目事实，再从最容易被面试官击穿的项目亮点开始深挖。
```

Skill 会沿着“事实 → 决策 → 原理 → 边界 → 验证”推进，并区分真实经历、设计目标、估算值和线上数据，避免替你虚构项目细节。

### 对照 JD 查漏补缺

```text
使用 $master-interviewer 对照这份高级后端工程师 JD 和我的简历做查漏。优先问岗位要求但简历证据不足的知识点。
```

### 学习技术文档或代码

```text
使用 $master-interviewer 阅读这篇 Kafka 文档，拆出原子知识点。先讲解，再用小例子和反例检验我是否真正理解。
```

### 复习薄弱项

```text
查看进度。
重点题。
错题复习，优先考最近回答为 C 或 D 的知识点。
```

一次答对不会立即清除历史薄弱点。Skill 会通过间隔复习和不同问法验证是否稳定掌握。

## 仓库结构

```text
skills/master-interviewer/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── grading-and-review.md
│   ├── company-styles.md
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

切换并查看当前配置：

```bash
python3 skills/master-interviewer/scripts/progress_tracker.py \
  --state-dir /tmp/master-interviewer-demo \
  set-config --profile demo --top-mode interviewer --strategy deep --style alibaba

python3 skills/master-interviewer/scripts/progress_tracker.py \
  --state-dir /tmp/master-interviewer-demo \
  show-config --profile demo
```

开发和测试时建议总是传入临时的 `--state-dir`，避免与真实学习数据混合。

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

## 进度展示示例

下面是一个仅保留通用技术知识点的脱敏示例，不对应任何真实候选人，也不包含简历、公司、项目或业务数据。覆盖率表示知识点是否已经被提问，掌握度表示最近一次独立回答的质量，两者不会混为一谈。

```text
总体覆盖：████░░░░░░ 13/36（36.1%）
掌握分布：A 1｜B 5｜C 6｜D 1｜未评估 23
重点复习：重点拷问 2｜重点复习 6｜持续观察 5
修正进度：待修正 13｜已完成修正 0
```

掌握度含义：A 为原理、场景和边界均准确；B 为结论正确但细节不足；C 为只掌握部分概念；D 为回答错误或尚不会。

| 知识点 | 掌握 | 主要薄弱点 |
|---|---:|---|
| Dubbo 超时、重试与服务治理 | C | 写接口重试、超时结果不确定性和端到端幂等 |
| JVM 内存、GC 与性能调优 | B | Full GC 边界、泄漏判断和生产现场诊断链路 |
| Java 集合与底层数据结构 | C | HashMap 树化条件、扩容拆分和并发写风险 |
| AQS、锁与 CAS | B | 等待队列状态、取消节点和非公平竞争边界 |
| Kafka 分区与副本机制 | C | HW/LSO、acks、最小 ISR 和 Leader 选举 |

这个视图可以帮助使用者同时回答三个问题：哪些内容还没有覆盖、已经回答的内容掌握到什么程度、下一轮应该优先修正什么。

## 隐私说明

本仓库不包含作者简历、项目资料或历史复习进度。使用时请不要把密钥、客户数据或公司内部资料提交到 Git；目录中的 `source` 字段应使用安全、抽象的来源定位。

## License

[MIT](LICENSE)

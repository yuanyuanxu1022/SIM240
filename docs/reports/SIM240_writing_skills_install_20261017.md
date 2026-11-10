# 科研写作Skill双平台安装与自动选用

日期：2026-10-17。用户明确要求补充此前推荐的3个Skill，并在以后按任务自动使用。沿用已确认的Codex与Claude Code双平台范围；没有安装整套榜单。

## 已完成

| Skill | 来源固定提交 | 上游版本 | 每平台文件数 |
| --- | --- | --- | --- |
| scientific-writing | K-Dense-AI/scientific-agent-skills@a1043ef544e3a100c28e70a736b6cf32554d0677 | 2.3 | 33 |
| peer-review | 同上 | 2.4 | 26 |
| academic-humanizer | AIScientists-Dev/academic-humanizer@94b88b23703bed7df507acae7d6d5876209a0cdf | 0.3.3 | 11 |

安装位置：`/home/dell/.codex/skills/`与`/home/dell/.claude/skills/`中上述三个同名子目录；每平台70文件，未覆盖原有同名目录或其他Skill。许可证均保留。仅将不被本地验证器接受的顶层compatibility/version字段移入metadata；正文、脚本、模板与原有资源哈希保持一致。新增agents/openai.yaml明确allow_implicit_invocation=true。

安装先使用官方skill-installer。K-Dense固定提交的git安装失败，报临时repo目录已存在；未向活跃技能目录写入该半成品。随后用新的独立source-kdense目录fetch同一固定提交、核对HEAD，沿用安装器_validate_skill/_copy_skill完成校验与复制。academic-humanizer固定提交下载成功。该初次工具错误不隐去，也不作为最终安装失败。

自动选用规则已写入：

- `/home/dell/.codex/AGENTS.md`：个人级长期指令。
- `/home/dell/.claude/CLAUDE.md`：新建个人级指令，原文件不存在。
- 本项目`AGENTS.md` §0.2：跨AI可读路由及SIM240范围限制。

规则：起草/证据组织→scientific-writing；稿件自审/论证检查→peer-review；已有文本语言润色→academic-humanizer。其他现有文献/作图/Office技能按需使用，不要求每次全部串联。项目协议、原始证据、真实FAIL和长算授权边界优先；不把确定性CFD网格不确定度套成医学样本量或p值问题。已有明确任务授权沿用；第三方保密材料另依适用政策。自动发现默认从下一轮或刷新后的会话使用，不能以写入规则证明每一次未来请求都会正确路由。

## 验证与边界

`/home/dell/.codex/skill-install-records/20261017-writing-auto/verify_installation.py`独立exit0，49项检查全部通过：两平台文件哈希一致、上游正文及资源保持、六入口格式有效、自动选用开关、入口资源路径，以及15个本地CLI的帮助入口。

六个隔离合成软件检查退出码为0/1/1/0/1/1：创建明确未完成草稿；拒绝覆盖同目录；拒绝将占位草稿通过文字检查；接受格式合法的合成证据条目；拦下缺证据的supported条目；保持未填写审查授权模板的阻断。非零是预期拦截，未改变阈值。所有样例均为新建合成材料，未打开用户稿件或运行科研计算。

Codex CLI 0.162.1的只读app-server skills/list实际返回3项均enabled=true、scope=user，并正确解析界面元数据。没有发起模型对话或付费API调用。此证据确认文件可被该Codex运行时发现，不等于实际稿件自动触发/写作质量测试。Claude Code当前PATH无可执行程序，因此只确认其文件/指令/资源和与Codex的逐文件一致性，运行时发现待在用户的Claude会话核实。

完整清单、逐文件SHA256、命令与退出、原版、两份既有指令备份、合成检查和Codex发现结果保留在`/home/dell/.codex/skill-install-records/20261017-writing-auto/`；主证据为`installation.json`。没有修改登录、模型配置、原始结果、源码或冻结协议。

## 交接

后续用户只需说“写引言”“检查论文”“润色这段”，由代理按规则选择相关Skill并简短说明。当前安装任务已完成；实际稿件效果按后续具体任务检验，Claude发现未实测，不能冒称通过。用户“以后自动使用”的长期偏好已另存记忆更新便条。无新仿真、编译、数值验收或Gate放行，run_id不适用，无新增长计算授权；不需用户执行任何仿真命令。

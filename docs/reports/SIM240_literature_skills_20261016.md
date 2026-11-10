# 文献检索 Skills 安装与使用（2026-10-16）

已按用户要求安装4个文献工作Skill，同时放入Codex与Claude Code。来源为第三方K-Dense-AI/scientific-agent-skills，固定提交`a1043ef544e3a100c28e70a736b6cf32554d0677`。沿用用户此前明确的双平台偏好。

## 装了什么

| Skill | 用途 | Codex入口 |
|---|---|---|
| paper-lookup | 主题/DOI检索、引文及开放获取线索，保留来源 | `/home/dell/.codex/skills/paper-lookup/SKILL.md` |
| literature-review | 检索式、筛选、证据提取、综述和检索记录 | `/home/dell/.codex/skills/literature-review/SKILL.md` |
| citation-management | 核对DOI/标题/作者等书目信息，整理BibTeX | `/home/dell/.codex/skills/citation-management/SKILL.md` |
| scientific-critical-thinking | 区分证据、假设、外推与待验证结论 | `/home/dell/.codex/skills/scientific-critical-thinking/SKILL.md` |

Claude入口为`/home/dell/.claude/skills/<同名Skill>/SKILL.md`。两平台各67文件，逐文件SHA256一致。Skill在下一轮或刷新会话后可被发现；当前Claude Code运行时是否已刷新未验证。

## 已验证与限制

- 四个Skill在两个平台的格式检查通过，全部自带Python源码完成语法解析，4个主要CLI帮助入口exit0。
- 元数据提取工具从Crossref成功取回Jain2017与Dewangan2020的DOI、准确标题及BibTeX信息，逐条匹配成功。
- paper-lookup分页工具完成一次nanoimprint公开检索，取3条后按限制停止并明确标为不完整。这只是安装功能检查，不是论文查新。
- DOI核验器确认两个DOI均已注册。其中一次Jain元数据请求遭遇SSL EOF，如实记为metadata unavailable；另一个提取工具已成功取得两条元数据。保留两种证据，不绕过SSL验证、不将请求失败写成成功。
- 本地校验器不接受上游compatibility头字段；只删除该头字段，正文和脚本不改，原版入口和依赖说明保存在安装记录目录。
- 基础Python与requests可用，无需新增密钥。Google Scholar的scholarly、Parallel认证、Pandoc/XeLaTeX、可选AI示意图功能未安装/未测试；需要专用功能时再按任务处理，不默认付费调用。
- Skill不会赋予WoS/ScienceDirect订阅或绕过全文权限，不会自动完成Asta操作。DOI存在不证明公式或结论正确；仍须回原文页码核对，查新仍须记录覆盖范围。

## 以后直接这样说

1. **找论文：**“用paper-lookup和literature-review，检索满充液、固定间隙、矩形沟槽中的沿槽/横槽输运；列检索式、数据库与筛选理由，区分摘要线索和全文证据。”
2. **核引用：**“用citation-management，逐条核对这份清单的DOI、标题、作者和年份，并导出BibTeX；有缺口写未核实。”
3. **查重合与创新：**“用scientific-critical-thinking，比较论文与我们的几何、边界、驱动及参数范围；每条判断给原文依据，不根据检索无命中宣布首次。”

SIM240工程物理检索优先采用合适数据库和期刊原文，不机械套用医学临床评价框架。用户范围与AGENTS协议优先于通用Skill指南。

安装清单、原版入口、文件哈希与检查输出：`/home/dell/.codex/skill-install-records/20261016-literature-skills/installation.json`及同目录`checks/`。[固定版本来源](https://github.com/K-Dense-AI/scientific-agent-skills/tree/a1043ef544e3a100c28e70a736b6cf32554d0677)。

本轮仅工具安装与最小公开接口检查；无新增OpenLB计算、数值验收或Gate放行，不刷新此前D2运行状态。

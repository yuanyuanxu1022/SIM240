# 优先任务：恢复邀请老师协作的能力

2026-10-27。用户明确需要账号能邀请老师；直接上传到自有仓库不是该问题的替代解决方案。原上传清单保留，当前优先处理协作邀请，先前准备的所有者登录脚本不作为本轮修复步骤。

## 已确认

- 用户确认老师账号仍为`bokong537`，新账号能检索并选中老师，但发送邀请时出现错误。当前错误原文和对应截图尚未取得，不能照搬旧仓库的历史错误字符串。
- 公开接口`/users/bokong537`返回200，用户名bokong537、显示名Bo Kong、ID34483962，搜索1条；不是“老师账号搜不到”分支。
- 用户说明主邮箱Verified，随后提供Emails设置截图，截图显示Primary、Verified，顶部显示25yuanyuanxu-source。无需再次验证同一邮箱；本报告不保存真实邮箱地址。
- 公开按名查询`/users/25yuanyuanxu-source`仍404；目标仓库此前也404。可以记录对外不可见的当前现象，不能单凭404判为不存在、封禁或某种具体安全限制。

## 新出现的身份信息矛盾

主代理从截图下方GitHub隐私邮箱说明读到数字前缀34883237，但公开`GET /user/34883237`返回200、login=dengzhang、id=34883237；按名`/users/dengzhang`也对应同一ID。实查结果保存`public_identity_checks.json`。本轮已调用GPT-6 Astra｜High独立只读复核，代理github_identity_review独立未认证HTTPS查询复现上述对应，未改文件或邀请/登录。

GitHub官方[邮箱格式文档](https://docs.github.com/en/account-and-profile/reference/email-addresses-reference)说明ID+USERNAME形式；[用户接口文档](https://docs.github.com/en/rest/users/users#get-a-user-using-their-id)说明数字ID是持久标识、login可变。因此目前要核清“同一浏览器、当前官方设置页、实际显示数字”的对应，不能仅凭裁剪截图推导原因。

[改名文档](https://docs.github.com/en/account-and-profile/concepts/username-changes)支持旧profile链接可能404、GitHub Mobile可能保留旧显示名，但不证明桌面Emails页出现此差异的原因。缓存、改名同步、数字误读或页面上下文差异均未证实。没有官方证据表明手工添加邮箱能改写该自动说明里的数字ID，也没有据此指控截图伪造或账号被盗。

## 最小下一步（历史准备；完整截图已收到，当前见补证记录）

在当前登录新账号的同一浏览器中直接打开`https://github.com/settings/emails`，刷新一次；截图同时保留地址栏、页顶账号名和下方完整GitHub隐私邮箱说明行。真实邮箱可以遮住。此步用于核当前身份与页面来源，不修改设置、不重新验证邮箱、不重复邀请，也不切换登录。

身份核清后，读取已有的老师邀请失败错误原文/截图，再选择核查账号通知或支持工单。不把单纯等待24小时、购买套餐、反复新建账号或重复点击当作已验证修复。

GitHub官方[账号受限说明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/preventing-unauthorized-access)确认某些限制可同时影响公开主页/搜索与敏感操作，即使仍可登录；这只提供候选机制，不构成本账号的诊断。免费账号也可以就账号/安全问题联系支持，见[官方工单说明](https://docs.github.com/en/support/contacting-github-support/creating-a-support-ticket)。已准备`SUPPORT_TICKET_DRAFT.md`，明确还需要刷新页与当前错误证据，未提交工单或发送消息。

## 权限与项目状态

没有执行登录脚本、增加token scope、改邮箱/密码/账号设置、发送邀请、修改remote、提交或推送。没有编译、求解、真实N8提取、第二项或新run_id。原8,637项上传准备与科学状态保留；旧N8 run_id=D4_N8_diag_v3_1_20261026_v1，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD，历史FAIL保持。

本轮是GitHub协作排障，不新增科研结论；账号内部状态需要本人页面证据或GitHub支持核实。

2026-10-27完整截图更新：地址栏、账号名、Verified及隐私邮箱编号已补齐；不再要求重复同页截图。当前结论与停止点见[FULL_SCREENSHOT_FOLLOWUP.md](FULL_SCREENSHOT_FOLLOWUP.md)，可提交支持文本见[SUPPORT_REQUEST_READY.md](SUPPORT_REQUEST_READY.md)，未提交。

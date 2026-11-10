# GitHub 支持申请：可由用户提交，尚未发送

2026-10-27。最新完整截图已补齐地址栏、账号名、主邮箱Verified以及GitHub隐私邮箱说明行。以下只陈述可核事实，不宣称账号已被封禁、受限或被盗。当前邀请错误的精确英文尚未取得，可在提交时附已有报错截图；这不妨碍先请求平台核查账号。

请用受影响的新账号登录 https://support.github.com/ ，选择账号相关问题。免费账号也可就账号问题联系支持。把下面Subject与正文复制到表单；可以附本次截图，并遮住真实邮箱，保留地址栏、账号名、Verified与GitHub隐私邮箱说明行。无需重复邀请以制造新报错。代理未提交表单或联系老师。

**Subject**

Unable to invite a collaborator; please check account visibility and identity

**Message**

Hello GitHub Support,

I need to invite my teacher, `bokong537`, to my research repository:
https://github.com/25yuanyuanxu-source/SIM240-data

I can sign in and access the repository settings. I can find and select `bokong537`, but sending the collaborator invitation fails.

My account settings display `25yuanyuanxu-source`, and my primary email is marked Verified. I have attached a screenshot with the browser address bar showing `github.com/settings/emails`.

On 27 October 2026, public API checks showed:
- `GET /users/bokong537`: HTTP 200.
- `GET /users/25yuanyuanxu-source`: HTTP 404.
- The numeric ID shown in the GitHub-provided noreply address on my settings page is `34883237`, but `GET /user/34883237` currently returns the login `dengzhang`.

Please investigate this account identity/visibility discrepancy and the failed collaborator invitation. Please let me know whether any account condition or restriction is involved and what steps are required to restore normal collaboration.

Thank you.

---

提交后保留工单编号及平台原始回复；回复说明具体限制前，根因保持未判定。不要提供密码、访问令牌或恢复代码。

官方工单说明：https://docs.github.com/en/support/contacting-github-support/creating-a-support-ticket 。

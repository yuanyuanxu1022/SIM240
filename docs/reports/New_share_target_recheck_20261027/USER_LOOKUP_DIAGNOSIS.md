# 截图中的账号检索失败：指定诊断

2026-10-27。用户截图显示SIM240-data的Add people弹框，输入yuanyuanxu1022后明确提示Could not find a GitHub account matching yuanyuanxu1022；背景Direct access为0。尚未选中可邀请账号，不能视为已发出邀请。

当前实查：已认证/user识别为yuanyuanxu1022；同账号按名称查询/users/yuanyuanxu1022为404，用户名搜索0条，未认证公开查询也404。新目标所属账号25yuanyuanxu-source的未认证查询同为404。可以报告当前对外检索不可见，不能据这些证据断言账号不存在、被封禁或限制的具体原因。此前另一个协作者邀请失败仅提供诊断方法，不作为本次根因证据。

该用户名与工具真实登录身份一致，不能再让用户重复同样的用户名搜索/点击。GitHub官方允许以用户名或关联邮箱邀请；下一最小动作是使用旧账号yuanyuanxu1022绑定且已验证的邮箱，在同一框试一次。旧账号公开email字段为空；/user/emails返回404并明确提示缺少user scope，表示当前工具读取权限不足，不表示账号未登记邮箱。没有执行工具提示中的gh auth refresh，没有增加授权范围或更改登录。

若用户知道关联邮箱，直接在网页输入即可，无需把邮箱发给AI。若邮箱仍无法匹配，停止重复尝试，进一步核账号通知/联系GitHub支持，不把受限猜测写成已证实事实。当前工具不能自动解除GitHub账号状态。

上传清单仍沿用8,637项固定版本；本轮未提交、改remote、接受其他邀请、发送邀请、推送或启动计算。来源/科学状态和旧FAIL保持。

官方邀请说明：https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository 。

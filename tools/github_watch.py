#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SIM240 GitHub 外部动作监控

作用：检查 yuanyuanxu1022/SIM240 是否出现「不是你本人」的动作。

边界（务必理解）：GitHub 不提供「谁查看了仓库 / 谁下载了文件」的记录，
公开仓库更是完全无从得知。本脚本只能发现**留下痕迹**的动作：
推送代码、上传文件、建删分支、被加为协作者、fork、star、提 PR、开 issue。

用法：
  python3 tools/github_watch.py             # 打印当前状态，不落盘
  python3 tools/github_watch.py --baseline  # 建立 / 重建基线
  python3 tools/github_watch.py --check     # 与基线比对，报告变化并更新基线

退出码：0 = 正常；2 = 发现需要你注意的动作。

匿名调用 GitHub 公开 API（不需要 token、不会泄露凭据），
一次检查约 6 个请求，匿名额度 60 次/小时，每天两次绰绰有余。
"""

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

OWNER = "yuanyuanxu1022"
REPO = "SIM240"

# 重点关注的账号：一旦其名下出现任何动作，单独高亮提示
# GitHub 用户名不区分大小写，比较时统一转小写
WATCH_USERS = ["kobong537"]
_WATCH_LOWER = {u.lower() for u in WATCH_USERS}

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "docs", "reports", "github_watch")
STATE = os.path.join(OUT_DIR, "state.json")
ALERT_LOG = os.path.join(OUT_DIR, "ALERTS.md")

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "sim240-github-watch/1.0",
}
BJ = timezone(timedelta(hours=8))

# 这些动作类型意味着「有内容进来了」或「权限被动了」，需要提醒
HIGH_RISK_EVENTS = {
    "PushEvent": "推送了提交",
    "CreateEvent": "新建了分支或标签",
    "DeleteEvent": "删除了分支或标签",
    "MemberEvent": "协作者列表被改动",
    "ForkEvent": "把仓库 fork 到自己名下",
    "PullRequestEvent": "提交了 PR",
    "IssuesEvent": "开了 issue",
    "ReleaseEvent": "发布了一个 release",
    "PublicEvent": "把仓库设为公开",
    "CommitCommentEvent": "评论了某个提交",
}
LOW_RISK_EVENTS = {"WatchEvent": "给仓库点了 star"}


def now_bj():
    return datetime.now(BJ).strftime("%Y-%m-%d %H:%M")


def gh(path):
    """匿名 GET，失败时返回 {'__error__': ...} 而不抛异常。"""
    req = urllib.request.Request(API + path, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__path__": path}
    except Exception as e:  # 网络问题
        return {"__error__": str(e), "__path__": path}


def actor_of(ev):
    return (ev.get("actor") or {}).get("login", "?")


def is_watched(login):
    """大小写不敏感地判断是否为关注账号。"""
    return bool(login) and login.lower() in _WATCH_LOWER


def summarize_event(ev):
    """把事件压成一句人话。"""
    t = ev.get("type", "?")
    p = ev.get("payload") or {}
    if t == "PushEvent":
        n = len(p.get("commits") or [])
        return f"推送了 {n} 个提交到 {p.get('ref', '').replace('refs/heads/', '')}"
    if t == "CreateEvent":
        return f"新建了 {p.get('ref_type', '?')}：{p.get('ref', '')}"
    if t == "DeleteEvent":
        return f"删除了 {p.get('ref_type', '?')}：{p.get('ref', '')}"
    if t == "MemberEvent":
        return f"协作者变动：{p.get('action', '')} {(p.get('member') or {}).get('login', '')}"
    if t == "ForkEvent":
        return f"fork 到了 {(p.get('forkee') or {}).get('full_name', '')}"
    if t == "WatchEvent":
        return "点了 star"
    if t == "PullRequestEvent":
        return f"PR #{p.get('number', '?')} {p.get('action', '')}"
    if t == "IssuesEvent":
        return f"issue #{p.get('issue', {}).get('number', '?')} {p.get('action', '')}"
    return t


def fetch_state():
    """抓一份当前快照。"""
    repo = gh(f"/repos/{OWNER}/{REPO}")
    commits = gh(f"/repos/{OWNER}/{REPO}/commits?per_page=30")
    events = gh(f"/repos/{OWNER}/{REPO}/events?per_page=50")
    forks = gh(f"/repos/{OWNER}/{REPO}/forks?per_page=100")

    if isinstance(repo, dict) and "__error__" in repo:
        return {"__fatal__": f"取仓库信息失败：HTTP {repo['__error__']}（可能是触发限速，稍后重试）"}

    st = {
        "checked_at": now_bj(),
        "repo": {
            "stars": repo.get("stargazers_count"),
            "watchers": repo.get("subscribers_count"),
            "forks": repo.get("forks_count"),
            "open_issues": repo.get("open_issues_count"),
            "pushed_at": repo.get("pushed_at"),
            "private": repo.get("private"),
        },
        "commit_shas": [],
        "head": None,
        "fork_logins": [],
        "event_ids": [],
        "event_map": {},
        "watch_users": {},
    }

    if isinstance(commits, list):
        st["commit_shas"] = [c["sha"] for c in commits]
        if commits:
            c0 = commits[0]
            st["head"] = {
                "sha": c0["sha"][:10],
                "author": ((c0.get("author") or {}).get("login")
                           or (c0.get("commit", {}).get("author", {}) or {}).get("name", "?")),
                "date": c0.get("commit", {}).get("author", {}).get("date", ""),
                "message": (c0.get("commit", {}).get("message", "") or "").split("\n")[0][:120],
            }

    if isinstance(events, list):
        for ev in events:
            eid = str(ev.get("id", ""))
            if not eid:
                continue
            st["event_ids"].append(eid)
            st["event_map"][eid] = {
                "type": ev.get("type"),
                "actor": actor_of(ev),
                "at": (ev.get("created_at") or "")[:19],
                "summary": summarize_event(ev),
            }

    if isinstance(forks, list):
        st["fork_logins"] = [(f.get("owner") or {}).get("login", "?") for f in forks]

    # 关注账号是否存在（账号不存在时，只盯这个名字等于监控空转）
    for u in WATCH_USERS:
        info = gh(f"/users/{u}")
        if isinstance(info, dict) and "__error__" in info:
            st["watch_users"][u] = "not_found" if info["__error__"] == 404 else f"error_{info['__error__']}"
        else:
            st["watch_users"][u] = info.get("login", u)

    return st


def commit_files(sha):
    """只在发现可疑提交时调用，取它改了哪些文件。"""
    d = gh(f"/repos/{OWNER}/{REPO}/commits/{sha}")
    if not isinstance(d, dict) or "__error__" in d:
        return None
    files = d.get("files") or []
    return {
        "author": ((d.get("author") or {}).get("login")
                   or (d.get("commit", {}).get("author", {}) or {}).get("name", "?")),
        "message": (d.get("commit", {}).get("message", "") or "").split("\n")[0][:150],
        "date": d.get("commit", {}).get("author", {}).get("date", ""),
        "files": [f.get("filename") for f in files][:40],
        "n_files": len(files),
        "stats": d.get("stats", {}),
    }


def diff(prev, cur):
    """返回 (高危项列表, 低危项列表, 说明行列表)。"""
    high, low, notes = [], [], []

    if not prev:
        notes.append("首次运行，只建立基线，不判断变化。")
        return high, low, notes

    # 1) 新提交
    prev_shas = set(prev.get("commit_shas") or [])
    new_shas = [s for s in (cur.get("commit_shas") or []) if s not in prev_shas]
    for sha in reversed(new_shas):  # 时间正序
        info = commit_files(sha)
        if not info:
            high.append({"kind": "新提交", "actor": "未知", "sha": sha[:10],
                         "note": "提交详情读取失败"})
            continue
        who = info["author"]
        entry = {"kind": "新提交", "actor": who, "sha": sha[:10], "note": info["message"],
                 "files": info["files"], "n_files": info["n_files"],
                 "stats": info["stats"], "at": info["date"]}
        if is_watched(who):
            entry["note"] = "[关注账号] " + entry["note"]
            high.append(entry)
        elif who.lower() != OWNER.lower():
            high.append(entry)
        # 本人提交不报（那是你自己在工作）

    # 2) 新事件
    prev_ids = set(prev.get("event_ids") or [])
    for eid in cur.get("event_ids") or []:
        if eid in prev_ids:
            continue
        ev = cur["event_map"].get(eid, {})
        who = ev.get("actor", "?")
        typ = ev.get("type", "")
        if who.lower() == OWNER.lower():
            continue  # 你自己的动作
        entry = {"kind": typ, "actor": who, "at": ev.get("at"), "note": ev.get("summary", "")}
        if is_watched(who):
            entry["note"] = "[关注账号] " + entry["note"]
            high.append(entry)
        elif typ in HIGH_RISK_EVENTS:
            high.append(entry)
        elif typ in LOW_RISK_EVENTS:
            low.append(entry)
        else:
            low.append(entry)

    # 3) fork 增加
    prev_forks = set(prev.get("fork_logins") or [])
    for f in cur.get("fork_logins") or []:
        if f not in prev_forks:
            entry = {"kind": "新 fork", "actor": f, "note": "有人把仓库复制到自己名下，可继续公开分发"}
            if is_watched(f):
                entry["note"] = "[关注账号] " + entry["note"]
            high.append(entry)

    # 4) star 计数增加（不显示是谁，只能知道数量变了）
    p_star = (prev.get("repo") or {}).get("stars")
    c_star = (cur.get("repo") or {}).get("stars")
    if isinstance(p_star, int) and isinstance(c_star, int) and c_star > p_star:
        low.append({"kind": "star", "actor": "（GitHub 不显示具体是谁）",
                    "note": f"star 数 {p_star} -> {c_star}"})

    # 5) 仓库可见性变化（公开/私有切换）
    if (prev.get("repo") or {}).get("private") != (cur.get("repo") or {}).get("private"):
        high.append({"kind": "可见性变化", "actor": "仓库设置",
                     "note": f"private: {(prev.get('repo') or {}).get('private')} -> {(cur.get('repo') or {}).get('private')}"})

    # 6) 关注账号是否存在过
    for u, status in (cur.get("watch_users") or {}).items():
        old = (prev.get("watch_users") or {}).get(u)
        if old != status:
            notes.append(f"关注账号 {u} 状态：{old or '未知'} -> {status}")

    return high, low, notes


def fmt_entry(e):
    parts = [f"- 【{e.get('kind')}】{e.get('actor', '?')}"]
    if e.get("at"):
        parts.append(f"  时间：{e['at']} UTC")
    if e.get("sha"):
        parts.append(f"  提交：{e['sha']}")
    if e.get("note"):
        parts.append(f"  说明：{e['note']}")
    if e.get("n_files") is not None:
        st = e.get("stats") or {}
        parts.append(f"  改动：{e['n_files']} 个文件 (+{st.get('additions', '?')}/-{st.get('deletions', '?')})")
        for fn in (e.get("files") or [])[:10]:
            parts.append(f"    - {fn}")
        if e["n_files"] > 10:
            parts.append(f"    … 另有 {e['n_files'] - 10} 个")
    return "\n".join(parts)


def write_alert_log(cur, high, low, notes):
    os.makedirs(OUT_DIR, exist_ok=True)
    exists = os.path.exists(ALERT_LOG)
    lines = []
    if not exists:
        lines.append("# SIM240 GitHub 外部动作告警记录\n")
        lines.append("> 只记录「留下痕迹」的动作。GitHub 无法提供「谁查看了仓库」。\n")
    lines.append(f"\n## {cur['checked_at']}\n")
    if not high and not low:
        lines.append("- 无外部动作（本人提交不计）。\n")
    for e in high:
        lines.append(fmt_entry(e) + "\n")
    for e in low:
        lines.append(fmt_entry(e) + "\n")
    for n in notes:
        lines.append(f"- {n}\n")
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    args = set(sys.argv[1:])
    check = "--check" in args
    baseline = "--baseline" in args

    cur = fetch_state()
    if "__fatal__" in cur:
        print(f"[结果] 检查失败：{cur['__fatal__']}")
        print("[提示] 不是有异常，是没查成功，稍后重试即可。")
        return 1

    prev = None
    if os.path.exists(STATE):
        try:
            with open(STATE, encoding="utf-8") as f:
                prev = json.load(f)
        except Exception:
            prev = None

    if baseline or not prev:
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
        r = cur["repo"]
        print(f"[基线已建立] {cur['checked_at']}")
        print(f"仓库：{OWNER}/{REPO}（{'私有' if r['private'] else '公开'}）")
        print(f"star {r['stars']} / fork {r['forks']} / 关注 {r['watchers']} / open issue {r['open_issues']}")
        if cur.get("head"):
            h = cur["head"]
            print(f"最新提交：{h['sha']} by {h['author']} — {h['message']}")
        print(f"已记录 {len(cur['commit_shas'])} 个提交、{len(cur['event_ids'])} 条事件作为基线。")
        for u, s in cur["watch_users"].items():
            if s == "not_found":
                print(f"[注意] 关注账号 {u} 在 GitHub 上不存在，只盯这个名字不会触发任何提醒。")
            else:
                print(f"[关注账号] {u} 存在。")
        return 0

    high, low, notes = diff(prev, cur)

    # 无论有无异常都更新基线，避免同一件事反复报
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)

    if not check:
        # 只看现状
        r = cur["repo"]
        print(f"[当前状态] {cur['checked_at']}")
        print(f"star {r['stars']} / fork {r['forks']} / 关注 {r['watchers']}")
        if cur.get("head"):
            h = cur["head"]
            print(f"最新提交：{h['sha']} by {h['author']} — {h['message']}")
        print(f"基线快照：{STATE}")
        return 0

    if not high and not low:
        r = cur["repo"]
        line = (f"[结果] 无异常（检查时间 {cur['checked_at']}）。"
                f"最近一次提交仍是你本人 {cur['head']['author'] if cur.get('head') else '?'}，"
                f"star {r['stars']} / fork {r['forks']} 未变。")
        print(line)
        for u, s in cur["watch_users"].items():
            if s == "not_found":
                print(f"[提示] 关注账号 {u} 仍不存在于 GitHub，这个名字的监控处于空转状态。")
        write_alert_log(cur, high, low, notes)
        return 0

    print(f"[结果] 发现 {len(high)} 项需注意、{len(low)} 项一般变化（检查时间 {cur['checked_at']}）")
    if high:
        print("\n== 需注意 ==")
        for e in high:
            print(fmt_entry(e))
    if low:
        print("\n== 一般变化 ==")
        for e in low:
            print(fmt_entry(e))
    for n in notes:
        print(f"\n[说明] {n}")
    for u, s in (cur.get("watch_users") or {}).items():
        if s == "not_found":
            print(f"[提示] 关注账号 {u} 不存在于 GitHub，这个名字本身不会触发提醒；以上异常来自其他账号。")

    write_alert_log(cur, high, low, notes)
    print(f"\n已追加记录：{ALERT_LOG}")
    return 2 if high else 0


if __name__ == "__main__":
    sys.exit(main())

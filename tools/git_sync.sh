#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# git_sync.sh — 按 AGENTS.md §6/§6.1 执行「审查 → 暂存 → 提交 → 推送 → 核验」
#
# 用法：
#   tools/git_sync.sh -n                     # 只列出候选改动（分组+体积+行数），不动仓库
#   tools/git_sync.sh -m "fix: xxx" CASE/xxx docs/yyy   # 只暂存这些明确路径
#   tools/git_sync.sh -m "chore: xxx" --dry   # 暂存并预览完整 diff，不提交
#
# 协议约束（本脚本强制，不提供绕过开关）：
#   - 拒绝整目录/整仓库暂存（禁止 `.`、`-A`、`--all`、`*`）；必须给明确路径。
#   - 暂存后必须通过：体积检查、敏感内容检查、`git diff --cached --check`。
#   - 推送目标固定 sim240/main（origin 指向导师只读仓库，pushurl 已置 DISABLED_READONLY）。
#   - push 后核验远端 commit 与本次文件 blob，核验失败只报"本地提交完成"。
#
# 数据分层参 .gitignore：网格/场/体数据、原始转储、媒体、他人论文原文不入库。
# 超过 SKIP_MB（默认 5MB）的文件会被拒绝并提示登记 .git/info/exclude。
# ---------------------------------------------------------------------------
set -uo pipefail

SKIP_MB="${SKIP_MB:-5}"
PUSH_REMOTE="${PUSH_REMOTE:-sim240}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
DRY_RUN=0
NO_PUSH=0
COMMIT_MSG=""

while getopts ":m:nrh" opt; do
  case "$opt" in
    m) COMMIT_MSG="$OPTARG" ;;
    n) DRY_RUN=1 ;;
    r) NO_PUSH=1 ;;
    h) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "未知参数: -$OPTARG" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
PATHSPEC=("$@")

cd "$(git rev-parse --show-toplevel)" || exit 3
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# --- 0. 只读预览：列出候选改动 -------------------------------------------
if [ "$DRY_RUN" -eq 1 ] && [ ${#PATHSPEC[@]} -eq 0 ]; then
  echo "[git_sync] 分支 $BRANCH ｜ 候选改动（按顶层目录聚合）："
  git status --porcelain | awk '{print $NF}' | cut -d/ -f1 \
    | sort | uniq -c | sort -rn | sed 's/^/    /'
  echo
  echo "  未跟踪文件数: $(git ls-files -o --exclude-standard | wc -l)"
  echo "  请给出明确路径后执行，例如："
  echo "    tools/git_sync.sh -m \"feat: xxx\" CASE/03_grid_convergence/G2_xxx docs/reports/yyy"
  exit 0
fi

# --- 1. 协议守卫：禁止整目录暂存 -----------------------------------------
if [ ${#PATHSPEC[@]} -eq 0 ]; then
  echo "[git_sync] ✗ 未指定路径。AGENTS.md §6.1 禁止 git add . / -A。" >&2
  echo "  先用 -n 查看候选，再给出明确路径。" >&2
  exit 2
fi
for p in "${PATHSPEC[@]}"; do
  case "$p" in
    .|./|./*|-A|--all|'*') echo "[git_sync] ✗ 拒绝整仓库/整目录暂存：$p" >&2; exit 2 ;;
  esac
done

# --- 2. 只暂存明确路径 ----------------------------------------------------
git add -A -- "${PATHSPEC[@]}" || { echo "[git_sync] ✗ 暂存失败" >&2; exit 1; }

STAGED="$(git diff --cached --name-only | wc -l | tr -d ' ')"
[ "$STAGED" -eq 0 ] && { echo "[git_sync] 指定路径无改动。"; exit 0; }

# --- 3. 体积检查 ----------------------------------------------------------
OVERSIZE="$(git diff --cached --name-only --diff-filter=AM \
  | while IFS= read -r f; do
      [ -f "$f" ] || continue
      sz="$(stat -c%s "$f" 2>/dev/null || echo 0)"
      [ "$sz" -gt $((SKIP_MB * 1048576)) ] && printf '%s\t%s\n' "$((sz / 1048576))MB" "$f"
    done)"
if [ -n "$OVERSIZE" ]; then
  echo "[git_sync] ✗ 以下文件超过 ${SKIP_MB}MB，不入库：" >&2
  printf '%s\n' "$OVERSIZE" | sed 's/^/    /' >&2
  printf '%s\n' "$OVERSIZE" | cut -f2- | while IFS= read -r f; do
    git reset -q HEAD -- "$f" 2>/dev/null || true
  done
  echo "  已从暂存区撤下。若确属证据数据，请登记到 .git/info/exclude 或改用 LFS。" >&2
  exit 1
fi

# --- 4. 敏感内容检查 ------------------------------------------------------
SENSITIVE="$(git diff --cached --name-only \
  | grep -Ei '(^|/)\.env$|id_rsa|\.(pem|key|p12|keystore)$|/sources/.*\.pdf$|_received_/.*\.pdf$' || true)"
if [ -n "$SENSITIVE" ]; then
  echo "[git_sync] ✗ 疑似凭据或他人版权原文：" >&2
  printf '%s\n' "$SENSITIVE" | sed 's/^/    /' >&2
  printf '%s\n' "$SENSITIVE" | while IFS= read -r f; do git reset -q HEAD -- "$f" 2>/dev/null || true; done
  exit 1
fi

# --- 5. 空白/冲突标记检查 -------------------------------------------------
if ! git diff --cached --check >/tmp/gitsync_check.$$ 2>&1; then
  echo "[git_sync] ⚠ git diff --cached --check 报告问题（空白错误/冲突标记）：" >&2
  head -10 /tmp/gitsync_check.$$ | sed 's/^/    /' >&2
  rm -f /tmp/gitsync_check.$$
  exit 1
fi
rm -f /tmp/gitsync_check.$$

# --- 6. 预览 --------------------------------------------------------------
echo "[git_sync] 分支 $BRANCH ｜ 待提交 $STAGED 个文件"
git diff --cached --stat | tail -1
if [ "$DRY_RUN" -eq 1 ]; then
  git diff --cached --stat | head -25
  echo "[git_sync] 预览模式，未提交。"
  exit 0
fi

# --- 7. 提交 --------------------------------------------------------------
if [ -z "$COMMIT_MSG" ]; then
  echo "[git_sync] ✗ 必须用 -m 给出单一目的的提交说明（AGENTS.md §6.1）。" >&2
  exit 2
fi
git commit -q -m "$COMMIT_MSG" || { echo "[git_sync] ✗ 提交失败" >&2; exit 1; }
LOCAL_SHA="$(git rev-parse HEAD)"
echo "[git_sync] ✓ 已提交 $(git log -1 --format='%h %s')"
[ "$NO_PUSH" -eq 1 ] && { echo "[git_sync] -r 指定不推送，结束。"; exit 0; }

# --- 8. 推送并核验 --------------------------------------------------------
echo "[git_sync] 推送 $PUSH_REMOTE/$TARGET_BRANCH ..."
if ! git push "$PUSH_REMOTE" "$TARGET_BRANCH"; then
  echo "[git_sync] ✗ 推送失败；提交仅在本地：$LOCAL_SHA" >&2
  exit 1
fi

REMOTE_SHA="$(git ls-remote "$PUSH_REMOTE" "refs/heads/$TARGET_BRANCH" | cut -f1)"
if [ "$REMOTE_SHA" = "$LOCAL_SHA" ]; then
  echo "[git_sync] ✓ 远端核验通过：$PUSH_REMOTE/$TARGET_BRANCH = $LOCAL_SHA"
  BAD="$(git diff-tree --no-commit-id --name-only -r HEAD \
    | while IFS= read -r f; do
        [ -f "$f" ] || continue
        [ "$(git hash-object "$f")" = "$(git rev-parse "HEAD:$f" 2>/dev/null)" ] || echo "$f"
      done)"
  [ -z "$BAD" ] && echo "[git_sync] ✓ 本次文件 blob 与工作区一致" || { echo "[git_sync] ⚠ blob 不一致：" >&2; printf '%s\n' "$BAD" >&2; }
else
  echo "[git_sync] ✗ 远端核验失败：远端=$REMOTE_SHA 本地=$LOCAL_SHA（只报本地提交完成）" >&2
  exit 1
fi

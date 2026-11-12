#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# git_sync.sh — 一条命令完成「提交 + 推送」，让 SIM240 仓库保持活跃
#
# 用法：
#   tools/git_sync.sh                       # 提交当前所有改动并推送
#   tools/git_sync.sh -m "feat: xxx"        # 自定义提交信息
#   tools/git_sync.sh -n                    # 只预览，不提交不推送
#   tools/git_sync.sh docs/ CASE/           # 只提交指定路径
#   SKIP_MB=20 tools/git_sync.sh            # 临时放宽单文件体积上限
#   STRICT=1 tools/git_sync.sh              # 遇到大文件直接报错退出（CI/严格模式）
#
# 数据策略（与 .gitignore 配套）：
#   文本 / 代码 / 配置 / 报告 / 小图  → 入库
#   网格、场数据、体数据、原始转储、媒体 → 不入库
#   体积超过 SKIP_MB（默认 5MB）的文件会被自动登记进 .git/info/exclude
#   （仅本机生效，不会污染仓库），避免每次都重新冒出来挡住提交。
#
# 推送目标固定为 remote `sim240`：origin 指向导师的只读仓库，
# 其 pushurl 被显式置为 DISABLED_READONLY，防止误推。
# ---------------------------------------------------------------------------
set -uo pipefail

SKIP_MB="${SKIP_MB:-5}"
STRICT="${STRICT:-0}"
PUSH_REMOTE="${PUSH_REMOTE:-sim240}"
DRY_RUN=0
COMMIT_MSG=""

while getopts ":m:nh" opt; do
  case "$opt" in
    m) COMMIT_MSG="$OPTARG" ;;
    n) DRY_RUN=1 ;;
    h) sed -n '2,26p' "$0"; exit 0 ;;
    *) echo "未知参数: -$OPTARG" >&2; exit 2 ;;
  esac
done
shift $((OPTIND - 1))
PATHSPEC=("$@")

cd "$(git rev-parse --show-toplevel)" || exit 3
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
EXCLUDE_FILE=".git/info/exclude"

# --- 1. 暂存 --------------------------------------------------------------
if [ ${#PATHSPEC[@]} -gt 0 ]; then
  git add -A -- "${PATHSPEC[@]}"
else
  git add -A
fi

# --- 2. 体积策略：超限文件从暂存区撤下，并登记到本地 exclude -------------
OVERSIZE="$(git diff --cached --name-only --diff-filter=AM \
  | while IFS= read -r f; do
      [ -f "$f" ] || continue
      sz="$(stat -c%s "$f" 2>/dev/null || echo 0)"
      if [ "$sz" -gt $((SKIP_MB * 1048576)) ]; then
        printf '%s\t%s\n' "$((sz / 1048576))MB" "$f"
      fi
    done)"

if [ -n "$OVERSIZE" ]; then
  if [ "$STRICT" = "1" ]; then
    echo "[git_sync] ✗ 以下文件超过 ${SKIP_MB}MB（STRICT 模式，拒绝提交）：" >&2
    echo "$OVERSIZE" >&2
    exit 1
  fi
  echo "[git_sync] ⚠ 跳过 ${SKIP_MB}MB 以上的大文件（已登记到 $EXCLUDE_FILE，之后不再重复提示）："
  printf '%s\n' "$OVERSIZE" | sed 's/^/    /'
  printf '%s\n' "$OVERSIZE" | cut -f2- | while IFS= read -r f; do
    esc="$(printf '%s' "$f" | sed 's/[][*?\\]/\\&/g')"
    grep -qxF "/$esc" "$EXCLUDE_FILE" 2>/dev/null || echo "/$esc" >> "$EXCLUDE_FILE"
  done
  printf '%s\n' "$OVERSIZE" | cut -f2- | while IFS= read -r f; do
    git reset -q HEAD -- "$f" 2>/dev/null || true
  done
fi

STAGED="$(git diff --cached --name-only | wc -l | tr -d ' ')"
if [ "$STAGED" -eq 0 ]; then
  echo "[git_sync] 没有需要提交的改动（大文件已全部忽略），工作区干净。"
  exit 0
fi

# --- 3. 敏感内容守卫 ------------------------------------------------------
SENSITIVE="$(git diff --cached --name-only \
  | grep -Ei '(^|/)\.env$|id_rsa|\.(pem|key|p12|keystore)$|_received_/.*sources/|/sources/.*\.pdf$' || true)"
if [ -n "$SENSITIVE" ]; then
  echo "[git_sync] ✗ 以下文件疑似凭据或他人版权原文，已阻止提交：" >&2
  echo "$SENSITIVE" >&2
  exit 1
fi

# --- 4. 预览 --------------------------------------------------------------
echo "[git_sync] 分支 $BRANCH ｜ 待提交 $STAGED 个文件"
git diff --cached --stat | tail -1
if [ "$DRY_RUN" -eq 1 ]; then
  echo "[git_sync] 预览模式，未提交、未推送。前 20 条："
  git diff --cached --name-status | head -20
  exit 0
fi

# --- 5. 提交 --------------------------------------------------------------
if [ -z "$COMMIT_MSG" ]; then
  AREAS="$(git diff --cached --name-only | cut -d/ -f1 | sort -u | paste -sd ',' -)"
  COMMIT_MSG="chore(sync): $(date '+%Y-%m-%d %H:%M') 同步 $STAGED 个文件（$AREAS）"
fi
git commit -q -m "$COMMIT_MSG" || { echo "[git_sync] ✗ 提交失败" >&2; exit 1; }
echo "[git_sync] ✓ 已提交 $(git log -1 --format='%h %s')"

# --- 6. 推送 --------------------------------------------------------------
echo "[git_sync] 推送到 $PUSH_REMOTE/$BRANCH ..."
if git push "$PUSH_REMOTE" "$BRANCH"; then
  echo "[git_sync] ✓ 推送完成，远端最新：$(git log -1 --format='%h %ci')"
else
  echo "[git_sync] ✗ 推送失败，提交已在本地，可稍后重试：git push $PUSH_REMOTE $BRANCH" >&2
  exit 1
fi

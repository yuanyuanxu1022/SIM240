#!/usr/bin/env bash
# User-started authentication only. This script never uploads files.
set -euo pipefail
umask 077
SIM240_GH_BIN=$(command -v gh)

SIM240_AUTH_DIR=/home/dell/.local/share/sim240-github-auth/new-share-20261027
mkdir -p "$SIM240_AUTH_DIR"
chmod 700 "$SIM240_AUTH_DIR"
export GH_CONFIG_DIR="$SIM240_AUTH_DIR"
export GIT_CONFIG_GLOBAL="$SIM240_AUTH_DIR/gitconfig"
export GIT_CONFIG_NOSYSTEM=1
unset GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN

printf '%s\n' '请在 GitHub 网页使用新仓库所有者账号 25yuanyuanxu-source 完成授权。'
"$SIM240_GH_BIN" auth login --hostname github.com --git-protocol https --web
SIM240_LOGIN_USER=$("$SIM240_GH_BIN" api user --jq .login)
printf '已登录账号：%s\n' "$SIM240_LOGIN_USER"
if [[ "$SIM240_LOGIN_USER" != '25yuanyuanxu-source' ]]; then
  printf '%s\n' '登录的不是指定新账号，已停止。没有上传文件。'
  exit 3
fi
printf '%s\n' '新账号授权完成，尚未上传。请回复 Codex：新账号授权完成。'

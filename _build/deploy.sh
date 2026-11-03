#!/bin/bash
# 길된교회 사이트 배포 — 페이지를 새로 만들고 GitHub Pages에 올린다.
#
#   bash _build/deploy.sh "바뀐 내용 한 줄 설명"
#
# 원본(이 폴더)은 옵시디언/아이클라우드에 두고, 배포용 git 저장소는
# 아이클라우드 밖(~/.gdnj/site)에 둔다. 접속 키와 설정도 ~/.gdnj 에 있다.
set -e

SRC="$(cd "$(dirname "$0")/.." && pwd)"
HOME_DIR="$HOME/.gdnj"
REPO="$HOME_DIR/site"
KEY="$HOME_DIR/deploy_key"
CONF="$HOME_DIR/config"

[ -f "$CONF" ] || { echo "설정 파일이 없습니다: $CONF"; exit 1; }
source "$CONF"   # GH_USER, GH_REPO
[ -n "$GH_USER" ] && [ -n "$GH_REPO" ] || { echo "config에 GH_USER, GH_REPO를 적어주세요."; exit 1; }

export GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=$HOME_DIR/known_hosts"
REMOTE="git@github.com:$GH_USER/$GH_REPO.git"
GIT_ID=(-c "user.name=$GH_USER" -c "user.email=${GH_EMAIL:-$GH_USER@users.noreply.github.com}")

echo "· 페이지 만드는 중…"
python3 "$SRC/_build/build.py"

if [ ! -d "$REPO/.git" ]; then
  mkdir -p "$REPO" && git -C "$REPO" init -q -b main
fi
git -C "$REPO" remote get-url origin >/dev/null 2>&1 || git -C "$REPO" remote add origin "$REMOTE"
git -C "$REPO" remote set-url origin "$REMOTE"
# 원격에 먼저 올라간 변경(자동 업데이트 등)이 있으면 받아온다
if git -C "$REPO" ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
  git -C "$REPO" fetch -q origin main
  git -C "$REPO" reset -q --soft origin/main 2>/dev/null || true
fi

echo "· 파일 복사 중…"
# _build(빌드 재료)도 함께 올린다 — GitHub Actions가 서버에서 혼자 빌드할 수 있게.
rsync -a --delete --exclude ".git" --exclude ".DS_Store" --exclude "*.md" "$SRC/" "$REPO/"
touch "$REPO/.nojekyll"

cd "$REPO"
git add -A
if git diff --cached --quiet; then
  echo "바뀐 내용이 없어서 올리지 않았습니다."
  exit 0
fi
git "${GIT_ID[@]}" commit -q -m "${1:-사이트 업데이트}" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
echo "· GitHub에 올리는 중…"
git push -q -u origin main
echo "✓ 배포 완료: https://$GH_USER.github.io/$GH_REPO/  (반영까지 1~2분 걸릴 수 있습니다)"

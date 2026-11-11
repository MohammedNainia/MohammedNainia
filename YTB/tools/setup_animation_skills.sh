#!/usr/bin/env bash
# Re-installs artemnovitckii/claude-animation-skills in a fresh cloud session (Linux).
# Same as its install.sh, except: no Playwright browser download (the session has one) and GSAP comes from npm (cdnjs is blocked here).
set -euo pipefail
DIR=/home/user/claude-animation-skills
[ -d "$DIR" ] || git clone -q --depth 1 https://github.com/artemnovitckii/claude-animation-skills.git "$DIR"
(cd "$DIR/kit" && PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install --silent --no-audit --no-fund)
mkdir -p "$DIR/kit/vendor"
if [ ! -s "$DIR/kit/vendor/gsap.min.js" ]; then
  T=$(mktemp -d); (cd "$T" && npm pack gsap@3.12.5 --silent >/dev/null && tar xzf gsap-3.12.5.tgz && cp package/dist/gsap.min.js "$DIR/kit/vendor/"); rm -rf "$T"
fi
npx --yes hyperframes@0.8.34 --version >/dev/null 2>&1 || true
mkdir -p ~/.claude/skills
for d in "$DIR"/skills/*/; do ln -sfn "${d%/}" ~/.claude/skills/"$(basename "$d")"; done
echo "animation skills ready: graph, map-route, minimalistic-graphics, breakdown, stick-figure, zach-d-films"

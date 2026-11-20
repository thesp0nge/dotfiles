#!/usr/bin/env bash
set -euo pipefail
bundle_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cd "$bundle_dir"
python3 -m unittest discover -s tests -v
python3 -m py_compile colorscheme.py install.py render.py
if command -v zsh >/dev/null; then zsh -n hooks/zsh.zsh; fi
python3 install.py "$@"

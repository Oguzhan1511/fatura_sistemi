#!/bin/zsh
# ERP'den bağımsız yerel test ortamını başlatır.
cd -- "$(dirname -- "$0")" || exit 1
python3 start_local.py --lab --open

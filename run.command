#!/usr/bin/env bash
# =====================================================================
#  File cho macOS: double-click trong Finder de chay ung dung.
#  (Thuc chat goi lai run.sh trong cung thu muc.)
#
#  Lan dau, neu bao "khong the mo do nha phat trien khong xac dinh",
#  vao System Settings > Privacy & Security > bam "Open Anyway",
#  hoac chay: chmod +x run.command  roi mo lai.
# =====================================================================
cd "$(dirname "$0")" || exit 1
exec bash ./run.sh

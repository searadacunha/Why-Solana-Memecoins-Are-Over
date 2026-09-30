#!/bin/sh
# Chains the collection: windows (retrying failures once), then wallets and funding hops.
# Keys come from the untracked .helius_keys file, through the environment only.
cd "$(dirname "$0")/../.." || exit 1
HELIUS_API_KEYS=$(cat post_detection_forensics/.helius_keys); export HELIUS_API_KEYS
LOG=post_detection_forensics/data/onchain_cache
if [ -n "$1" ]; then while kill -0 "$1" 2>/dev/null; do sleep 30; done; fi
python3 post_detection_forensics/code/col_10_windows.py >> $LOG/col_10.log 2>&1
python3 post_detection_forensics/code/col_10_windows.py >> $LOG/col_10.log 2>&1
python3 post_detection_forensics/code/col_20_wallets.py >> $LOG/col_20.log 2>&1
python3 post_detection_forensics/code/col_20_wallets.py >> $LOG/col_20.log 2>&1
echo "COLLECTION FINISHED $(date -u)" >> $LOG/col_20.log

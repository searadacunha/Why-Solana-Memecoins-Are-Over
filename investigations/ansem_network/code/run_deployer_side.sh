#!/bin/zsh
# Rest of the deployer's history, then its treasuries over 2026. All resume from checkpoints.
export PYTHONDONTWRITEBYTECODE=1
PY=~/.local/share/forensics_v2/venv/bin/python
$PY col_03_stream.py 1700 17000 yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe
for a in FkCcgvCoR6p6BRucCnU1t1DXP97Y3rJeMYBiU1o31nuv F5XqYtdUWUT7bbuuKEjckDs8Hwk7j7mhdwGe3YKn5Xf7 AvYukzeAFzFo66i1GJHShcdBbb4jeSkZiEJnNMds54mo 9bxyzm6MFn3TWEedvYuMzSaZkkGWKSyTgWpRXCzMP3dm 4qcD8iSFLC5VDZphBtM7pSeevtHtD8Chi7Zmhcm9TvHm E94dd6pnFhE7LNbC7oSbyWmCCQ9kNoEhSa6cKN6brSAm; do
  $PY col_06_windows.py $a "2026-03-01 00:00:00" "2026-11-03 00:00:00" 150 1600
done

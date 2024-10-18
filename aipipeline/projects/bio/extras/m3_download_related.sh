#!/bin/bash
# set -x
time conda run -n m3-download  m3-download generate \
--exclude-group 'ROV:pending-verifications' \
--exclude-activity 'unspecified' \
--exclude-project 'ML-Tracking' \
/mnt/ML_SCRATCH/M3/Baseline/images /mnt/ML_SCRATCH/M3/Baseline/xml
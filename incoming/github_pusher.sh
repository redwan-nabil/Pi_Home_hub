#!/bin/bash
cd /home/redwannabil/portfolio_staging
if [ -n "$(git status --porcelain)" ]; then
    git add .
    git commit -m "Auto-Staged new raw scripts"
    git push origin main
fi

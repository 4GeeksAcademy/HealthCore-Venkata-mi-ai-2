#!/bin/sh
set -e
cd /workspace/uis/healthcore
npm run dev -- --hostname 0.0.0.0 --port 3000 &
cd /workspace/uis/backoffice
npm run dev -- --hostname 0.0.0.0 --port 3001 &
wait

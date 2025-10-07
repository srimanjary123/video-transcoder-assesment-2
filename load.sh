#!/usr/bin/env bash
set -euo pipefail

BASE="http://ec2-13-55-66-77.ap-southeast-2.compute.amazonaws.com:8080/api/v1"
USER="alice"
PASS="password1"
FILE="sample.mp4"     # keep a small mp4 next to this script
RES="720p"
CONCURRENCY=4
ROUNDS=30

echo "[1/4] Login"
TOKEN=$(curl -s -X POST "$BASE/login" -H "Content-Type: application/json" \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" | jq -r .token)
if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then echo "Login failed"; exit 1; fi

echo "[2/4] Upload (once)"
VID=$(curl -s -X POST "$BASE/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@${FILE}" | jq -r .video_id)
if [[ -z "${VID}" || "${VID}" == "null" ]]; then echo "Upload failed"; exit 1; fi
echo "VID=$VID"

echo "[3/4] Hammer /transcode"
for ((r=1; r<=ROUNDS; r++)); do
  echo "Round $r"
  pids=()
  for ((i=1; i<=CONCURRENCY; i++)); do
    curl -s -X POST "$BASE/transcode" \
      -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
      -d "{\"video_id\":\"$VID\",\"resolution\":\"$RES\",\"replace_old\":true}" >/dev/null &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait $p; done
done
echo "[4/4] Done"

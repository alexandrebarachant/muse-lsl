#!/usr/bin/env bash
# Start Muse LSL stream and EEG viewer in one command.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
export PYTHONUNBUFFERED=1

MUSE_NAME="${1:-}"
MUSE_ADDRESS="${2:-}"
STREAM_ARGS=(--retries 5)

# Prefer name so each run re-scans for a fresh BLE address on macOS.
if [[ -n "$MUSE_NAME" ]]; then
  STREAM_ARGS+=(--name "$MUSE_NAME")
elif [[ -n "$MUSE_ADDRESS" ]]; then
  STREAM_ARGS+=(--address "$MUSE_ADDRESS")
fi

cleanup() {
  rm -f "${STREAM_LOG:-}"
  if [[ -n "${STREAM_PID:-}" ]] && kill -0 "$STREAM_PID" 2>/dev/null; then
    kill "$STREAM_PID" 2>/dev/null || true
    wait "$STREAM_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

STREAM_LOG="$(mktemp)"
START_TS=$(date +%s)
echo "[$(date +%H:%M:%S)] Starting Muse LSL stream (BLE can take 30-90s with retries)..."
python3 -u -m muselsl stream "${STREAM_ARGS[@]}" > >(tee "$STREAM_LOG") 2>&1 &
STREAM_PID=$!

echo ""
connected=false
for i in $(seq 1 120); do
  if grep -q "Streaming" "$STREAM_LOG" 2>/dev/null; then
    connected=true
    break
  fi
  if grep -q "Failed to connect to Muse\|Traceback" "$STREAM_LOG" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] Stream failed after $(( $(date +%s) - START_TS ))s"
    wait "$STREAM_PID" 2>/dev/null || true
    exit 1
  fi
  if ! kill -0 "$STREAM_PID" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] Stream exited after $(( $(date +%s) - START_TS ))s"
    if grep -q "Disconnected" "$STREAM_LOG" 2>/dev/null; then
      echo "Stream disconnected — wear the headband so EEG sensors make skin contact."
    fi
    wait "$STREAM_PID" 2>/dev/null || true
    exit 1
  fi
  if (( i % 10 == 0 )); then
    elapsed=$(( $(date +%s) - START_TS ))
    status=""
    if grep -q "BLE connected" "$STREAM_LOG" 2>/dev/null; then
      status=" — BLE linked, setting up sensors"
    elif grep -q "Connecting to" "$STREAM_LOG" 2>/dev/null; then
      status=" — still trying BLE handshake"
    fi
    echo "[$(date +%H:%M:%S)] Still waiting... ${elapsed}s elapsed${status} — headband on, phone BT off"
  fi
  sleep 1
done

if [[ "$connected" != true ]]; then
  echo "[$(date +%H:%M:%S)] Timed out after $(( $(date +%s) - START_TS ))s. Power-cycle Muse and run again immediately."
  kill "$STREAM_PID" 2>/dev/null || true
  exit 1
fi

if ! kill -0 "$STREAM_PID" 2>/dev/null; then
  echo "[$(date +%H:%M:%S)] Stream ended before viewer opened — wear the headband and try again."
  exit 1
fi

echo ""
echo "[$(date +%H:%M:%S)] Opening EEG viewer — close the window to stop."
muselsl view --backend MacOSX

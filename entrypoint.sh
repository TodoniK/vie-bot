#!/bin/bash
set -e

INTERVAL=${CHECK_INTERVAL:-60}

cleanup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Arrêt du bot VIE..."
    kill "$CHILD_PID" 2>/dev/null
    exit 0
}

trap cleanup SIGTERM SIGINT

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Démarrage du bot VIE (intervalle: ${INTERVAL}s)"

while true; do
    python3 /app/vie.py || echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERREUR] vie.py a échoué, nouvelle tentative dans ${INTERVAL}s"
    sleep "$INTERVAL" &
    CHILD_PID=$!
    wait "$CHILD_PID"
done

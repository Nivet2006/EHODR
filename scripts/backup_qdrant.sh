#!/usr/bin/env bash
# ==============================================================================
# UAMS Qdrant Vector Collection Snapshot Backup Script.
# Schedule via cron to run nightly: 0 2 * * * /app/scripts/backup_qdrant.sh
# ==============================================================================

set -euo pipefail

# 1. Load Configurations with standard defaults
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_HTTP_PORT:-6333}"
COLLECTION_NAME="${QDRANT_COLLECTION:-ai_memories}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/qdrant_backups}"

echo "Starting automated vector collection backup sequence..."
echo "Target Collection: ${COLLECTION_NAME}"
echo "Server Endpoint:   http://${QDRANT_HOST}:${QDRANT_PORT}"

# Ensure output path exists
mkdir -p "${BACKUP_DIR}"

# 2. Trigger Qdrant REST snapshot API
# Verify snapshot API endpoint at: https://qdrant.tech/documentation/concepts/snapshots/
API_ENDPOINT="http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${COLLECTION_NAME}/snapshots"

echo "Requesting database cluster to generate collection snapshot..."
RESPONSE=$(curl -s -X POST "${API_ENDPOINT}")

# Extract snapshot filename and status using simple python json parsing (ensures zero external tools like jq needed)
SNAPSHOT_NAME=$(python3 -c "import sys, json; print(json.loads(sys.stdin.read())['result']['name'])" <<< "${RESPONSE}")

if [ -n "${SNAPSHOT_NAME}" ]; then
    echo "✅ Snapshot created successfully: ${SNAPSHOT_NAME}"
    
    # 3. Pull snapshot file down to local backup disk
    DOWNLOAD_URL="${API_ENDPOINT}/${SNAPSHOT_NAME}"
    OUTPUT_FILE="${BACKUP_DIR}/${SNAPSHOT_NAME}"
    
    echo "Downloading snapshot file to: ${OUTPUT_FILE}..."
    curl -s -o "${OUTPUT_FILE}" "${DOWNLOAD_URL}"
    echo "✅ Download complete."
    
    # 4. Optional cloud syncing (S3 / GCS integration example)
    # echo "Syncing snapshot file to AWS S3 bucket..."
    # aws s3 cp "${OUTPUT_FILE}" "s3://my-company-uams-backups/qdrant/${SNAPSHOT_NAME}"
    
    # 5. Enforce 7-day retention policy locally to prevent disk saturation
    echo "Cleaning local snapshots older than 7 days..."
    find "${BACKUP_DIR}" -name "*.snapshot" -type f -mtime +7 -delete
    echo "✅ Local purge cycle completed."
else
    echo "❌ Qdrant Snapshot API failed to return a valid snapshot name!"
    echo "Response payload: ${RESPONSE}"
    exit 1
fi

echo "=============================================================================="
echo "UAMS Qdrant Vector Collection Backup Completed Successfully."
echo "=============================================================================="

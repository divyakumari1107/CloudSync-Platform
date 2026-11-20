import os
import time
import datetime
import random
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

PORT = int(os.environ.get("PORT", 7003))
AWS_NODE_URL = os.environ.get("AWS_NODE_URL", "http://aws_node:7001")
AZURE_NODE_URL = os.environ.get("AZURE_NODE_URL", "http://azure_node:7002")

SYNC_LOGS = [
    {
        "sync_id": "sync-9082",
        "source": "s3://cloudsync-primary-vault",
        "target": "azure://cloudsyncvaultbackup/cloudsync-backup-vault",
        "objects_replicated": 3,
        "bytes_transferred": 137467904,
        "duration_seconds": 1.4,
        "status": "COMPLETED",
        "rpo_lag_ms": 110,
        "timestamp": (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)).isoformat()
    }
]

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "HEALTHY",
        "service": "cloudsync-replication-daemon",
        "engine": "Ansible Synchronize Module / Multi-Cloud Storage Bridge",
        "sync_interval_seconds": 15,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/sync/status", methods=["GET"])
def sync_status():
    return jsonify({
        "status": "ACTIVE_SYNCHRONIZED",
        "rpo_seconds": "< 1s",
        "rto_target_seconds": "< 30s",
        "last_sync": SYNC_LOGS[0]["timestamp"] if SYNC_LOGS else None,
        "total_sync_runs": len(SYNC_LOGS),
        "history": SYNC_LOGS[:10]
    }), 200

@app.route("/api/sync/trigger", methods=["POST"])
def trigger_sync():
    sync_id = f"sync-{random.randint(1000, 9999)}"
    
    # Generate new object on AWS S3 and mirror to Azure
    new_filename = f"transaction_audit_log_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    size = random.randint(50000, 2500000)
    
    try:
        requests.post(f"{AWS_NODE_URL}/api/storage/objects", json={"key": new_filename, "size_bytes": size}, timeout=3)
    except Exception:
        pass

    try:
        requests.post(f"{AZURE_NODE_URL}/api/storage/objects", json={"name": new_filename, "size_bytes": size}, timeout=3)
    except Exception:
        pass

    log_entry = {
        "sync_id": sync_id,
        "source": "s3://cloudsync-primary-vault",
        "target": "azure://cloudsyncvaultbackup/cloudsync-backup-vault",
        "objects_replicated": 1,
        "bytes_transferred": size,
        "duration_seconds": round(random.uniform(0.4, 1.2), 2),
        "status": "COMPLETED",
        "rpo_lag_ms": random.randint(70, 180),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    SYNC_LOGS.insert(0, log_entry)

    return jsonify({
        "message": "Continuous Cross-Cloud Replication executed via Ansible sync engine",
        "sync_event": log_entry
    }), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

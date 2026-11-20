import os
import time
import datetime
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

PORT = int(os.environ.get("PORT", 7002))
START_TIME = datetime.datetime.utcnow()
ROLE = "SECONDARY_STANDBY"  # changes to "PROMOTED_ACTIVE" upon failover

AZURE_BLOB_VAULT = [
    {"name": "customer_database_dump_20261120.sql.gz", "size_bytes": 104857600, "etag": "0x8DC8B234F9", "synced_from": "s3://cloudsync-primary-vault", "replication_lag_ms": 140, "last_replicated": datetime.datetime.utcnow().isoformat()},
    {"name": "product_catalog_index.parquet", "size_bytes": 28416000, "etag": "0x8DC8B234F0", "synced_from": "s3://cloudsync-primary-vault", "replication_lag_ms": 180, "last_replicated": datetime.datetime.utcnow().isoformat()},
    {"name": "auth_identity_tokens_backup.enc", "size_bytes": 4194304, "etag": "0x8DC8B234FA", "synced_from": "s3://cloudsync-primary-vault", "replication_lag_ms": 95, "last_replicated": datetime.datetime.utcnow().isoformat()}
]

@app.route("/health", methods=["GET"])
def health():
    uptime = str(datetime.datetime.utcnow() - START_TIME).split(".")[0]
    return jsonify({
        "status": "HEALTHY",
        "provider": "Microsoft Azure",
        "vm_name": "vm-cloudsync-azure-standby",
        "vm_size": "Standard_B2s",
        "region": "East US 2",
        "role": ROLE,
        "is_active_serving": (ROLE == "PROMOTED_ACTIVE"),
        "uptime": uptime,
        "cpu_percentage": round(random.uniform(4.0, 12.0) if ROLE == "SECONDARY_STANDBY" else random.uniform(35.0, 65.0), 1),
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/storage/objects", methods=["GET", "POST"])
def storage_objects():
    if request.method == "POST":
        data = request.json or {}
        new_blob = {
            "name": data.get("name", f"replicated_blob_{int(time.time())}.dat"),
            "size_bytes": data.get("size_bytes", random.randint(10240, 5242880)),
            "etag": f"0x8DC{hex(random.randint(0x100000, 0xFFFFFF))[2:].upper()}",
            "synced_from": "s3://cloudsync-primary-vault",
            "replication_lag_ms": random.randint(80, 220),
            "last_replicated": datetime.datetime.utcnow().isoformat()
        }
        AZURE_BLOB_VAULT.insert(0, new_blob)
        return jsonify({"message": "Blob replica written to Azure Storage", "blob": new_blob, "container": "cloudsync-backup-vault"}), 201

    return jsonify({
        "storage_account": "cloudsyncvaultbackup",
        "container": "cloudsync-backup-vault",
        "region": "East US 2",
        "objects": AZURE_BLOB_VAULT,
        "total_count": len(AZURE_BLOB_VAULT),
        "total_size_mb": round(sum(b["size_bytes"] for b in AZURE_BLOB_VAULT) / (1024 * 1024), 2)
    }), 200

@app.route("/api/metrics/azure_monitor", methods=["GET"])
def azure_monitor_metrics():
    return jsonify({
        "resource_group": "rg-cloudsync-production",
        "resource_id": "/subscriptions/sub-id/resourceGroups/rg-cloudsync-production/providers/Microsoft.Compute/virtualMachines/vm-cloudsync-azure-standby",
        "metrics": {
            "Percentage_CPU": round(random.uniform(5.1, 14.2) if ROLE == "SECONDARY_STANDBY" else random.uniform(45.0, 72.0), 2),
            "NetworkIn_Bytes": random.randint(45000, 180000),
            "NetworkOut_Bytes": random.randint(25000, 120000),
            "DiskReadBytesSec": random.randint(1024, 8192),
            "ReplicationLag_ms": random.randint(65, 190)
        },
        "alert_status": "MONITORING_WARM_STANDBY" if ROLE == "SECONDARY_STANDBY" else "ALERT_ACTIVE_PROMOTED",
        "last_sync": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/failover/promote", methods=["POST"])
def promote_to_primary():
    global ROLE
    ROLE = "PROMOTED_ACTIVE"
    return jsonify({
        "status": "SUCCESS",
        "role": ROLE,
        "message": "Azure VM promoted to ACTIVE PRIMARY node. Failover completed in 820ms."
    }), 200

@app.route("/api/failover/demote", methods=["POST"])
def demote_to_standby():
    global ROLE
    ROLE = "SECONDARY_STANDBY"
    return jsonify({
        "status": "SUCCESS",
        "role": ROLE,
        "message": "Azure VM returned to WARM STANDBY mode."
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

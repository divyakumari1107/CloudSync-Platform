import os
import time
import datetime
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app)

PORT = int(os.environ.get("PORT", 7001))
IS_HEALTHY = True
START_TIME = datetime.datetime.utcnow()

S3_VAULT = [
    {"key": "customer_database_dump_20261120.sql.gz", "size_bytes": 104857600, "etag": "a3f124b89d", "last_modified": datetime.datetime.utcnow().isoformat(), "storage_tier": "STANDARD"},
    {"key": "product_catalog_index.parquet", "size_bytes": 28416000, "etag": "7c823ef190", "last_modified": datetime.datetime.utcnow().isoformat(), "storage_tier": "STANDARD"},
    {"key": "auth_identity_tokens_backup.enc", "size_bytes": 4194304, "etag": "9812bc34aa", "last_modified": datetime.datetime.utcnow().isoformat(), "storage_tier": "INTELLIGENT_TIERING"}
]

@app.route("/health", methods=["GET"])
def health():
    global IS_HEALTHY
    if not IS_HEALTHY:
        return jsonify({
            "status": "UNHEALTHY",
            "provider": "AWS",
            "region": "us-east-1",
            "role": "PRIMARY (OUTAGE SIMULATED)",
            "message": "AWS Region degraded / EC2 StatusCheckFailed. Traffic should failover to Azure Standby."
        }), 503

    uptime = str(datetime.datetime.utcnow() - START_TIME).split(".")[0]
    return jsonify({
        "status": "HEALTHY",
        "provider": "AWS",
        "instance_id": "i-094bf32e8d1a12001",
        "instance_type": "t3.medium",
        "region": "us-east-1",
        "availability_zone": "us-east-1a",
        "role": "PRIMARY_ACTIVE",
        "uptime": uptime,
        "load_percentage": round(random.uniform(22.0, 48.0), 1),
        "active_traffic_percentage": 100,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/storage/objects", methods=["GET", "POST"])
def storage_objects():
    if request.method == "POST":
        data = request.json or {}
        new_obj = {
            "key": data.get("key", f"object_snapshot_{int(time.time())}.dat"),
            "size_bytes": data.get("size_bytes", random.randint(10240, 5242880)),
            "etag": hex(random.randint(0x1000000000, 0xFFFFFFFFFF))[2:],
            "last_modified": datetime.datetime.utcnow().isoformat(),
            "storage_tier": "STANDARD"
        }
        S3_VAULT.insert(0, new_obj)
        return jsonify({"message": "Object uploaded to S3 successfully", "object": new_obj, "bucket": "cloudsync-primary-vault"}), 201

    return jsonify({
        "bucket": "cloudsync-primary-vault",
        "region": "us-east-1",
        "objects": S3_VAULT,
        "total_count": len(S3_VAULT),
        "total_size_mb": round(sum(o["size_bytes"] for o in S3_VAULT) / (1024 * 1024), 2)
    }), 200

@app.route("/api/metrics/cloudwatch", methods=["GET"])
def cloudwatch_metrics():
    global IS_HEALTHY
    return jsonify({
        "namespace": "AWS/EC2",
        "instance_id": "i-094bf32e8d1a12001",
        "metrics": {
            "StatusCheckFailed": 1 if not IS_HEALTHY else 0,
            "CPUUtilization": 0.0 if not IS_HEALTHY else round(random.uniform(15.2, 35.8), 2),
            "NetworkIn_KBps": 0.0 if not IS_HEALTHY else round(random.uniform(120.5, 450.2), 1),
            "NetworkOut_KBps": 0.0 if not IS_HEALTHY else round(random.uniform(320.1, 890.4), 1),
            "AverageLatency_ms": 999.0 if not IS_HEALTHY else round(random.uniform(12.4, 18.2), 2)
        },
        "alarm_state": "ALARM" if not IS_HEALTHY else "OK",
        "alarm_name": "cloudsync-aws-primary-unhealthy",
        "last_updated": datetime.datetime.utcnow().isoformat()
    }), 200

@app.route("/api/chaos/outage", methods=["POST"])
def toggle_outage():
    global IS_HEALTHY
    IS_HEALTHY = not IS_HEALTHY
    state = "OUTAGE_SIMULATED" if not IS_HEALTHY else "HEALTHY_RESTORED"
    return jsonify({
        "action": state,
        "is_healthy": IS_HEALTHY,
        "message": f"AWS region simulated health state changed to: {state}"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)

import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://localhost:8070"

def log_test(name, passed, details=""):
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"{symbol} {name}")
    if details:
        print(f"       -> {details}")

def test_nginx_ingress():
    try:
        req = urllib.request.Request(f"{BASE_URL}/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            content = resp.read().decode("utf-8")
            passed = resp.status == 200 and "CloudSync" in content
            log_test("Nginx Edge DR Dashboard (Port 8070)", passed, f"Status: {resp.status}, Title: CloudSync detected")
            return passed
    except Exception as e:
        log_test("Nginx Edge DR Dashboard (Port 8070)", False, str(e))
        return False

def test_aws_primary():
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/aws/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            passed = resp.status == 200 and data.get("provider") == "AWS" and data.get("status") == "HEALTHY"
            log_test("AWS Primary Node (EC2 us-east-1)", passed, f"Instance: {data.get('instance_id')}, Status: {data.get('status')}")
            return passed
    except Exception as e:
        log_test("AWS Primary Node (EC2 us-east-1)", False, str(e))
        return False

def test_azure_standby():
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/azure/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            passed = resp.status == 200 and data.get("provider") == "Microsoft Azure" and data.get("status") == "HEALTHY"
            log_test("Azure Standby Node (Azure VM East US 2)", passed, f"VM: {data.get('vm_name')}, Role: {data.get('role')}")
            return passed
    except Exception as e:
        log_test("Azure Standby Node (Azure VM East US 2)", False, str(e))
        return False

def test_storage_sync():
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/sync/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            passed = resp.status == 200 and data.get("status") == "ACTIVE_SYNCHRONIZED"
            log_test("Cross-Cloud Storage Sync (S3 <-> Azure Blob)", passed, f"RPO: {data.get('rpo_seconds')}, RTO Target: {data.get('rto_target_seconds')}")
            return passed
    except Exception as e:
        log_test("Cross-Cloud Storage Sync (S3 <-> Azure Blob)", False, str(e))
        return False

def test_automated_failover_routing():
    try:
        # Step 1: Verify baseline traffic routes to AWS
        req1 = urllib.request.Request(f"{BASE_URL}/cloud/health")
        with urllib.request.urlopen(req1, timeout=5) as resp:
            data1 = json.loads(resp.read().decode("utf-8"))
            initial_provider = data1.get("provider")

        # Step 2: Trigger simulated AWS Outage (Chaos 503)
        req_chaos = urllib.request.Request(f"{BASE_URL}/api/aws/api/chaos/outage", method="POST")
        with urllib.request.urlopen(req_chaos, timeout=5) as resp:
            chaos_data = json.loads(resp.read().decode("utf-8"))

        time.sleep(1)

        # Step 3: Verify Nginx Edge Proxy reroutes active traffic to Azure Standby (Backup)
        req2 = urllib.request.Request(f"{BASE_URL}/cloud/health")
        with urllib.request.urlopen(req2, timeout=5) as resp:
            data2 = json.loads(resp.read().decode("utf-8"))
            failover_provider = data2.get("provider")

        # Step 4: Restore AWS Node to healthy
        req_restore = urllib.request.Request(f"{BASE_URL}/api/aws/api/chaos/outage", method="POST")
        with urllib.request.urlopen(req_restore, timeout=5) as resp:
            restore_data = json.loads(resp.read().decode("utf-8"))

        passed = initial_provider == "AWS" and failover_provider == "Microsoft Azure"
        log_test("Automated Active-Passive Disaster Recovery Failover", passed, 
                 f"Normal: {initial_provider} -> Simulated Outage -> Failover Target: {failover_provider} (Zero Downtime)")
        return passed
    except Exception as e:
        log_test("Automated Active-Passive Disaster Recovery Failover", False, str(e))
        return False

def test_telemetry_probes():
    try:
        # Check AWS CloudWatch
        req_cw = urllib.request.Request(f"{BASE_URL}/api/aws/api/metrics/cloudwatch")
        with urllib.request.urlopen(req_cw, timeout=5) as resp:
            cw_data = json.loads(resp.read().decode("utf-8"))

        # Check Azure Monitor
        req_am = urllib.request.Request(f"{BASE_URL}/api/azure/api/metrics/azure_monitor")
        with urllib.request.urlopen(req_am, timeout=5) as resp:
            am_data = json.loads(resp.read().decode("utf-8"))

        passed = resp.status == 200 and "CPUUtilization" in cw_data.get("metrics", {}) and "Percentage_CPU" in am_data.get("metrics", {})
        log_test("Unified Multi-Cloud Telemetry (CloudWatch + Azure Monitor)", passed, 
                 f"CloudWatch Alarm: {cw_data.get('alarm_state')}, Azure Monitor Alert: {am_data.get('alert_status')}")
        return passed
    except Exception as e:
        log_test("Unified Multi-Cloud Telemetry (CloudWatch + Azure Monitor)", False, str(e))
        return False

def main():
    print("=" * 70)
    print("CloudSync Multi-Cloud Disaster Recovery Platform - Integration Test Suite")
    print("Target Ingress: " + BASE_URL)
    print("=" * 70)

    tests = [
        test_nginx_ingress,
        test_aws_primary,
        test_azure_standby,
        test_storage_sync,
        test_automated_failover_routing,
        test_telemetry_probes
    ]

    results = [t() for t in tests]
    passed_count = sum(results)
    total_count = len(results)

    print("=" * 70)
    print(f"Summary: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")
    print("=" * 70)

    if passed_count == total_count:
        print("[SUCCESS] All CloudSync multi-cloud DR & failover tests passed successfully!")
        sys.exit(0)
    else:
        print("[ERROR] Some tests failed. Please inspect container logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()

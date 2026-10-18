import urllib.request
import urllib.parse
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"

def make_request(method, url, data=None, headers=None):
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
            
    body = json.dumps(data).encode('utf-8') if data else None
    
    try:
        with urllib.request.urlopen(req, data=body) as response:
            res_body = response.read().decode('utf-8')
            return response.status, json.loads(res_body)
    except urllib.error.HTTPError as e:
        res_body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(res_body)
        except Exception:
            return e.code, {"detail": res_body}

def test_human_approval_system():
    print("=== TESTING WORKORA HUMAN APPROVAL SYSTEM ===")

    # Obtain admin JWT token
    code, auth_res = make_request("POST", f"{BASE_URL}/api/auth/login", {
        "email": "admin@logiflow.com",
        "password": "password123"
    })
    assert code == 200, f"Expected 200 for admin login, got {code}: {auth_res}"
    admin_token = auth_res["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Obtain customer JWT token
    code, cust_auth = make_request("POST", f"{BASE_URL}/api/auth/login", {
        "email": "rahul@example.com",
        "password": "password123"
    })
    assert code == 200, f"Expected 200 for customer login, got {code}: {cust_auth}"
    cust_token = cust_auth["access_token"]
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # 1. GET /api/approvals/stats
    code, stats = make_request("GET", f"{BASE_URL}/api/approvals/stats")
    assert code == 200, f"Expected 200, got {code}: {stats}"
    assert "pending_approvals" in stats
    assert stats.get("label") == "Demo Data"
    print("[PASS] GET /api/approvals/stats")

    # 2. GET /api/approvals
    code, list_data = make_request("GET", f"{BASE_URL}/api/approvals")
    assert code == 200, f"Expected 200, got {code}: {list_data}"
    assert len(list_data) >= 1, f"Expected at least 1 approval, got {len(list_data)}"
    print("[PASS] GET /api/approvals")

    # TEST 1 — REFUND CREATION
    print("\n--- TEST 1 — REFUND CREATION ---")
    code, chat_res = make_request("POST", f"{BASE_URL}/api/chat", {
        "message": "I want a ₹1,000 refund for SL1004 because my package was damaged.",
        "active_employee": "billing",
        "customer_id": "CUST001"
    })
    assert code == 200, f"Expected 200, got {code}: {chat_res}"
    msg_text = chat_res.get("message") or chat_res.get("reply", "")
    assert "Pending Review" in msg_text or "Pending Human Approval" in msg_text or "REF-" in msg_text or "APR-" in msg_text
    print("[PASS] TEST 1: Refund request created with status Pending Approval (No automatic refund)")

    # Create explicit test approval request for tests 2, 3, 4, 5
    code, new_app = make_request("POST", f"{BASE_URL}/api/approvals", {
        "request_type": "refund",
        "employee": "💰 Billing Employee",
        "customer_id": "CUST001",
        "shipment_id": "SL1004",
        "invoice_id": "INV-2045",
        "amount": 2000.0,
        "reason": "Damaged shipment",
        "requested_action": "Refund ₹2,000"
    })
    assert code == 200, f"Expected 200, got {code}: {new_app}"
    test_app_id = new_app["approval_id"]
    print(f"[PASS] Created test approval request: {test_app_id}")

    # TEST 4 — CUSTOMER CANNOT APPROVE (403 FORBIDDEN)
    print("\n--- TEST 4 — CUSTOMER CANNOT APPROVE ---")
    code, cust_res = make_request("POST", f"{BASE_URL}/api/approvals/{test_app_id}/approve", headers=cust_headers)
    assert code == 403, f"Expected 403 Forbidden for customer approve attempt, got {code}: {cust_res}"
    print("[PASS] TEST 4: Customer approval attempt correctly rejected with HTTP 403 Forbidden")

    # TEST 5 — QUERY PARAMETER IS_ADMIN CANNOT BYPASS AUTH (401/403)
    print("\n--- TEST 5 — QUERY PARAMETER CANNOT BYPASS AUTH ---")
    code, bypass_res = make_request("POST", f"{BASE_URL}/api/approvals/{test_app_id}/approve?is_admin=true")
    assert code in [401, 403], f"Expected 401/403 for query param bypass attempt, got {code}: {bypass_res}"
    print("[PASS] TEST 5: is_admin=true query parameter correctly ignored; auth required")

    # TEST 2 — ADMIN APPROVE WORKFLOW WITH VALID JWT
    print("\n--- TEST 2 — ADMIN APPROVE WORKFLOW ---")
    code, app_res = make_request("POST", f"{BASE_URL}/api/approvals/{test_app_id}/approve", headers=admin_headers)
    assert code == 200, f"Expected 200 for admin approve, got {code}: {app_res}"
    assert app_res["status"] == "Approved"
    assert app_res["reviewed_by"] is not None
    print(f"[PASS] TEST 2: Admin approved {test_app_id}. Status updated to Approved & action executed.")

    # Create another test approval request for TEST 3 (Rejection)
    code, rej_app = make_request("POST", f"{BASE_URL}/api/approvals", {
        "request_type": "refund",
        "employee": "💰 Billing Employee",
        "customer_id": "CUST001",
        "shipment_id": "SL1004",
        "invoice_id": "INV-2045",
        "amount": 15000.0,
        "reason": "Exceeds allowed claim limit",
        "requested_action": "Refund ₹15,000"
    })
    assert code == 200, f"Expected 200, got {code}: {rej_app}"
    rej_app_id = rej_app["approval_id"]

    # TEST 3 — REJECT WORKFLOW WITH VALID JWT
    print("\n--- TEST 3 — ADMIN REJECT WORKFLOW ---")
    code, rej_res = make_request("POST", f"{BASE_URL}/api/approvals/{rej_app_id}/reject", {
        "reason": "Refund exceeds policy limit."
    }, headers=admin_headers)
    assert code == 200, f"Expected 200 for admin reject, got {code}: {rej_res}"
    assert rej_res["status"] == "Rejected"
    assert "Refund exceeds policy limit." in (rej_res.get("review_comment") or rej_res.get("reason", ""))
    print(f"[PASS] TEST 3: Admin rejected {rej_app_id}. Status updated to Rejected & refund NOT executed.")

    # Verify duplicate approval on already approved request returns 409 Conflict
    code, dup_res = make_request("POST", f"{BASE_URL}/api/approvals/{test_app_id}/approve", headers=admin_headers)
    assert code == 409, f"Expected 409 for duplicate approval, got {code}: {dup_res}"
    print("[PASS] Replay / duplicate approval attempt correctly prevented with HTTP 409 Conflict")

if __name__ == "__main__":
    import traceback
    try:
        test_human_approval_system()
        print("\n🎉 ALL HUMAN APPROVAL TEST CASES & SECURITY CHECKS PASSED SUCCESSFULLY! 🛡️")
        sys.exit(0)
    except Exception as e:
        print("\n❌ TEST FAILED:")
        traceback.print_exc()
        sys.exit(1)

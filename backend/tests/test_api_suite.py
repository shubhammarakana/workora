import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = 'http://127.0.0.1:8000'

def call(endpoint, method='GET', data=None, token=None):
    url = f'{BASE}{endpoint}'
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data else None,
        headers=headers,
        method=method
    )
    try:
        with urllib.request.urlopen(req) as res:
            body = json.loads(res.read().decode())
            return res.status, body
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def run_suite():
    print("=" * 65)
    print(" LOGIFLOW LOGISTICS - COMPREHENSIVE END-TO-END TEST SUITE")
    print("=" * 65)

    # Test 1: Health Check
    status, body = call('/health')
    print(f"[TEST 1] GET /health -> HTTP {status}")
    assert status == 200 and body.get('status') == 'ok', "Health check failed"
    print("  [PASS] Service is healthy & running.")

    # Test 2: Login Demo Account
    status, body = call('/api/auth/login', method='POST', data={
        'email': 'rahul@example.com',
        'password': 'password123'
    })
    print(f"[TEST 2] POST /api/auth/login -> HTTP {status}")
    assert status == 200 and 'access_token' in body, "Login failed"
    token = body['access_token']
    print(f"  [PASS] Authenticated customer: {body['user']['name']} ({body['user']['customer_id']})")

    # Test 3: Get Current Profile
    status, body = call('/api/auth/me', token=token)
    print(f"[TEST 3] GET /api/auth/me -> HTTP {status}")
    assert status == 200 and body['email'] == 'rahul@example.com', "Get profile failed"
    print(f"  [PASS] Verified profile for {body['name']} ({body['city']}, {body['state']})")

    # Test 4: List Shipments
    status, body = call('/api/shipments', token=token)
    print(f"[TEST 4] GET /api/shipments -> HTTP {status}")
    assert status == 200 and isinstance(body, list) and len(body) >= 2, "Shipments list failed"
    print(f"  [PASS] Found {len(body)} shipments for authenticated customer.")

    # Test 5: Get Specific Shipment SL1004
    status, body = call('/api/shipments/SL1004', token=token)
    print(f"[TEST 5] GET /api/shipments/SL1004 -> HTTP {status}")
    assert status == 200 and body['shipment_id'] == 'SL1004', "Get shipment SL1004 failed"
    print(f"  [PASS] Status: {body['status']} | Location: {body['current_location']} | ETA: {body['expected_delivery']}")

    # Test 6: Chat - Shipment Tracking Query
    status, body = call('/api/chat', method='POST', data={'message': 'Where is my shipment SL1004?'}, token=token)
    print(f"[TEST 6] POST /api/chat ('Where is my shipment SL1004?') -> HTTP {status}")
    assert status == 200 and body['intent'] in ['shipment_tracking', 'routing_shipment'] and body['shipment_id'] == 'SL1004'
    print(f"  [PASS] Response: '{body['message']}'")

    # Test 7: Chat - Delay Inquiry
    status, body = call('/api/chat', method='POST', data={'message': 'Why is my shipment delayed?'}, token=token)
    print(f"[TEST 7] POST /api/chat ('Why is my shipment delayed?') -> HTTP {status}")
    assert status == 200 and body['intent'] in ['delayed_shipment', 'routing_shipment', 'delivery_delay']
    print(f"  [PASS] Response: '{body['message']}'")

    # Test 8: Chat - Invoice Inquiry
    status, body = call('/api/chat', method='POST', data={'message': 'Show my latest invoice'}, token=token)
    print(f"[TEST 8] POST /api/chat ('Show my latest invoice') -> HTTP {status}")
    assert status == 200 and body['intent'] in ['invoice_lookup', 'invoice_request', 'missing_invoice_id']
    print(f"  [PASS] Response: '{body['message']}'")

    # Test 9: Chat - Human Support Request
    status, body = call('/api/chat', method='POST', data={'message': 'Connect me with human support'}, token=token)
    print(f"[TEST 9] POST /api/chat ('Connect me with human support') -> HTTP {status}")
    assert status == 200 and body['intent'] == 'human_support'
    print(f"  [PASS] Response: '{body['message']}'")

    # Test 10: Chat - Unsupported Intent Fallback
    status, body = call('/api/chat', method='POST', data={'message': 'What is the weather in Tokyo?'}, token=token)
    print(f"[TEST 10] POST /api/chat ('What is the weather in Tokyo?') -> HTTP {status}")
    assert status == 200 and body['intent'] == 'unsupported'
    print(f"  [PASS] Safe Fallback Response: '{body['message']}'")

    # Test 11: Support Tickets List
    status, body = call('/api/tickets', token=token)
    print(f"[TEST 11] GET /api/tickets -> HTTP {status}")
    assert status == 200 and isinstance(body, list)
    print(f"  [PASS] Retrieved {len(body)} support tickets.")

    # Test 12: Invoices List
    status, body = call('/api/billing/history/CUST001', token=token)
    print(f"[TEST 12] GET /api/billing/history/CUST001 -> HTTP {status}")
    inv_list = body.get('invoices', []) if isinstance(body, dict) else body
    assert status == 200 and isinstance(inv_list, list)
    print(f"  [PASS] Retrieved {len(inv_list)} customer invoices.")

    print("=" * 65)
    print(" [OK] ALL 12 API & RELATIONAL DATABASE TESTS PASSED!")
    print("=" * 65)

if __name__ == '__main__':
    run_suite()

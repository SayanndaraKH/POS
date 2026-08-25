import requests
import json
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:5000"

def run_all_tests():
    print("=== STARTING FULL END-TO-END POS SYSTEM TESTS ===")
    session = requests.Session()

    # 1. Test Login Page GET
    r = session.get(f"{BASE_URL}/login")
    assert r.status_code == 200, f"Login GET failed: {r.status_code}"
    print("[PASS] 1. Login Page loaded successfully (Status: 200)")


    # 2. Test Admin Authentication
    r = session.post(f"{BASE_URL}/login", data={"username": "admin", "password": "admin123"}, allow_redirects=True)
    assert r.status_code == 200, f"Admin login failed: {r.status_code}"
    assert "ផ្ទាំងលក់ (POS)" in r.text or "Sros Sray" in r.text, "Admin login response missing dashboard elements"
    print("✓ 2. Admin Authentication & Session established successfully")

    # 3. Test POS Products & Categories API
    r = session.get(f"{BASE_URL}/api/pos/products?category_id=all")
    assert r.status_code == 200, f"Products API failed: {r.status_code}"
    prod_data = r.json()
    assert prod_data.get('success') is True, "Products API returned success=False"
    products = prod_data.get('products', [])
    assert len(products) > 0, "No products returned from API"
    print(f"✓ 3. POS Products API verified ({len(products)} products available with sizes)")

    # 4. Test Current Shift Status
    r = session.get(f"{BASE_URL}/shifts")
    assert r.status_code == 200, "Shifts page failed"
    print("✓ 4. Shift & Cash Drawer page verified")

    # 5. Get Raw Material stock before placing order
    r = session.get(f"{BASE_URL}/api/inventory/materials")
    mat_data = r.json()
    mat_dict = {m['id']: m for m in mat_data['materials']}
    cup_m_before = mat_dict[1]['current_stock'] # Plastic Cups M
    boba_before = mat_dict[5]['current_stock']   # Raw Boba Pearls
    print(f"✓ 5. Initial Inventory Stock checked (Cups M: {cup_m_before}, Boba: {boba_before}g)")

    # 6. Test Placing an Order (Point of Sale Checkout)
    # Drink 1: Brown Sugar Boba (pid=1), Size M, Sugar 50%, Ice 100%, + Topping (top_id=1, គុជខ្មៅ)
    # Drink 2: Iced Milk Coffee (pid=6), Size M, Sugar 100%, Ice 100%
    order_payload = {
        "items": [
            {
                "product_id": 1,
                "product_name": "តែគុជស្ករត្នោតទឹកដោះគោស្រស់",
                "size": "M",
                "sugar_level": "50%",
                "ice_level": "ទឹកកកពេញ (100%)",
                "unit_price": 2.25,
                "quantity": 2,
                "toppings": [
                    {"id": 1, "name_km": "គុជខ្មៅស្ករត្នោត", "price": 0.35}
                ],
                "notes": "កែវដាច់ដោយឡែក"
            },
            {
                "product_id": 6,
                "product_name": "កាហ្វេទឹកដោះគោទឹកកក (Iced Milk Coffee)",
                "size": "M",
                "sugar_level": "100%",
                "ice_level": "ទឹកកកពេញ (100%)",
                "unit_price": 1.50,
                "quantity": 1,
                "toppings": [],
                "notes": ""
            }
        ],
        "payment_method": "cash",
        "discount_usd": 0.50,
        "amount_received_usd": 10.00,
        "amount_received_khr": 0
    }

    r = session.post(f"{BASE_URL}/api/order/create", json=order_payload)
    assert r.status_code == 200, f"Create order failed: {r.status_code} - {r.text}"
    order_res = r.json()
    assert order_res.get('success') is True, f"Order creation failed: {order_res}"
    order_id = order_res.get('order_id')
    inv_number = order_res.get('invoice_number')
    print(f"✓ 6. Order created successfully: {inv_number} (Order ID: {order_id})")

    # 7. Verify Receipt API & Calculations
    receipt = order_res.get('receipt', {})
    order_info = receipt.get('order', {})
    # Expected total: ((2.25 + 0.35) * 2 + 1.50) - 0.50 = 5.20 + 1.50 - 0.50 = 6.20
    assert order_info.get('total_usd') == 6.20, f"Expected total $6.20, got {order_info.get('total_usd')}"
    assert order_info.get('change_usd') == 3.80, f"Expected change $3.80, got {order_info.get('change_usd')}"
    print(f"✓ 7. Receipt calculations verified (Total: ${order_info.get('total_usd')}, Change: ${order_info.get('change_usd')})")

    # 8. Test Automatic Inventory Stock Deduction
    r = session.get(f"{BASE_URL}/api/inventory/materials")
    mat_data_after = r.json()
    mat_dict_after = {m['id']: m for m in mat_data_after['materials']}
    cup_m_after = mat_dict_after[1]['current_stock']
    boba_after = mat_dict_after[5]['current_stock']

    # Cups M should be reduced by 3 (2 for drink 1, 1 for drink 2)
    assert cup_m_after == cup_m_before - 3, f"Cups stock deduction failed: expected {cup_m_before - 3}, got {cup_m_after}"
    # Boba should be reduced by: drink 1 recipe (40g * 2) + topping (35g * 2) = 150g
    assert boba_after == boba_before - 150, f"Boba stock deduction failed: expected {boba_before - 150}, got {boba_after}"
    print(f"✓ 8. Inventory Auto-Deduction verified (Cups M: {cup_m_before} -> {cup_m_after}, Boba: {boba_before}g -> {boba_after}g)")

    # 9. Test Stock-In API
    r = session.post(f"{BASE_URL}/api/inventory/materials/1/stock-in", json={"quantity": 100, "notes": "នាំចូលបន្ថែមតេស្ត"})
    assert r.status_code == 200 and r.json().get('success') is True, "Stock-In failed"
    print("✓ 9. Material Stock-In API verified")

    # 10. Test Reports Dashboard & Visual KPI Summary
    r = session.get(f"{BASE_URL}/api/reports/dashboard")
    assert r.status_code == 200, "Reports dashboard failed"
    dash_data = r.json()
    assert dash_data.get('success') is True, "Dashboard returned success=False"
    summary = dash_data.get('summary', {})
    assert summary.get('today_usd', 0) >= 6.20, "Dashboard today sales mismatch"
    print(f"✓ 10. Reports KPI Dashboard verified (Today Sales: ${summary.get('today_usd')}, Cups Sold: {summary.get('today_cups')})")

    # 11. Test DataGridView Filter & Pagination
    r = session.get(f"{BASE_URL}/api/reports/orders?page=1&limit=15&search={inv_number}")
    assert r.status_code == 200, "Orders DataGridView failed"
    grid_data = r.json()
    assert grid_data.get('total') >= 1, "DataGridView did not find created invoice"
    print(f"✓ 11. DataGridView filtering & search verified (Found: {grid_data['orders'][0]['invoice_number']})")

    # 12. Test Excel (.xlsx) and CSV Report Export
    r_excel = session.get(f"{BASE_URL}/api/reports/export/excel")
    assert r_excel.status_code == 200 and len(r_excel.content) > 0, "Excel export failed"
    r_csv = session.get(f"{BASE_URL}/api/reports/export/csv")
    assert r_csv.status_code == 200 and len(r_csv.content) > 0, "CSV export failed"
    print("✓ 12. Excel (.xlsx) and CSV Export endpoints verified")

    # 13. Test Database Backup Download
    r_backup = session.get(f"{BASE_URL}/api/backup/download")
    assert r_backup.status_code == 200 and len(r_backup.content) > 0, "Database backup failed"
    print(f"✓ 13. SQLite Database Backup Download verified (Size: {len(r_backup.content)} bytes)")

    # 14. Test QR Code Generator
    r_qr = session.get(f"{BASE_URL}/api/qr/generate?text=KHQR:TEST")
    assert r_qr.status_code == 200 and r_qr.headers.get('Content-Type') == 'image/png', "QR generator failed"
    print("✓ 14. Dynamic KHQR Generator endpoint verified")

    print("\n==================================================")
    print("🎉 ALL 14 POS INTEGRATION TESTS PASSED 100%!")
    print("==================================================")

if __name__ == '__main__':
    run_all_tests()

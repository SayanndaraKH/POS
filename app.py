import os
import io
import json
import sqlite3
import datetime
import qrcode
import pandas as pd
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, redirect, 
    url_for, session, send_file, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    get_db, init_db, seed_data_if_empty, get_store_settings, 
    update_store_settings, get_current_shift, deduct_inventory_for_order, 
    get_low_stock_alerts, DB_PATH
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'boba-pos-secret-khmer-2026-key-tea-system')
if os.environ.get('VERCEL'):
    app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
else:
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
except Exception:
    pass

# Ensure DB is created on startup
with app.app_context():
    init_db()
    seed_data_if_empty()

# ----------------- AUTHENTICATION HELPERS -----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'ការអនុញ្ញាតត្រូវបានបដិសេធ (ត្រូវការសិទ្ធិជា Admin)'}), 403
            flash('ត្រូវការសិទ្ធិជា Admin ដើម្បីចូលមើលទំព័រនេះ!', 'danger')
            return redirect(url_for('pos_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_global_data():
    settings = get_store_settings()
    low_stock_count = 0
    try:
        alerts = get_low_stock_alerts()
        low_stock_count = len(alerts)
    except Exception:
        pass
    return {
        'settings': settings,
        'low_stock_count': low_stock_count,
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        } if 'user_id' in session else None,
        'now': datetime.datetime.now()
    }

# ----------------- AUTH ROUTES -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('pos_page'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']

            # Auto-open shift if cashier doesn't have an open shift
            shift = get_current_shift(user['id'])
            if not shift and user['role'] == 'cashier':
                conn = get_db()
                conn.execute('''
                    INSERT INTO shifts (cashier_id, opening_float_usd, opening_float_khr, status, notes)
                    VALUES (?, 0.0, 0.0, 'open', 'បានបើកវេនដោយស្វ័យប្រវត្តិនៅពេល Login')
                ''', (user['id'],))
                conn.commit()
                conn.close()

            next_url = request.args.get('next')
            return redirect(next_url or url_for('pos_page'))
        else:
            flash('ឈ្មោះអ្នកប្រើ ឬពាក្យសម្ងាត់មិនត្រឹមត្រូវទេ!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('អ្នកបានចាកចេញដោយជោគជ័យ!', 'info')
    return redirect(url_for('login'))

# ----------------- POS MAIN PAGES & APIS -----------------
@app.route('/')
@login_required
def pos_page():
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order ASC').fetchall()
    toppings = conn.execute('SELECT * FROM toppings WHERE is_available = 1 ORDER BY price ASC').fetchall()
    conn.close()
    
    current_shift = get_current_shift(session.get('user_id'))
    return render_template('pos.html', categories=categories, toppings=toppings, shift=current_shift)

@app.route('/api/pos/products', methods=['GET'])
@login_required
def get_pos_products():
    category_id = request.args.get('category_id')
    search = request.args.get('search', '').strip()

    conn = get_db()
    query = '''
        SELECT p.*, c.name_km as category_name_km, c.name_en as category_name_en
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.is_available = 1
    '''
    params = []

    if category_id and category_id != 'all':
        query += ' AND p.category_id = ?'
        params.append(category_id)

    if search:
        query += ' AND (p.name_km LIKE ? OR p.name_en LIKE ? OR p.code LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

    query += ' ORDER BY p.category_id ASC, p.id ASC'
    products = conn.execute(query, params).fetchall()

    # Attach sizes to products
    prod_list = []
    for p in products:
        p_dict = dict(p)
        sizes = conn.execute('SELECT * FROM product_sizes WHERE product_id = ? ORDER BY extra_price ASC', (p['id'],)).fetchall()
        p_dict['sizes'] = [dict(s) for s in sizes]
        prod_list.append(p_dict)

    conn.close()
    return jsonify({'success': True, 'products': prod_list})

@app.route('/api/order/create', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    if not data or 'items' not in data or not data['items']:
        return jsonify({'success': False, 'error': 'សូមជ្រើសរើសភេសជ្ជៈយ៉ាងហោចណាស់មួយ!'}), 400

    items = data.get('items', [])
    cashier_id = session.get('user_id')
    cashier_name = session.get('full_name', 'Cashier')
    payment_method = data.get('payment_method', 'cash')
    customer_note = data.get('customer_note', '')
    
    settings = get_store_settings()
    exchange_rate = float(settings.get('exchange_rate', 4100.0))

    # Calculate Subtotal
    subtotal_usd = 0.0
    for item in items:
        qty = int(item.get('quantity', 1))
        unit_price = float(item.get('unit_price', 0.0))
        top_total = sum(float(t.get('price', 0.0)) for t in item.get('toppings', []))
        item_total = (unit_price + top_total) * qty
        item['calculated_item_total'] = round(item_total, 2)
        subtotal_usd += item_total

    discount_usd = float(data.get('discount_usd', 0.0))
    tax_usd = float(data.get('tax_usd', 0.0))
    total_usd = max(0.0, round(subtotal_usd - discount_usd + tax_usd, 2))
    total_khr = round(total_usd * exchange_rate, -2) # Round to nearest 100 riels

    # Payment calculations
    amount_received_usd = float(data.get('amount_received_usd', 0.0))
    amount_received_khr = float(data.get('amount_received_khr', 0.0))
    
    # Calculate Total Received in USD
    total_received_in_usd = amount_received_usd + (amount_received_khr / exchange_rate if exchange_rate > 0 else 0)
    
    if payment_method == 'cash':
        change_usd_val = max(0.0, total_received_in_usd - total_usd)
        change_usd = round(change_usd_val, 2)
        change_khr = round(change_usd * exchange_rate, -2)
    else:
        amount_received_usd = total_usd
        amount_received_khr = total_khr
        change_usd = 0.0
        change_khr = 0.0

    # Ensure active shift
    shift = get_current_shift(cashier_id)
    shift_id = shift['id'] if shift else None

    # Generate Unique Invoice Number (INV-YYYYMMDD-XXXX)
    now = datetime.datetime.now()
    date_prefix = now.strftime('%Y%m%d')
    conn = get_db()
    cursor = conn.cursor()

    count_row = cursor.execute('SELECT COUNT(*) as cnt FROM orders WHERE invoice_number LIKE ?', (f'INV-{date_prefix}-%',)).fetchone()
    seq = (count_row['cnt'] if count_row else 0) + 1
    invoice_number = f"INV-{date_prefix}-{seq:04d}"

    # Insert Order
    cursor.execute('''
        INSERT INTO orders (
            invoice_number, cashier_id, shift_id, subtotal_usd, discount_usd, tax_usd,
            total_usd, total_khr, exchange_rate, payment_method, amount_received_usd,
            amount_received_khr, change_usd, change_khr, status, customer_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)
    ''', (
        invoice_number, cashier_id, shift_id, subtotal_usd, discount_usd, tax_usd,
        total_usd, total_khr, exchange_rate, payment_method, amount_received_usd,
        amount_received_khr, change_usd, change_khr, customer_note
    ))
    order_id = cursor.lastrowid

    # Insert Order Items & Toppings
    for item in items:
        cursor.execute('''
            INSERT INTO order_items (
                order_id, product_id, product_name, size, sugar_level, ice_level,
                unit_price, quantity, item_total, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id, item.get('product_id'), item.get('product_name'),
            item.get('size', 'M'), item.get('sugar_level', '100%'), item.get('ice_level', '100%'),
            float(item.get('unit_price', 0.0)), int(item.get('quantity', 1)),
            item['calculated_item_total'], item.get('notes', '')
        ))
        item_id = cursor.lastrowid

        for top in item.get('toppings', []):
            cursor.execute('''
                INSERT INTO order_item_toppings (order_item_id, topping_id, topping_name, price)
                VALUES (?, ?, ?, ?)
            ''', (item_id, top.get('id') or top.get('topping_id'), top.get('name_km') or top.get('topping_name'), float(top.get('price', 0.0))))

    # Update Shift totals
    if shift_id:
        cursor.execute('''
            UPDATE shifts 
            SET total_sales_usd = total_sales_usd + ?, 
                total_sales_khr = total_sales_khr + ?, 
                total_orders = total_orders + 1
            WHERE id = ?
        ''', (total_usd, total_khr, shift_id))

    conn.commit()
    conn.close()

    # Auto-Deduct Inventory in background/transaction
    try:
        deduct_inventory_for_order(order_id, items, cashier_name)
    except Exception as e:
        print(f"Error deducting inventory: {e}")

    # Return receipt details
    receipt_data = get_order_receipt_data(order_id)
    return jsonify({
        'success': True,
        'order_id': order_id,
        'invoice_number': invoice_number,
        'receipt': receipt_data
    })

def get_order_receipt_data(order_id):
    conn = get_db()
    order = conn.execute('''
        SELECT o.*, u.full_name as cashier_name
        FROM orders o
        JOIN users u ON o.cashier_id = u.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()

    if not order:
        conn.close()
        return None

    items = conn.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
    item_list = []
    for item in items:
        i_dict = dict(item)
        toppings = conn.execute('SELECT * FROM order_item_toppings WHERE order_item_id = ?', (item['id'],)).fetchall()
        i_dict['toppings'] = [dict(t) for t in toppings]
        item_list.append(i_dict)

    settings = get_store_settings()
    conn.close()

    return {
        'order': dict(order),
        'items': item_list,
        'settings': settings
    }

@app.route('/api/order/<int:order_id>/receipt', methods=['GET'])
@login_required
def get_receipt(order_id):
    data = get_order_receipt_data(order_id)
    if not data:
        return jsonify({'success': False, 'error': 'មិនអាចស្វែងរកវិក្កយបត្របានទេ!'}), 404
    return jsonify({'success': True, 'receipt': data})

@app.route('/api/order/<int:order_id>/void', methods=['POST'])
@login_required
def void_order(order_id):
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'មានតែ Admin ប៉ុណ្ណោះដែលអាច Void វិក្កយបត្របាន!'}), 403

    conn = get_db()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    if not order:
        conn.close()
        return jsonify({'success': False, 'error': 'មិនមានវិក្កយបត្រនេះទេ!'}), 404

    if order['status'] == 'voided':
        conn.close()
        return jsonify({'success': False, 'error': 'វិក្កយបត្រនេះត្រូវបាន Void រួចហើយ!'}), 400

    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'voided' WHERE id = ?", (order_id,))

    # Subtract from shift if active
    if order['shift_id']:
        cursor.execute('''
            UPDATE shifts 
            SET total_sales_usd = MAX(0, total_sales_usd - ?),
                total_sales_khr = MAX(0, total_sales_khr - ?),
                total_orders = MAX(0, total_orders - 1)
            WHERE id = ?
        ''', (order['total_usd'], order['total_khr'], order['shift_id']))

    # Reverse stock deduction from stock_logs
    logs = cursor.execute('''
        SELECT raw_material_id, quantity_changed 
        FROM stock_logs 
        WHERE reference_id = ? AND change_type = 'sale_deduct'
    ''', (f"Order #{order_id}",)).fetchall()

    for log in logs:
        restore_qty = abs(float(log['quantity_changed']))
        rm = cursor.execute('SELECT current_stock FROM raw_materials WHERE id = ?', (log['raw_material_id'],)).fetchone()
        if rm:
            new_stock = float(rm['current_stock']) + restore_qty
            cursor.execute('UPDATE raw_materials SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_stock, log['raw_material_id']))
            cursor.execute('''
                INSERT INTO stock_logs (raw_material_id, change_type, quantity_changed, balance_after, reference_id, notes, created_by)
                VALUES (?, 'order_void', ?, ?, ?, 'ត្រឡប់ស្តុកវិញដោយសារ Void វិក្កយបត្រ', ?)
            ''', (log['raw_material_id'], restore_qty, new_stock, f"Void #{order_id}", session.get('full_name', 'Admin')))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': f'វិក្កយបត្រ {order["invoice_number"]} ត្រូវបាន Void និងត្រឡប់ស្តុកវិញជោគជ័យ!'})

# ----------------- SHIFT MANAGEMENT -----------------
@app.route('/shifts')
@login_required
def shifts_page():
    conn = get_db()
    shifts = conn.execute('''
        SELECT s.*, u.full_name as cashier_name
        FROM shifts s
        JOIN users u ON s.cashier_id = u.id
        ORDER BY s.id DESC LIMIT 30
    ''').fetchall()
    conn.close()
    current_shift = get_current_shift(session.get('user_id'))
    return render_template('shifts.html', shifts=shifts, current_shift=current_shift)

@app.route('/api/shift/open', methods=['POST'])
@login_required
def open_shift():
    data = request.get_json() or {}
    cashier_id = session.get('user_id')
    opening_usd = float(data.get('opening_float_usd', 0.0))
    opening_khr = float(data.get('opening_float_khr', 0.0))
    notes = data.get('notes', 'បើកវេនលក់')

    current = get_current_shift(cashier_id)
    if current:
        return jsonify({'success': False, 'error': 'អ្នកមានវេនដែលកំពុងបើកដំណើរការរួចហើយ!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO shifts (cashier_id, opening_float_usd, opening_float_khr, status, notes)
        VALUES (?, ?, ?, 'open', ?)
    ''', (cashier_id, opening_usd, opening_khr, notes))
    shift_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'shift_id': shift_id, 'message': 'បើកវេនលក់បានជោគជ័យ!'})

@app.route('/api/shift/close', methods=['POST'])
@login_required
def close_shift():
    data = request.get_json() or {}
    shift_id = data.get('shift_id')
    closing_usd = float(data.get('closing_cash_usd', 0.0))
    closing_khr = float(data.get('closing_cash_khr', 0.0))
    notes = data.get('notes', '')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE shifts 
        SET status = 'closed', end_time = CURRENT_TIMESTAMP,
            closing_cash_usd = ?, closing_cash_khr = ?, notes = ?
        WHERE id = ?
    ''', (closing_usd, closing_khr, notes, shift_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'បានបិទវេនលក់ដោយជោគជ័យ!'})

# ----------------- INVENTORY MANAGEMENT -----------------
@app.route('/inventory')
@admin_required
def inventory_page():
    conn = get_db()
    materials = conn.execute('SELECT * FROM raw_materials ORDER BY current_stock <= min_threshold DESC, name_km ASC').fetchall()
    categories = conn.execute('SELECT * FROM categories ORDER BY sort_order ASC').fetchall()
    products = conn.execute('''
        SELECT p.*, c.name_km as category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.category_id ASC, p.id ASC
    ''').fetchall()
    toppings = conn.execute('''
        SELECT t.*, rm.name_km as material_name, rm.unit as material_unit
        FROM toppings t
        LEFT JOIN raw_materials rm ON t.raw_material_id = rm.id
        ORDER BY t.id ASC
    ''').fetchall()
    stock_logs = conn.execute('''
        SELECT sl.*, rm.name_km as material_name, rm.unit
        FROM stock_logs sl
        JOIN raw_materials rm ON sl.raw_material_id = rm.id
        ORDER BY sl.id DESC LIMIT 50
    ''').fetchall()
    conn.close()

    alerts = get_low_stock_alerts()
    return render_template(
        'inventory.html',
        materials=materials,
        categories=categories,
        products=products,
        toppings=toppings,
        stock_logs=stock_logs,
        alerts=alerts
    )

# Raw Material APIs
@app.route('/api/inventory/materials', methods=['GET', 'POST'])
@admin_required
def handle_materials():
    conn = get_db()
    if request.method == 'POST':
        data = request.get_json()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO raw_materials (name_km, name_en, unit, current_stock, min_threshold, cost_per_unit)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('name_km'), data.get('name_en', ''), data.get('unit', 'pcs'),
            float(data.get('current_stock', 0)), float(data.get('min_threshold', 10)),
            float(data.get('cost_per_unit', 0))
        ))
        mat_id = cursor.lastrowid
        cursor.execute('''
            INSERT INTO stock_logs (raw_material_id, change_type, quantity_changed, balance_after, notes, created_by)
            VALUES (?, 'restock', ?, ?, 'បង្កើតវត្ថុធាតុដើមថ្មី', ?)
        ''', (mat_id, float(data.get('current_stock', 0)), float(data.get('current_stock', 0)), session.get('full_name', 'Admin')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានបន្ថែមវត្ថុធាតុដើមជោគជ័យ!'})
    else:
        materials = conn.execute('SELECT * FROM raw_materials ORDER BY name_km ASC').fetchall()
        conn.close()
        return jsonify({'success': True, 'materials': [dict(m) for m in materials]})

@app.route('/api/inventory/materials/<int:mat_id>', methods=['PUT', 'DELETE'])
@admin_required
def modify_material(mat_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM raw_materials WHERE id = ?', (mat_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានលុបវត្ថុធាតុដើមជោគជ័យ!'})
    else:
        data = request.get_json()
        cursor.execute('''
            UPDATE raw_materials 
            SET name_km = ?, name_en = ?, unit = ?, min_threshold = ?, cost_per_unit = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            data.get('name_km'), data.get('name_en'), data.get('unit'),
            float(data.get('min_threshold', 10)), float(data.get('cost_per_unit', 0)),
            mat_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានកែប្រែព័ត៌មានវត្ថុធាតុដើមជោគជ័យ!'})

@app.route('/api/inventory/materials/<int:mat_id>/stock-in', methods=['POST'])
@admin_required
def stock_in_material(mat_id):
    data = request.get_json()
    add_qty = float(data.get('quantity', 0))
    notes = data.get('notes', 'នាំចូលស្តុកបន្ថែម (Stock-In)')

    if add_qty <= 0:
        return jsonify({'success': False, 'error': 'បរិមាណនាំចូលត្រូវតែធំជាង ០!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    rm = cursor.execute('SELECT * FROM raw_materials WHERE id = ?', (mat_id,)).fetchone()
    if not rm:
        conn.close()
        return jsonify({'success': False, 'error': 'រកមិនឃើញវត្ថុធាតុដើម!'}), 404

    new_stock = float(rm['current_stock']) + add_qty
    cursor.execute('UPDATE raw_materials SET current_stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_stock, mat_id))
    cursor.execute('''
        INSERT INTO stock_logs (raw_material_id, change_type, quantity_changed, balance_after, notes, created_by)
        VALUES (?, 'restock', ?, ?, ?, ?)
    ''', (mat_id, add_qty, new_stock, notes, session.get('full_name', 'Admin')))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'new_stock': new_stock, 'message': f'បានបញ្ចូលស្តុក {add_qty} {rm["unit"]} ជោគជ័យ!'})

# Product CRUD APIs
@app.route('/api/inventory/products', methods=['POST'])
@admin_required
def add_product():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO products (category_id, name_km, name_en, code, base_price, image_url, description, is_available)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        data.get('category_id'), data.get('name_km'), data.get('name_en', ''),
        data.get('code', ''), float(data.get('base_price', 0.0)),
        data.get('image_url', '/static/images/brown_sugar_boba.svg'), data.get('description', '')
    ))
    prod_id = cursor.lastrowid

    # Add default size options (M & L)
    cursor.execute('''
        INSERT INTO product_sizes (product_id, size_code, size_name_km, size_name_en, extra_price)
        VALUES 
        (?, 'M', 'កែវកណ្តាល (M)', 'Medium', 0.0),
        (?, 'L', 'កែវធំ (L)', 'Large', 0.50)
    ''', (prod_id, prod_id))

    # Add default raw material deductions (Cup, Straw, Seal)
    cursor.execute('''
        INSERT INTO product_recipes (product_id, raw_material_id, quantity_used, for_size)
        VALUES 
        (?, 1, 1.0, 'M'),
        (?, 2, 1.0, 'L'),
        (?, 3, 1.0, 'ALL'),
        (?, 4, 1.0, 'ALL')
    ''', (prod_id, prod_id, prod_id, prod_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'product_id': prod_id, 'message': 'បានបង្កើតភេសជ្ជៈថ្មីជោគជ័យ!'})

@app.route('/api/inventory/products/<int:prod_id>', methods=['PUT', 'DELETE'])
@admin_required
def modify_product(prod_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM products WHERE id = ?', (prod_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានលុបភេសជ្ជៈជោគជ័យ!'})
    else:
        data = request.get_json()
        cursor.execute('''
            UPDATE products 
            SET category_id = ?, name_km = ?, name_en = ?, code = ?, base_price = ?,
                image_url = ?, description = ?, is_available = ?
            WHERE id = ?
        ''', (
            data.get('category_id'), data.get('name_km'), data.get('name_en'),
            data.get('code'), float(data.get('base_price', 0.0)),
            data.get('image_url'), data.get('description'),
            1 if data.get('is_available', True) else 0,
            prod_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានកែប្រែភេសជ្ជៈជោគជ័យ!'})

@app.route('/api/inventory/recipes/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def handle_recipes(product_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.get_json() or {}
        recipes = data.get('recipes', [])
        # Delete existing and replace
        cursor.execute('DELETE FROM product_recipes WHERE product_id = ?', (product_id,))
        for r in recipes:
            cursor.execute('''
                INSERT INTO product_recipes (product_id, raw_material_id, quantity_used, for_size)
                VALUES (?, ?, ?, ?)
            ''', (product_id, r['raw_material_id'], float(r['quantity_used']), r.get('for_size', 'ALL')))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានរក្សាទុករូបមន្តកាត់ស្តុកជោគជ័យ!'})
    else:
        items = conn.execute('''
            SELECT pr.*, rm.name_km as material_name, rm.unit
            FROM product_recipes pr
            JOIN raw_materials rm ON pr.raw_material_id = rm.id
            WHERE pr.product_id = ?
        ''', (product_id,)).fetchall()
        conn.close()
        return jsonify({'success': True, 'recipes': [dict(i) for i in items]})

# Toppings CRUD
@app.route('/api/inventory/toppings', methods=['POST'])
@admin_required
def add_topping():
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO toppings (name_km, name_en, price, raw_material_id, deduction_amount, is_available)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (
        data.get('name_km'), data.get('name_en', ''), float(data.get('price', 0.0)),
        data.get('raw_material_id') if data.get('raw_material_id') else None,
        float(data.get('deduction_amount', 0.0))
    ))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'បានបន្ថែម Topping ថ្មីជោគជ័យ!'})

@app.route('/api/inventory/toppings/<int:top_id>', methods=['PUT', 'DELETE'])
@admin_required
def modify_topping(top_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM toppings WHERE id = ?', (top_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានលុប Topping ជោគជ័យ!'})
    else:
        data = request.get_json()
        cursor.execute('''
            UPDATE toppings 
            SET name_km = ?, name_en = ?, price = ?, raw_material_id = ?, deduction_amount = ?, is_available = ?
            WHERE id = ?
        ''', (
            data.get('name_km'), data.get('name_en'), float(data.get('price', 0.0)),
            data.get('raw_material_id') if data.get('raw_material_id') else None,
            float(data.get('deduction_amount', 0.0)),
            1 if data.get('is_available', True) else 0,
            top_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានកែប្រែ Topping ជោគជ័យ!'})

# ----------------- REPORTING & DATAGRIDVIEW -----------------
@app.route('/reports')
@admin_required
def reports_page():
    conn = get_db()
    cashiers = conn.execute('SELECT id, full_name FROM users').fetchall()
    categories = conn.execute('SELECT id, name_km FROM categories').fetchall()
    conn.close()
    return render_template('reports.html', cashiers=cashiers, categories=categories)

@app.route('/api/reports/dashboard', methods=['GET'])
@admin_required
def get_reports_dashboard():
    conn = get_db()
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    start_week = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).strftime('%Y-%m-%d')
    start_month = datetime.date.today().strftime('%Y-%m-01')

    # 1. Summary Metrics
    today_metrics = conn.execute('''
        SELECT 
            COALESCE(SUM(total_usd), 0) as total_usd,
            COALESCE(SUM(total_khr), 0) as total_khr,
            COUNT(*) as total_orders
        FROM orders
        WHERE date(created_at) = ? AND status = 'completed'
    ''', (today_str,)).fetchone()

    week_metrics = conn.execute('''
        SELECT 
            COALESCE(SUM(total_usd), 0) as total_usd,
            COUNT(*) as total_orders
        FROM orders
        WHERE date(created_at) >= ? AND status = 'completed'
    ''', (start_week,)).fetchone()

    month_metrics = conn.execute('''
        SELECT 
            COALESCE(SUM(total_usd), 0) as total_usd,
            COUNT(*) as total_orders
        FROM orders
        WHERE date(created_at) >= ? AND status = 'completed'
    ''', (start_month,)).fetchone()

    total_cups_today = conn.execute('''
        SELECT COALESCE(SUM(oi.quantity), 0) as cups
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE date(o.created_at) = ? AND o.status = 'completed'
    ''', (today_str,)).fetchone()['cups']

    # 2. Top 5 Best Selling Drinks (All time / Month)
    top_drinks = conn.execute('''
        SELECT oi.product_name, SUM(oi.quantity) as total_qty, SUM(oi.item_total) as total_revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'completed'
        GROUP BY oi.product_name
        ORDER BY total_qty DESC
        LIMIT 5
    ''').fetchall()

    # 3. Sales by Category
    cat_sales = conn.execute('''
        SELECT c.name_km as category_name, SUM(oi.item_total) as revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE o.status = 'completed'
        GROUP BY c.id
    ''').fetchall()

    # 4. Hourly Sales for Today
    hourly = conn.execute('''
        SELECT strftime('%H:00', created_at) as hour, SUM(total_usd) as total_sales, COUNT(*) as orders_count
        FROM orders
        WHERE date(created_at) = ? AND status = 'completed'
        GROUP BY strftime('%H', created_at)
        ORDER BY hour ASC
    ''', (today_str,)).fetchall()

    # 5. Payment Methods distribution
    payments = conn.execute('''
        SELECT payment_method, COUNT(*) as count, SUM(total_usd) as total_usd
        FROM orders
        WHERE status = 'completed'
        GROUP BY payment_method
    ''').fetchall()

    conn.close()

    return jsonify({
        'success': True,
        'summary': {
            'today_usd': round(today_metrics['total_usd'], 2),
            'today_khr': round(today_metrics['total_khr'], 0),
            'today_orders': today_metrics['total_orders'],
            'today_cups': total_cups_today,
            'week_usd': round(week_metrics['total_usd'], 2),
            'week_orders': week_metrics['total_orders'],
            'month_usd': round(month_metrics['total_usd'], 2),
            'month_orders': month_metrics['total_orders']
        },
        'top_drinks': [dict(d) for d in top_drinks],
        'category_sales': [dict(c) for c in cat_sales],
        'hourly_sales': [dict(h) for h in hourly],
        'payment_methods': [dict(p) for p in payments]
    })

@app.route('/api/reports/orders', methods=['GET'])
@admin_required
def get_orders_datagrid():
    # Filtering params
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    cashier_id = request.args.get('cashier_id', '')
    payment_method = request.args.get('payment_method', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()

    # Pagination params
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 15))
    offset = (page - 1) * limit

    conn = get_db()
    base_query = '''
        FROM orders o
        JOIN users u ON o.cashier_id = u.id
        WHERE 1=1
    '''
    params = []

    if start_date:
        base_query += ' AND date(o.created_at) >= ?'
        params.append(start_date)
    if end_date:
        base_query += ' AND date(o.created_at) <= ?'
        params.append(end_date)
    if cashier_id and cashier_id != 'all':
        base_query += ' AND o.cashier_id = ?'
        params.append(cashier_id)
    if payment_method and payment_method != 'all':
        base_query += ' AND o.payment_method = ?'
        params.append(payment_method)
    if status and status != 'all':
        base_query += ' AND o.status = ?'
        params.append(status)
    if search:
        base_query += ' AND (o.invoice_number LIKE ? OR u.full_name LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    # Count total matching
    count_sql = f"SELECT COUNT(*) as total {base_query}"
    total_records = conn.execute(count_sql, params).fetchone()['total']

    # Total Sum of filtered
    sum_sql = f"SELECT COALESCE(SUM(o.total_usd), 0) as total_sum_usd, COALESCE(SUM(o.total_khr), 0) as total_sum_khr {base_query} AND o.status = 'completed'"
    sum_row = conn.execute(sum_sql, params).fetchone()

    # Fetch paginated rows
    data_sql = f'''
        SELECT o.*, u.full_name as cashier_name
        {base_query}
        ORDER BY o.id DESC
        LIMIT ? OFFSET ?
    '''
    fetch_params = params + [limit, offset]
    rows = conn.execute(data_sql, fetch_params).fetchall()
    conn.close()

    total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1

    return jsonify({
        'success': True,
        'orders': [dict(r) for r in rows],
        'total': total_records,
        'page': page,
        'limit': limit,
        'total_pages': total_pages,
        'filtered_total_usd': round(sum_row['total_sum_usd'], 2),
        'filtered_total_khr': round(sum_row['total_sum_khr'], 0)
    })

# Export Excel / CSV
@app.route('/api/reports/export/excel', methods=['GET'])
@admin_required
def export_orders_excel():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db()
    query = '''
        SELECT 
            o.invoice_number as 'លេខវិក្កយបត្រ',
            u.full_name as 'អ្នកគិតលុយ',
            o.created_at as 'កាលបរិច្ឆេទ',
            o.payment_method as 'វិធីទូទាត់',
            o.subtotal_usd as 'តម្លៃសរុបដើម ($)',
            o.discount_usd as 'បញ្ចុះតម្លៃ ($)',
            o.total_usd as 'សរុបជាដុល្លារ ($)',
            o.total_khr as 'សរុបជារៀល (៛)',
            o.status as 'ស្ថានភាព'
        FROM orders o
        JOIN users u ON o.cashier_id = u.id
        WHERE 1=1
    '''
    params = []
    if start_date:
        query += ' AND date(o.created_at) >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date(o.created_at) <= ?'
        params.append(end_date)

    query += ' ORDER BY o.id DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    data_list = [dict(r) for r in rows]
    df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['លេខវិក្កយបត្រ', 'អ្នកគិតលុយ', 'កាលបរិច្ឆេទ', 'វិធីទូទាត់', 'តម្លៃសរុបដើម ($)', 'បញ្ចុះតម្លៃ ($)', 'សរុបជាដុល្លារ ($)', 'សរុបជារៀល (៛)', 'ស្ថានភាព'])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='របាយការណ៍លក់')
    output.seek(0)

    filename = f"sales_report_{datetime.date.today().strftime('%Y%m%d')}.xlsx"
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/api/reports/export/csv', methods=['GET'])
@admin_required
def export_orders_csv():
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    conn = get_db()
    query = '''
        SELECT 
            o.invoice_number as 'Invoice_No',
            u.full_name as 'Cashier',
            o.created_at as 'Date_Time',
            o.payment_method as 'Payment',
            o.total_usd as 'Total_USD',
            o.total_khr as 'Total_KHR',
            o.status as 'Status'
        FROM orders o
        JOIN users u ON o.cashier_id = u.id
        WHERE 1=1
    '''
    params = []
    if start_date:
        query += ' AND date(o.created_at) >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND date(o.created_at) <= ?'
        params.append(end_date)

    query += ' ORDER BY o.id DESC'
    rows = conn.execute(query, params).fetchall()
    conn.close()

    data_list = [dict(r) for r in rows]
    df = pd.DataFrame(data_list) if data_list else pd.DataFrame(columns=['Invoice_No', 'Cashier', 'Date_Time', 'Payment', 'Total_USD', 'Total_KHR', 'Status'])

    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8-sig'))
    mem.seek(0)

    filename = f"sales_report_{datetime.date.today().strftime('%Y%m%d')}.csv"
    return send_file(
        mem,
        download_name=filename,
        as_attachment=True,
        mimetype='text/csv'
    )

# ----------------- SETTINGS, USERS & BACKUP -----------------
@app.route('/settings')
@admin_required
def settings_page():
    conn = get_db()
    users = conn.execute('SELECT id, username, full_name, role, is_active, created_at FROM users').fetchall()
    conn.close()
    settings = get_store_settings()
    return render_template('settings.html', users=users, settings=settings)

@app.route('/api/settings/update', methods=['POST'])
@admin_required
def update_settings_api():
    data = request.get_json() or {}
    update_store_settings(data)
    return jsonify({'success': True, 'message': 'បានកែប្រែការកំណត់ហាងជោគជ័យ!'})

@app.route('/api/settings/khqr/upload', methods=['POST'])
@admin_required
def upload_khqr_image():
    """Only Admin is allowed to upload/change store KHQR."""
    import base64
    if 'khqr_file' in request.files:
        file = request.files['khqr_file']
        if file and file.filename != '':
            # Validate extension
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.png', '.jpg', '.jpeg', '.webp', '.svg']:
                return jsonify({'success': False, 'error': 'អនុញ្ញាតតែឯកសាររូបភាព (.png, .jpg, .jpeg, .webp, .svg) ប៉ុណ្ណោះ!'}), 400
            
            img_bytes = file.read()
            # Maximum 5MB check
            if len(img_bytes) > 5 * 1024 * 1024:
                return jsonify({'success': False, 'error': 'ទំហំរូបភាពធំពេក (មិនត្រូវលើសពី 5MB)!'}), 400

            mime = file.mimetype or 'image/png'
            b64_str = f"data:{mime};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
            update_store_settings({'khqr_image_url': b64_str})
            return jsonify({'success': True, 'message': 'បាន Upload រូបភាព KHQR ជោគជ័យ!', 'image_url': b64_str})

    data = request.get_json() or {}
    if 'khqr_image_url' in data:
        update_store_settings({'khqr_image_url': data['khqr_image_url']})
        return jsonify({'success': True, 'message': 'បានរក្សាទុករូបភាព KHQR ជោគជ័យ!'})

    return jsonify({'success': False, 'error': 'សូមជ្រើសរើសរូបភាព KHQR ជាមុនសិន!'}), 400

@app.route('/api/settings/khqr/remove', methods=['POST'])
@admin_required
def remove_khqr_image():
    """Only Admin is allowed to reset/remove KHQR."""
    update_store_settings({'khqr_image_url': ''})
    return jsonify({'success': True, 'message': 'បានលុបរូបភាព KHQR ជោគជ័យ!'})

# Users CRUD
@app.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    role = data.get('role', 'cashier')

    if not username or not password or not full_name:
        return jsonify({'success': False, 'error': 'សូមបំពេញព័ត៌មានឱ្យបានគ្រប់ជ្រុងជ្រោយ!'}), 400

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO users (username, password_hash, full_name, role, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (username, generate_password_hash(password), full_name, role))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានបង្កើតគណនីថ្មីជោគជ័យ!'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'ឈ្មោះគណនី (Username) នេះមានរួចហើយ!'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
def modify_user(user_id):
    if user_id == session.get('user_id') and request.method == 'DELETE':
        return jsonify({'success': False, 'error': 'មិនអាចលុបគណនីដែលកំពុង Login បានទេ!'}), 400

    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'DELETE':
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានលុបគណនីជោគជ័យ!'})
    else:
        data = request.get_json()
        full_name = data.get('full_name')
        role = data.get('role')
        is_active = 1 if data.get('is_active', True) else 0
        password = data.get('password', '').strip()

        if password:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, role = ?, is_active = ?, password_hash = ?
                WHERE id = ?
            ''', (full_name, role, is_active, generate_password_hash(password), user_id))
        else:
            cursor.execute('''
                UPDATE users 
                SET full_name = ?, role = ?, is_active = ?
                WHERE id = ?
            ''', (full_name, role, is_active, user_id))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'បានកែប្រែគណនីជោគជ័យ!'})

# Backup & Restore
@app.route('/api/backup/download', methods=['GET'])
@admin_required
def download_backup():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"pos_tea_backup_{timestamp}.db"
    return send_file(
        DB_PATH,
        as_attachment=True,
        download_name=backup_filename,
        mimetype='application/x-sqlite3'
    )

@app.route('/api/backup/restore', methods=['POST'])
@admin_required
def restore_backup():
    if 'backup_file' not in request.files:
        return jsonify({'success': False, 'error': 'សូមជ្រើសរើសឯកសារ Database Backup (.db) !'}), 400

    file = request.files['backup_file']
    if file.filename == '' or not file.filename.endswith('.db'):
        return jsonify({'success': False, 'error': 'ឯកសារត្រូវតែជាប្រភេទ .db ប៉ុណ្ណោះ!'}), 400

    try:
        # Save temp and verify sqlite
        temp_path = os.path.join(os.path.dirname(__file__), 'temp_restore.db')
        file.save(temp_path)

        # Test if valid sqlite
        test_conn = sqlite3.connect(temp_path)
        test_cursor = test_conn.cursor()
        test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in test_cursor.fetchall()]
        test_conn.close()

        if 'orders' not in tables or 'products' not in tables or 'users' not in tables:
            os.remove(temp_path)
            return jsonify({'success': False, 'error': 'ឯកសារ Database មិនត្រូវតាមទម្រង់ប្រព័ន្ធ POS ទេ!'}), 400

        # Replace existing database safely
        if os.path.exists(DB_PATH):
            os.replace(temp_path, DB_PATH)
        else:
            os.rename(temp_path, DB_PATH)

        return jsonify({'success': True, 'message': 'បានទាញយក និងស្តារទិន្នន័យ (Restore) ជោគជ័យ!'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'បរាជ័យក្នុងការ Restore: {str(e)}'}), 500

# QR Code Dynamic Generator
@app.route('/api/qr/generate')
def generate_qr_image():
    text = request.args.get('text', 'https://bakong.nbc.org.kh')
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    print("==================================================")
    print("Boba & Beverage POS System is starting...")
    print("Server URL: http://127.0.0.1:5000")
    print("Admin Login: admin / admin123")
    print("Cashier Login: cashier / 123456")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)


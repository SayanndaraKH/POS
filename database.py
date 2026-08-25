import sqlite3
import os
import json
import shutil
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Handle read-only filesystem on Vercel Serverless
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/pos_tea.db'
    default_db = os.path.join(os.path.dirname(__file__), 'pos_tea.db')
    if not os.path.exists(DB_PATH) and os.path.exists(default_db):
        try:
            shutil.copyfile(default_db, DB_PATH)
        except Exception:
            pass
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'pos_tea.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('admin', 'cashier')),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_km TEXT NOT NULL,
            name_en TEXT NOT NULL,
            icon TEXT DEFAULT 'coffee',
            color TEXT DEFAULT '#10b981',
            sort_order INTEGER DEFAULT 0
        )
    ''')

    # 3. Raw Materials (Inventory ingredients)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_km TEXT NOT NULL,
            name_en TEXT NOT NULL,
            unit TEXT NOT NULL, -- pcs, g, ml, etc.
            current_stock REAL NOT NULL DEFAULT 0,
            min_threshold REAL NOT NULL DEFAULT 10,
            cost_per_unit REAL NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. Products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name_km TEXT NOT NULL,
            name_en TEXT NOT NULL,
            code TEXT UNIQUE,
            base_price REAL NOT NULL DEFAULT 0.0,
            image_url TEXT,
            is_available INTEGER DEFAULT 1,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    ''')

    # 5. Product Sizes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_sizes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            size_code TEXT NOT NULL, -- 'M', 'L'
            size_name_km TEXT NOT NULL,
            size_name_en TEXT NOT NULL,
            extra_price REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')

    # 6. Toppings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toppings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name_km TEXT NOT NULL,
            name_en TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0.0,
            raw_material_id INTEGER,
            deduction_amount REAL DEFAULT 0.0, -- amount of raw material per topping portion
            is_available INTEGER DEFAULT 1,
            FOREIGN KEY (raw_material_id) REFERENCES raw_materials (id) ON DELETE SET NULL
        )
    ''')

    # 7. Product Recipes (Bill of Materials / BOM)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            raw_material_id INTEGER NOT NULL,
            quantity_used REAL NOT NULL DEFAULT 1.0,
            for_size TEXT DEFAULT 'ALL', -- 'ALL', 'M', 'L'
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
            FOREIGN KEY (raw_material_id) REFERENCES raw_materials (id) ON DELETE CASCADE
        )
    ''')

    # 8. Shifts table (Cash drawer & shift control)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cashier_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            opening_float_usd REAL DEFAULT 0.0,
            opening_float_khr REAL DEFAULT 0.0,
            closing_cash_usd REAL DEFAULT 0.0,
            closing_cash_khr REAL DEFAULT 0.0,
            total_sales_usd REAL DEFAULT 0.0,
            total_sales_khr REAL DEFAULT 0.0,
            total_orders INTEGER DEFAULT 0,
            status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed')),
            notes TEXT,
            FOREIGN KEY (cashier_id) REFERENCES users (id)
        )
    ''')

    # 9. Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            cashier_id INTEGER NOT NULL,
            shift_id INTEGER,
            subtotal_usd REAL NOT NULL DEFAULT 0.0,
            discount_usd REAL DEFAULT 0.0,
            tax_usd REAL DEFAULT 0.0,
            total_usd REAL NOT NULL DEFAULT 0.0,
            total_khr REAL NOT NULL DEFAULT 0.0,
            exchange_rate REAL NOT NULL DEFAULT 4100.0,
            payment_method TEXT NOT NULL CHECK (payment_method IN ('cash', 'khqr', 'card')),
            amount_received_usd REAL DEFAULT 0.0,
            amount_received_khr REAL DEFAULT 0.0,
            change_usd REAL DEFAULT 0.0,
            change_khr REAL DEFAULT 0.0,
            status TEXT DEFAULT 'completed' CHECK (status IN ('completed', 'voided')),
            customer_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cashier_id) REFERENCES users (id),
            FOREIGN KEY (shift_id) REFERENCES shifts (id)
        )
    ''')

    # 10. Order Items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            size TEXT DEFAULT 'M',
            sugar_level TEXT DEFAULT '100%',
            ice_level TEXT DEFAULT '100%',
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            item_total REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
        )
    ''')

    # 11. Order Item Toppings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_item_toppings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_item_id INTEGER NOT NULL,
            topping_id INTEGER,
            topping_name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (order_item_id) REFERENCES order_items (id) ON DELETE CASCADE,
            FOREIGN KEY (topping_id) REFERENCES toppings (id) ON DELETE SET NULL
        )
    ''')

    # 12. Stock Logs (Audit trail for inventory movements)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_material_id INTEGER NOT NULL,
            change_type TEXT NOT NULL CHECK (change_type IN ('sale_deduct', 'restock', 'adjustment', 'waste', 'order_void')),
            quantity_changed REAL NOT NULL,
            balance_after REAL NOT NULL,
            reference_id TEXT, -- e.g. Order Invoice # or Shift #
            notes TEXT,
            created_by TEXT DEFAULT 'System',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (raw_material_id) REFERENCES raw_materials (id) ON DELETE CASCADE
        )
    ''')

    # 13. Store Settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT
        )
    ''')

    conn.commit()
    conn.close()

def seed_data_if_empty():
    conn = get_db()
    cursor = conn.cursor()

    # Check if users exist
    cursor.execute('SELECT COUNT(*) as count FROM users')
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return

    # Seed Admin and Cashier Users
    admin_pw = generate_password_hash('admin123')
    cashier_pw = generate_password_hash('123456')
    cursor.execute('''
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES 
        ('admin', ?, 'អ្នកគ្រប់គ្រងប្រព័ន្ធ (Admin)', 'admin'),
        ('cashier', ?, 'បុគ្គលិកគិតលុយ (Cashier)', 'cashier')
    ''', (admin_pw, cashier_pw))

    # Seed Store Settings
    settings = [
        ('shop_name_km', 'ហាងតែគុជ ស្រស់ស្រាយ (Sros Sray Boba)', 'ឈ្មោះហាងជាភាសាខ្មែរ'),
        ('shop_name_en', 'Sros Sray Boba & Beverage', 'Shop Name in English'),
        ('shop_phone', '012 345 678 / 098 765 432', 'លេខទូរស័ព្ទទំនាក់ទំនង'),
        ('shop_address', 'ផ្ទះលេខ ១២ ផ្លូវ ២០០ រាជធានីភ្នំពេញ', 'អាសយដ្ឋានហាង'),
        ('exchange_rate', '4100', 'អត្រាប្តូរប្រាក់ (1 USD = KHR)'),
        ('khqr_bakong_id', 'srossray_tea@aclb', 'Bakong Account ID'),
        ('khqr_merchant_name', 'SROS SRAY TEA & COFFEE', 'ឈ្មោះគណនីបាគង KHQR'),
        ('khqr_image_url', '', 'រូបភាពស្កេន KHQR (Base64 ឬ Link)'),
        ('khqr_instruction', 'ស្កេនទូទាត់ប្រាក់តាមកម្មវិធីបាគង ឬគ្រប់កម្មវិធីធនាគារទាំងអស់', 'ការណែនាំស្កេន KHQR')
    ]
    cursor.executemany('INSERT OR REPLACE INTO store_settings (key, value, description) VALUES (?, ?, ?)', settings)

    # Seed Raw Materials (Inventory)
    raw_materials = [
        # (name_km, name_en, unit, current_stock, min_threshold, cost_per_unit)
        ('កែវទំហំ M (500ml)', 'Plastic Cups M', 'pcs', 500, 50, 0.05),
        ('កែវទំហំ L (700ml)', 'Plastic Cups L', 'pcs', 500, 50, 0.07),
        ('ទុយោតែគុជ', 'Boba Straws', 'pcs', 800, 100, 0.01),
        ('ផ្លាស្ទិកបិទមាត់កែវ/គម្រប', 'Cup Seal Film', 'pcs', 1000, 100, 0.01),
        ('គ្រាប់គុជឆៅ (Boba)', 'Raw Boba Pearls', 'g', 10000, 1500, 0.005),
        ('គ្រាប់គុជស (Crystal Pearl)', 'Crystal White Pearls', 'g', 5000, 1000, 0.008),
        ('ស្លឹកតែខ្មៅបុរាណ', 'Black Tea Leaves', 'g', 4000, 500, 0.012),
        ('ម្សៅតែបៃតង Matcha', 'Green Tea Matcha Powder', 'g', 3000, 400, 0.02),
        ('ស្លឹកតែក្រហមថៃ', 'Thai Tea Leaves', 'g', 3500, 500, 0.01),
        ('ម្សៅត្រសក់ស្រូវ (Taro)', 'Taro Powder', 'g', 4000, 500, 0.015),
        ('គ្រាប់កាហ្វេ Arabica/Robusta', 'Coffee Beans', 'g', 5000, 800, 0.018),
        ('ទឹកដោះគោស្រស់ (Fresh Milk)', 'Fresh Milk', 'ml', 15000, 2000, 0.002),
        ('ទឹកដោះគោខាប់', 'Condensed Milk', 'ml', 10000, 1500, 0.003),
        ('ទឹកស៊ីរ៉ូស្ករធម្មជាតិ', 'Sugar Syrup', 'ml', 12000, 2000, 0.002),
        ('ទឹកស៊ីរ៉ូស្ករត្នោត (Brown Sugar)', 'Brown Sugar Syrup', 'ml', 8000, 1000, 0.004),
        ('ទឹកផ្លែផាសិនសុទ្ធ', 'Fresh Passion Puree', 'ml', 5000, 800, 0.005),
        ('ទឹកផ្លែស្ត្រប៊ែរីសុទ្ធ', 'Strawberry Puree', 'ml', 5000, 800, 0.006),
        ('ម្សៅពពុះឈីស (Cheese Powder)', 'Cheese Foam Powder', 'g', 3000, 400, 0.025),
        ('ពងមាន់ភូឌីង (Pudding)', 'Egg Pudding', 'g', 3000, 500, 0.01)
    ]
    cursor.executemany('''
        INSERT INTO raw_materials (name_km, name_en, unit, current_stock, min_threshold, cost_per_unit)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', raw_materials)

    # Seed Categories
    categories = [
        ('តែគុជ & តែដោះគោ', 'Milk Tea Series', 'cup-soda', '#10b981', 1),
        ('កាហ្វេឈ្ងុយឆ្ងាញ់', 'Coffee Selection', 'coffee', '#b45309', 2),
        ('តែផ្លែឈើ & ទឹកក្រឡុក', 'Fruit Tea & Smoothies', 'citrus', '#f59e0b', 3),
        ('ភេសជ្ជៈពិសេស & សូកូឡា', 'Special Brews & Choco', 'sparkles', '#8b5cf6', 4),
        ('នំ និងអាហារសម្រន់', 'Snacks & Bakery', 'cookie', '#ec4899', 5)
    ]
    cursor.executemany('''
        INSERT INTO categories (name_km, name_en, icon, color, sort_order)
        VALUES (?, ?, ?, ?, ?)
    ''', categories)

    # Seed Toppings
    # Map toppings to raw materials: 5: Boba (30g), 6: Crystal (30g), 18: Cheese Powder (20g), 19: Pudding (40g)
    toppings = [
        ('គុជខ្មៅស្ករត្នោត', 'Brown Sugar Boba', 0.35, 5, 35.0),
        ('គុជសគ្រីស្តាល់', 'Crystal White Pearls', 0.40, 6, 30.0),
        ('ពពុះឈីសក្រអូប', 'Cheese Foam', 0.50, 18, 25.0),
        ('ពងមាន់ភូឌីង', 'Egg Pudding', 0.45, 19, 45.0),
        ('ចាហួយដូងធម្មជាតិ', 'Coconut Jelly', 0.35, None, 0.0),
        ('គ្រាប់ជីសុខភាព', 'Chia Seeds', 0.25, None, 0.0)
    ]
    cursor.executemany('''
        INSERT INTO toppings (name_km, name_en, price, raw_material_id, deduction_amount)
        VALUES (?, ?, ?, ?, ?)
    ''', toppings)

    # Seed Products
    products = [
        # Cat 1: Milk Tea
        (1, 'តែគុជស្ករត្នោតទឹកដោះគោស្រស់', 'Brown Sugar Boba Fresh Milk', 'MT01', 2.25, '/static/images/brown_sugar_boba.svg', 'តែគុជស្ករត្នោតដ៏ពេញនិយម រសជាតិផ្អែមឈ្ងុយ និងទឹកដោះគោស្រស់សុទ្ធ'),
        (1, 'តែបៃតងដោះគោ (Matcha Green Tea)', 'Signature Matcha Milk Tea', 'MT02', 2.00, '/static/images/matcha_latte.svg', 'តែបៃតងម៉ាត់ឆាគុណភាពខ្ពស់ ឈ្ងុយឆ្ងាញ់ពិសេស'),
        (1, 'តែទឹកដោះគោបុរាណ (Classic Milk Tea)', 'Classic Signature Milk Tea', 'MT03', 1.75, '/static/images/classic_milk_tea.svg', 'តែទឹកដោះគោរសជាតិដើម ឈ្ងុយស្លឹកតែខ្មៅដិតដល់'),
        (1, 'តែក្រហមថៃដោះគោ (Thai Milk Tea)', 'Thai Red Milk Tea', 'MT04', 1.85, '/static/images/thai_tea.svg', 'តែថៃពណ៌ទឹកក្រូចដ៏ល្បីល្បាញ រសជាតិផ្អែមមុតស្រាល'),
        (1, 'តែត្រសក់ស្រូវដោះគោ (Taro Milk Tea)', 'Taro Milk Tea', 'MT05', 2.00, '/static/images/taro_milk_tea.svg', 'រសជាតិត្រសក់ស្រូវពណ៌ស្វាយ ផ្អែមឈ្ងុយប្លែកមាត់'),
        
        # Cat 2: Coffee
        (2, 'កាហ្វេទឹកដោះគោទឹកកក (Iced Milk Coffee)', 'Cambodian Iced Milk Coffee', 'CF01', 1.50, '/static/images/iced_coffee.svg', 'កាហ្វេទឹកដោះគោបែបខ្មែរ ឈ្ងុយដិតស្រស់ស្រាយ'),
        (2, 'កាហ្វេអាមេរិកាណូទឹកកក (Iced Americano)', 'Iced Americano', 'CF02', 1.50, '/static/images/americano.svg', 'កាហ្វេខ្មៅសុទ្ធ មិនផ្អែម ជំនួយដល់ការងារ'),
        (2, 'កាហ្វេឡាតេទឹកកក (Iced Latte)', 'Iced Cafe Latte', 'CF03', 2.00, '/static/images/latte.svg', 'កាហ្វេអេស្ព្រេសសូ លាយជាមួយទឹកដោះគោស្រស់'),
        (2, 'កាហ្វេម៉ូកាទឹកកក (Iced Mocha)', 'Iced Mocha Coffee', 'CF04', 2.25, '/static/images/mocha.svg', 'កាហ្វេបូកផ្សំជាមួយសូកូឡាដិត'),

        # Cat 3: Fruit Tea & Smoothies
        (3, 'តែផាសិនទឹកឃ្មុំស្រស់ (Fresh Passion Fruit Tea)', 'Fresh Passion Honey Tea', 'FT01', 1.75, '/static/images/passion_tea.svg', 'រសជាតិជូរអែមត្រជាក់ស្រស់ស្រាយបំបាត់ការស្រេកទឹក'),
        (3, 'ទឹកស្ត្រប៊ែរីក្រឡុក (Strawberry Smoothie)', 'Strawberry Cream Smoothie', 'FT02', 2.50, '/static/images/strawberry_smoothie.svg', 'ស្ត្រប៊ែរីក្រឡុកជាមួយទឹកដោះគោ រសជាតិឆ្ងាញ់ជាប់ចិត្ត'),
        (3, 'តែក្រូចឆ្មារទឹកឃ្មុំ (Lemon Honey Green Tea)', 'Honey Lemon Green Tea', 'FT03', 1.75, '/static/images/lemon_tea.svg', 'តែបៃតងក្រូចឆ្មារ ជួយជំនួយបំពង់ក'),

        # Cat 4: Special Brews
        (4, 'សូកូឡាទឹកដោះគោទឹកកក (Signature Chocolate)', 'Rich Dark Chocolate Milk', 'SP01', 2.00, '/static/images/chocolate.svg', 'សូកូឡាដិតគុណភាពខ្ពស់ ផ្អែមឈ្ងុយ'),
        (4, 'តែបៃតងម៉ាត់ឆាពពុះឈីស (Matcha Cheese Foam)', 'Matcha Cheese Foam Supreme', 'SP02', 2.75, '/static/images/matcha_cheese.svg', 'តែបៃតងម៉ាត់ឆាខាងក្រោម បូកជាមួយពពុះឈីសក្រអូបខាងលើ')
    ]
    cursor.executemany('''
        INSERT INTO products (category_id, name_km, name_en, code, base_price, image_url, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', products)

    # Seed Product Sizes (Standard M = +$0.00, L = +$0.50)
    cursor.execute('SELECT id FROM products')
    prod_ids = [row['id'] for row in cursor.fetchall()]
    for pid in prod_ids:
        cursor.execute('''
            INSERT INTO product_sizes (product_id, size_code, size_name_km, size_name_en, extra_price)
            VALUES 
            (?, 'M', 'កែវកណ្តាល (Medium)', 'Medium (500ml)', 0.00),
            (?, 'L', 'កែវធំ (Large)', 'Large (700ml)', 0.50)
        ''', (pid, pid))

    # Seed Standard Recipes (Raw material deduction linkage)
    # Every drink needs: 1 cup (M: 1, L: 2), 1 straw (3), 1 seal (4)
    # Specific drinks need tea/coffee/milk/syrup
    recipes = []
    # 1: Brown Sugar Boba (pid=1) -> Cup(1/2), Straw(3), Seal(4), Boba(5, 40g), Fresh Milk(12, 200ml), Brown Sugar Syrup(15, 30ml)
    recipes.append((1, 1, 1.0, 'M'))
    recipes.append((1, 2, 1.0, 'L'))
    recipes.append((1, 3, 1.0, 'ALL'))
    recipes.append((1, 4, 1.0, 'ALL'))
    recipes.append((1, 5, 40.0, 'ALL'))
    recipes.append((1, 12, 180.0, 'M'))
    recipes.append((1, 12, 250.0, 'L'))
    recipes.append((1, 15, 30.0, 'ALL'))

    # 2: Matcha Green Tea (pid=2) -> Cup, Straw, Seal, Matcha(8, 15g), Fresh Milk(12, 150ml), Syrup(14, 25ml)
    recipes.append((2, 1, 1.0, 'M'))
    recipes.append((2, 2, 1.0, 'L'))
    recipes.append((2, 3, 1.0, 'ALL'))
    recipes.append((2, 4, 1.0, 'ALL'))
    recipes.append((2, 8, 15.0, 'ALL'))
    recipes.append((2, 12, 150.0, 'ALL'))
    recipes.append((2, 14, 25.0, 'ALL'))

    # 3: Classic Milk Tea (pid=3) -> Cup, Straw, Seal, Black Tea(7, 20g), Condensed Milk(13, 30ml), Fresh Milk(12, 100ml)
    recipes.append((3, 1, 1.0, 'M'))
    recipes.append((3, 2, 1.0, 'L'))
    recipes.append((3, 3, 1.0, 'ALL'))
    recipes.append((3, 4, 1.0, 'ALL'))
    recipes.append((3, 7, 20.0, 'ALL'))
    recipes.append((3, 13, 30.0, 'ALL'))
    recipes.append((3, 12, 100.0, 'ALL'))

    # 6: Iced Milk Coffee (pid=6) -> Cup, Straw, Seal, Coffee Beans(11, 20g), Condensed Milk(13, 35ml), Fresh Milk(12, 60ml)
    recipes.append((6, 1, 1.0, 'M'))
    recipes.append((6, 2, 1.0, 'L'))
    recipes.append((6, 3, 1.0, 'ALL'))
    recipes.append((6, 4, 1.0, 'ALL'))
    recipes.append((6, 11, 20.0, 'ALL'))
    recipes.append((6, 13, 35.0, 'ALL'))
    recipes.append((6, 12, 60.0, 'ALL'))

    # General recipe fallback for other drinks
    for pid in range(4, 15):
        if pid not in [6]:
            recipes.append((pid, 1, 1.0, 'M'))
            recipes.append((pid, 2, 1.0, 'L'))
            recipes.append((pid, 3, 1.0, 'ALL'))
            recipes.append((pid, 4, 1.0, 'ALL'))

    cursor.executemany('''
        INSERT INTO product_recipes (product_id, raw_material_id, quantity_used, for_size)
        VALUES (?, ?, ?, ?)
    ''', recipes)

    # Seed Initial Shift (open shift for cashier)
    cursor.execute('''
        INSERT INTO shifts (cashier_id, opening_float_usd, opening_float_khr, status, notes)
        VALUES (2, 20.0, 80000.0, 'open', 'វេនពេលព្រឹកដំបូង')
    ''')

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully!")

# Helper functions for POS & Orders
def get_store_settings():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM store_settings').fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def update_store_settings(settings_dict):
    conn = get_db()
    cursor = conn.cursor()
    for k, v in settings_dict.items():
        cursor.execute('INSERT OR REPLACE INTO store_settings (key, value) VALUES (?, ?)', (k, str(v)))
    conn.commit()
    conn.close()

def get_current_shift(cashier_id=None):
    conn = get_db()
    if cashier_id:
        shift = conn.execute('''
            SELECT * FROM shifts WHERE cashier_id = ? AND status = 'open' 
            ORDER BY id DESC LIMIT 1
        ''', (cashier_id,)).fetchone()
    else:
        shift = conn.execute('''
            SELECT s.*, u.full_name as cashier_name 
            FROM shifts s JOIN users u ON s.cashier_id = u.id 
            WHERE s.status = 'open' 
            ORDER BY s.id DESC LIMIT 1
        ''').fetchone()
    conn.close()
    return dict(shift) if shift else None

def deduct_inventory_for_order(order_id, items, cashier_name="Cashier"):
    """
    Deducts raw materials based on recipes and selected toppings,
    and creates records in stock_logs.
    """
    conn = get_db()
    cursor = conn.cursor()

    for item in items:
        prod_id = item.get('product_id')
        qty = int(item.get('quantity', 1))
        size = item.get('size', 'M').upper()
        toppings = item.get('toppings', [])

        # 1. Deduct Product Recipe Ingredients
        recipes = cursor.execute('''
            SELECT pr.raw_material_id, pr.quantity_used, pr.for_size, rm.name_km, rm.current_stock, rm.unit
            FROM product_recipes pr
            JOIN raw_materials rm ON pr.raw_material_id = rm.id
            WHERE pr.product_id = ? AND (pr.for_size = ? OR pr.for_size = 'ALL')
        ''', (prod_id, size)).fetchall()

        for rec in recipes:
            deduct_qty = float(rec['quantity_used']) * qty
            new_stock = float(rec['current_stock']) - deduct_qty
            
            cursor.execute('''
                UPDATE raw_materials 
                SET current_stock = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_stock, rec['raw_material_id']))

            cursor.execute('''
                INSERT INTO stock_logs (raw_material_id, change_type, quantity_changed, balance_after, reference_id, notes, created_by)
                VALUES (?, 'sale_deduct', ?, ?, ?, ?, ?)
            ''', (rec['raw_material_id'], -deduct_qty, new_stock, f"Order #{order_id}", f"កាត់សម្រាប់ {item.get('product_name')} x{qty}", cashier_name))

        # 2. Deduct Toppings Ingredients
        for top in toppings:
            top_id = top.get('id') or top.get('topping_id')
            if top_id:
                top_row = cursor.execute('''
                    SELECT t.raw_material_id, t.deduction_amount, rm.current_stock, rm.name_km
                    FROM toppings t
                    JOIN raw_materials rm ON t.raw_material_id = rm.id
                    WHERE t.id = ? AND t.raw_material_id IS NOT NULL
                ''', (top_id,)).fetchone()

                if top_row and top_row['deduction_amount'] > 0:
                    deduct_qty = float(top_row['deduction_amount']) * qty
                    new_stock = float(top_row['current_stock']) - deduct_qty

                    cursor.execute('''
                        UPDATE raw_materials 
                        SET current_stock = ?, updated_at = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (new_stock, top_row['raw_material_id']))

                    cursor.execute('''
                        INSERT INTO stock_logs (raw_material_id, change_type, quantity_changed, balance_after, reference_id, notes, created_by)
                        VALUES (?, 'sale_deduct', ?, ?, ?, ?, ?)
                    ''', (top_row['raw_material_id'], -deduct_qty, new_stock, f"Order #{order_id}", f"កាត់ Topping: {top.get('name_km', 'Topping')} x{qty}", cashier_name))

    conn.commit()
    conn.close()

def get_low_stock_alerts():
    conn = get_db()
    alerts = conn.execute('''
        SELECT id, name_km, name_en, unit, current_stock, min_threshold,
               CASE 
                   WHEN current_stock <= 0 THEN 'danger'
                   WHEN current_stock <= min_threshold THEN 'warning'
                   ELSE 'ok'
               END as status
        FROM raw_materials
        WHERE current_stock <= min_threshold
        ORDER BY current_stock ASC
    ''').fetchall()
    conn.close()
    return [dict(row) for row in alerts]

if __name__ == '__main__':
    init_db()
    seed_data_if_empty()

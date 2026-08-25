# -*- coding: utf-8 -*-
"""
Sync Local Database to Turso Cloud Database Tool
Copies all existing local categories, products, toppings, recipes, raw materials,
users, and settings to your Turso Cloud Database automatically.
"""
import os
import sys
import sqlite3

# Ensure stdout uses UTF-8 on Windows
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

from turso_db import connect_turso

def main():
    print("=" * 79)
    print("  ☁️  ឧបករណ៍ភ្ជាប់ និង Sync ទិន្នន័យទៅកាន់ Turso Cloud Database")
    print("  ☕ Boba POS System - Cloud Database Initializer")
    print("=" * 79)
    print()

    turso_url = os.environ.get('TURSO_DATABASE_URL', '').strip()
    turso_token = os.environ.get('TURSO_AUTH_TOKEN', '').strip()

    if not turso_url:
        print("👉 សូមបញ្ចូល Turso Database URL របស់អ្នក (ឧ. https://pos-tea-xxxx.turso.io ឬ libsql://...):")
        turso_url = input("   TURSO_DATABASE_URL: ").strip()

    if not turso_token:
        print("👉 សូមបញ្ចូល Turso Auth Token របស់អ្នក:")
        turso_token = input("   TURSO_AUTH_TOKEN: ").strip()

    if not turso_url or not turso_token:
        print("\n❌ [កំហុស] សូមបញ្ចូល URL និង Token ឱ្យបានពេញលេញ!")
        input("\nចុច Enter ដើម្បីចាកចេញ...")
        return

    print("\n[*] កំពុងភ្ជាប់ទៅកាន់ Turso Cloud Database...")
    try:
        cloud_conn = connect_turso(turso_url, turso_token)
        # Test connection
        cloud_conn.execute("SELECT 1")
        print("✅ ភ្ជាប់ទៅកាន់ Cloud Database បានជោគជ័យ!")
    except Exception as e:
        print(f"❌ បរាជ័យក្នុងការភ្ជាប់៖ {e}")
        input("\nចុច Enter ដើម្បីចាកចេញ...")
        return

    # Initialize tables
    print("\n[*] កំពុងបង្កើត Tables ក្នុង Cloud Database...")
    import database
    # Temporarily set cloud connection in database module
    database.TURSO_URL = turso_url
    database.TURSO_TOKEN = turso_token
    database.init_db()
    print("✅ បង្កើត Schema និង Tables រួចរាល់!")

    # Check local db
    local_db_path = os.path.join(os.path.dirname(__file__), 'pos_tea.db')
    if os.path.exists(local_db_path):
        print("\n[*] រកឃើញឯកសារទិន្នន័យក្នុងម៉ាស៊ីន (pos_tea.db)!")
        ans = input("❓ តើអ្នកចង់ Sync ទិន្នន័យ (ផលិតផល, មុខទំនិញ, ស្តុក, គណនី) ពីម៉ាស៊ីនឡើងទៅ Cloud ដែរឬទេ? (Y/n): ").strip().lower()
        if ans != 'n':
            local_conn = sqlite3.connect(local_db_path)
            local_conn.row_factory = sqlite3.Row

            tables_to_sync = [
                'users', 'categories', 'raw_materials', 'products', 
                'product_sizes', 'toppings', 'product_recipes', 'store_settings'
            ]

            for tbl in tables_to_sync:
                try:
                    rows = local_conn.execute(f"SELECT * FROM {tbl}").fetchall()
                    if rows:
                        cols = list(rows[0].keys())
                        placeholders = ",".join(["?"] * len(cols))
                        cols_str = ",".join(cols)
                        sql = f"INSERT OR REPLACE INTO {tbl} ({cols_str}) VALUES ({placeholders})"
                        
                        count = 0
                        for r in rows:
                            vals = [r[c] for c in cols]
                            cloud_conn.execute(sql, vals)
                            count += 1
                        print(f"   ✓ បាន Sync {tbl}: {count} ជួរ")
                except Exception as ex:
                    print(f"   ⚠️ Sync {tbl} រំលង៖ {ex}")

            local_conn.close()
            print("\n🎉 ការ Sync ទិន្នន័យទៅកាន់ Cloud Database ត្រូវបានបញ្ចប់ដោយជោគជ័យ!")
    else:
        database.seed_data_if_empty()
        print("✅ បានបញ្ចូលទិន្នន័យគំរូដំបូងក្នុង Cloud Database រួចរាល់!")

    print("\n" + "=" * 79)
    print("  📋 ជំហានបន្ទាប់ដើម្បីដាក់ដំណើរការលើ Vercel:")
    print("  1. ចូលទៅកាន់ Vercel Dashboard ➡️ Project POS ➡️ Settings ➡️ Environment Variables")
    print("  2. បន្ថែម Variable ទាំង ២ នេះ៖")
    print(f"     • TURSO_DATABASE_URL = {turso_url}")
    print(f"     • TURSO_AUTH_TOKEN    = (Token របស់អ្នក)")
    print("  3. ពេលនោះរាល់ពេល Deploy ថ្មី ទិន្នន័យរបស់អ្នកនឹងស្ថិតនៅលើ Cloud ជារៀងរហូត (Zero Data Loss)!")
    print("=" * 79)
    print()
    input("ចុច Enter ដើម្បីបិទ...")

if __name__ == '__main__':
    main()

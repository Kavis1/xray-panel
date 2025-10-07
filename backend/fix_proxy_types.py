#!/usr/bin/env python3
"""
Auto-fix script to normalize proxy types to lowercase
"""
import sqlite3
import sys

def main():
    db_path = "panel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("PROXY TYPE NORMALIZATION")
        print("=" * 80)
        print()
        
        # Check current state
        cursor.execute("SELECT id, user_id, type FROM user_proxies WHERE type != LOWER(type)")
        proxies_to_fix = cursor.fetchall()
        
        if not proxies_to_fix:
            print("✅ All proxy types are already in lowercase")
            return
        
        print(f"Found {len(proxies_to_fix)} proxies with uppercase/mixed case types:")
        print()
        
        for proxy_id, user_id, ptype in proxies_to_fix:
            print(f"  Proxy ID {proxy_id} (User {user_id}): '{ptype}' → '{ptype.lower()}'")
        
        print()
        print("Fixing...")
        
        # Fix all types to lowercase
        cursor.execute("UPDATE user_proxies SET type = LOWER(type) WHERE type != LOWER(type)")
        fixed_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Fixed {fixed_count} proxy types to lowercase")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

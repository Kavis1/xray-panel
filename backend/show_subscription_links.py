#!/usr/bin/env python3
"""
Display subscription links for all users with their new tokens
"""
import sqlite3
import sys

def main():
    db_path = "panel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, subscription_token, status, expire_at
            FROM users
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("No users found")
            return
        
        print("\n" + "=" * 100)
        print("SUBSCRIPTION LINKS (use these in your clients)")
        print("=" * 100)
        print()
        
        # Get domain from environment or use default
        import os
        domain = os.getenv("DEFAULT_DOMAIN", "example.com")
        print(f"📍 Using domain: {domain}")
        print(f"   (Set DEFAULT_DOMAIN in .env to change)")
        print()
        
        for username, token, status, expire_at in users:
            if not token:
                print(f"⚠️  {username:25} - NO TOKEN (run token generation script)")
                continue
            
            status_icon = "✅" if status == "ACTIVE" else "❌"
            
            print(f"{status_icon} {username:25} → https://{domain}/sub/{token}")
            print(f"   sing-box:  https://{domain}/sub/singbox/{token}")
            print()
        
        print("=" * 100)
        print()
        print("📝 To change domain, edit this script and update 'domain' variable")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

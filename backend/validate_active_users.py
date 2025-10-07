#!/usr/bin/env python3
"""
Validate that all active users have at least one inbound assigned
Deactivate users without inbounds
"""
import sqlite3
import sys

def main():
    db_path = "panel.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 80)
        print("ACTIVE USERS VALIDATION")
        print("=" * 80)
        print()
        
        # Find active users without inbounds
        cursor.execute("""
            SELECT u.id, u.username, u.status,
                   (SELECT COUNT(*) FROM user_inbounds WHERE user_id = u.id) as inbound_count,
                   (SELECT COUNT(*) FROM user_proxies WHERE user_id = u.id) as proxy_count
            FROM users u
            WHERE u.status = 'active'
        """)
        
        users = cursor.fetchall()
        
        print(f"Checking {len(users)} active users...")
        print()
        
        users_without_inbounds = []
        users_ok = []
        
        for user_id, username, status, inbound_count, proxy_count in users:
            if inbound_count == 0:
                users_without_inbounds.append((user_id, username, proxy_count))
                print(f"  ❌ {username:25} - No inbounds (proxies: {proxy_count})")
            else:
                users_ok.append((user_id, username, inbound_count))
                print(f"  ✅ {username:25} - {inbound_count} inbound(s)")
        
        print()
        
        if users_without_inbounds:
            print(f"⚠️  Found {len(users_without_inbounds)} active users without inbounds")
            print("These users will be deactivated:")
            print()
            
            for user_id, username, proxy_count in users_without_inbounds:
                cursor.execute("UPDATE users SET status = 'inactive' WHERE id = ?", (user_id,))
                print(f"  • {username} → INACTIVE")
            
            conn.commit()
            print()
            print(f"✅ Deactivated {len(users_without_inbounds)} users")
            print()
            print("💡 To activate these users again:")
            print("   1. Assign at least one inbound to each user")
            print("   2. Change their status back to active")
        else:
            print("✅ All active users have inbounds assigned")
        
        print()
        print(f"Summary: {len(users_ok)} valid, {len(users_without_inbounds)} fixed")
        print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

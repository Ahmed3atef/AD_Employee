from ldap3 import Server, Connection, ALL, NTLM, SIMPLE
import ssl

def init_server(username, password):
    try:
        # Option 1: Use LDAPS (port 636) with SSL
        server = Server('localhost', port=636, use_ssl=True, get_info=ALL)
        
        conn = Connection(
            server, 
            user=f'{username}@eissa.local',
            password=password,
            auto_bind=True
        )
        
        print(f"✓ Connected successfully as {username}@eissa.local")
        print(f"Server info: {server.info}")
        
        # Search for users
        conn.search('DC=eissa,DC=local', '(objectClass=person)')
        print(f"\nFound {len(conn.entries)} users:")
        for entry in conn.entries:
            print(f"  - {entry.entry_dn}")
        
        conn.unbind()
        
    except Exception as e:
        print(f"✗ LDAPS failed: {e}")
        print("\nTrying with StartTLS on port 389...")
        
        # Option 2: Use StartTLS on port 389
        try:
            server = Server('localhost', port=389, get_info=ALL)
            
            # Create connection with TLS
            conn = Connection(
                server,
                user=f'{username}@eissa.local',
                password=password
            )
            
            # Start TLS before binding
            conn.start_tls()
            conn.bind()
            
            print(f"✓ Connected with StartTLS as {username}@eissa.local")
            
            # Search for users
            conn.search('DC=eissa,DC=local', '(objectClass=person)')
            print(f"\nFound {len(conn.entries)} users:")
            for entry in conn.entries:
                print(f"  - {entry.entry_dn}")
            
            conn.unbind()
            
        except Exception as e2:
            print(f"✗ StartTLS also failed: {e2}")
            print("\nTrying anonymous bind to check server...")
            
            # Option 3: Check if server is reachable with anonymous bind
            try:
                server = Server('localhost', port=389, get_info=ALL)
                conn = Connection(server)
                conn.bind()
                print(f"✓ Anonymous bind successful")
                print(f"Server info: {server.info}")
                conn.unbind()
            except Exception as e3:
                print(f"✗ Anonymous bind failed: {e3}")


def main():
    init_server('Administrator', 'Admin@123456')
    
if __name__ == "__main__":
    main()
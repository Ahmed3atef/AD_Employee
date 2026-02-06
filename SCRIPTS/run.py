from ldap3 import Server, Connection,ALL,SUBTREE

SERVER_HOST = 'ldap://localhost:389'
DOMAIN = 'eissa.local'
BASE_D = 'dc=eissa,dc=local'
BASE_CONTAINER = 'OU=New,DC=eissa,DC=local'
USERNAME = 'Administrator@eissa.local'
PASSWORD = 'Admin@123456'

def connect_ad():
    try:
        server = Server(SERVER_HOST, port=389, get_info=ALL)
        conn = Connection(server, user=f'{USERNAME}', password=PASSWORD)
        conn.start_tls()
        conn.bind()
        
        
        conn.search(
            BASE_D,
            search_filter='(objectClass=person)',
            search_scope=SUBTREE,
            attributes=['sAMAccountName', 'displayName', 'title']
        )
        
        return [entry.entry_dn for entry in conn.entries]
    except Exception as e:
        print(f"Error connecting to AD: {e}")
        return None

def mian():
    conn = connect_ad()
    if conn:
        print("Connected to AD")
        
    for i in conn:
        print(i)
        
if __name__ == '__main__':
    mian()

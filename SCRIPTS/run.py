from ldap3 import Server, Connection, ALL, SUBTREE

SERVER_HOST = 'ldap://localhost:389'
BASE_D = 'dc=eissa,dc=local'
USERNAME = 'Administrator@eissa.local'
PASSWORD = 'Admin@123456'

def connect_ad():
    server = Server(SERVER_HOST, get_info=ALL)
    conn = Connection(
        server,
        user=USERNAME,
        password=PASSWORD,
    )
    conn.start_tls()
    conn.bind()

    conn.search(
        BASE_D,
        '(objectClass=person)',
        SUBTREE,
        attributes=['sAMAccountName', 'displayName', 'title']
    )

    return conn

def main():
    conn = connect_ad()

    if not conn.bound:
        print("Authentication Failed ❌")
        return

    print(f"Successfully connected to AD as {USERNAME} ✅")

    for entry in conn.entries:
        print(entry.entry_dn)

if __name__ == '__main__':
    main()

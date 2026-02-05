from ldap3 import Server, Connection, ALL, NTLM, SIMPLE
import logging
import ssl

logger = logging.getLogger(__name__)

SERVER_HOST = os.getenv('AD_SERVER')
DOMAIN = os.getenv('AD_DOMAIN')
BASE_DN = os.getenv('AD_BASE_DN')
BASE_CONTAINER = os.getenv('AD_CONTAINER_DN_BASE')

class ADConnection:
    def __init__(self):
        try:
            server = Server('localhost', port=389, get_info=ALL)
            conn = Connection(server)
            conn.bind()
            print(f"✓ Anonymous bind successful")
            print(f"Server info: {server.info}")
            conn.unbind()
        except Exception as e3:
            print(f"✗ Anonymous bind failed: {e3}")
            
            
    def connect_ad(self, username, password):
        """
        Connect to AD
        """
        self.username = username if f'@{DOMAIN}' in username else f'{username}@{DOMAIN}'
        self.password = password 
        self.server = Server(SERVER_HOST, get_info=ALL)
        try:
            self.conn = Connection(self.server, user=self.username, password=self.password)
            self.conn.start_tls()
            self.conn.bind()
            logger.info(f"Successfully connected to AD as {self.username}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to AD: {e}")
            return False
    
    def get_all_users_full_info(self):
        """
        returns list of entries
        example:
            [
                DN: CN=fatima ahmed,OU=Accountant,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872853
                DN: CN=Administrator,CN=Users,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872895
                DN: CN=krbtgt,CN=Users,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872917
                DN: CN=omar mahmoud,OU=Sales,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872933
                DN: CN=ahmed hassan,OU=IT,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872948
                DN: CN=Guest,CN=Users,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872961
                DN: CN=sara ali,OU=HR,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872974
                DN: CN=mohamed khaled,OU=Projects,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.872990
                DN: CN=5D9533FD62B7,OU=Domain Controllers,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:10:28.873002
            ]
        """
        try:
            self.conn.search(BASE_DN, '(objectClass=person)')
            logger.info(f"Synced {len(self.conn.entries)} users from AD")
            return self.conn.entries
        except Exception as e:
            logger.error(f"Error syncing users from AD: {e}")
            return []
        
    def search_user_full_info(self, username):
        """
        returns list of entries
        example:
            [
                DN: CN=mohamed khaled,OU=Projects,OU=New,DC=eissa,DC=local - STATUS: Read - READ TIME: 2026-02-05T20:17:20.433030
            ]
        """
        try:
            self.conn.search(BASE_DN, f'(sAMAccountName={username})')
            logger.info(f"Synced {len(self.conn.entries)} users from AD")
            return self.conn.entries
        except Exception as e:
            logger.error(f"Error syncing users from AD: {e}")
            return []
    
    def get_all_users_dn(self):
        """
        returns list of entries
        example:
            [
                CN=omar mahmoud,OU=Sales,OU=New,DC=eissa,DC=local
                CN=ahmed hassan,OU=IT,OU=New,DC=eissa,DC=local
                CN=Guest,CN=Users,DC=eissa,DC=local
                CN=sara ali,OU=HR,OU=New,DC=eissa,DC=local
                CN=mohamed khaled,OU=Projects,OU=New,DC=eissa,DC=local
                CN=5D9533FD62B7,OU=Domain Controllers,DC=eissa,DC=local
            ]
        """
        try:
            self.conn.search(BASE_DN, '(objectClass=person)')
            logger.info(f"Synced {len(self.conn.entries)} users from AD")
            return [entry.entry_dn for entry in self.conn.entries]
        except Exception as e:
            logger.error(f"Error syncing users from AD: {e}")
            return []
        
    def searsh_user_dn(self, username):
        """
        returns list of entries
        example:
            [
                CN=mohamed khaled,OU=Projects,OU=New,DC=eissa,DC=local
            ]
        """
        try:
            self.conn.search(BASE_DN, f'(sAMAccountName={username})')
            logger.info(f"Synced {len(self.conn.entries)} users from AD")
            return [entry.entry_dn for entry in self.conn.entries]
        except Exception as e:
            logger.error(f"Error syncing users from AD: {e}")
            return []

    def update_ou(self, username, ou):
        """
        Update the OU of a user
        
        """
        try:
            old_dn = self.searsh_user_dn(username)
            new_ou = f'OU={ou},' + BASE_CONTAINER
            if old_dn:
                self.conn.modify_dn(old_dn, f'CN={username}', new_superior=new_ou)
                logger.info(f"Updated OU of {username} to {new_ou}")
                return True
            else:
                logger.error(f"User {username} not found in AD")
                return False
        except Exception as e:
            logger.error(f"Error updating OU of {username}: {e}")
            return False
                
    def __del__(self):
        self.conn.unbind()
        logger.info(f"Disconnected from AD as {self.username}")
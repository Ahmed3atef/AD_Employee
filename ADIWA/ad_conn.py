from ldap3 import Server, Connection, ALL, SUBTREE
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADConnection:
    def __init__(self, server_host, domain, base_dn, base_container):
        self.server_host = server_host
        self.domain = domain
        self.base_dn = base_dn
        self.base_container = base_container
        self.conn = None
        self.server = None

        try:
            server = Server(self.server_host, port=389, get_info=ALL)
            conn = Connection(server, auto_bind=True)
            logger.info("✓ Anonymous bind successful")
            logger.info(server.info)
            conn.unbind()
        except Exception as e:
            raise Exception(f"✗ Initial bind failed: {e}")

    def connect_ad(self, username: str, password: str) -> bool:
        self.username = (
            username if f"@{self.domain}" in username
            else f"{username}@{self.domain}"
        )

        self.server = Server(self.server_host, get_info=ALL)

        try:
            self.conn = Connection(
                self.server,
                user=self.username,
                password=password,
            )
            self.conn.start_tls()
            self.conn.bind()

            if not self.conn.bound:
                logger.error("Authentication failed")
                return False

            logger.info(f"Successfully connected as {self.username}")
            return True

        except Exception as e:
            logger.error(f"Error connecting to AD: {e}")
            return False

    def _ensure_bound(self):
        if not self.conn or not self.conn.bound:
            raise Exception("Not connected to AD")

    def get_all_users_full_info(self, attributes=None):
        self._ensure_bound()

        self.conn.search(
            self.base_dn,
            '(objectClass=person)',
            search_scope=SUBTREE,
            attributes=attributes or ['*']
        )

        logger.info(f"Synced {len(self.conn.entries)} users from AD")
        return self.conn.entries

    def search_user_full_info(self, username, attributes=None):
        self._ensure_bound()

        self.conn.search(
            self.base_dn,
            f'(sAMAccountName={username})',
            search_scope=SUBTREE,
            attributes=attributes or ['*']
        )

        return self.conn.entries

    def get_all_users_dn(self):
        self._ensure_bound()

        self.conn.search(self.base_dn, '(objectClass=person)')
        return [entry.entry_dn for entry in self.conn.entries]

    def search_user_dn(self, username):
        self._ensure_bound()

        self.conn.search(
            self.base_dn,
            f'(sAMAccountName={username})'
        )
        return [entry.entry_dn for entry in self.conn.entries]

    def update_ou(self, username, new_ou):
        self._ensure_bound()

        old_dns = self.search_user_dn(username)
        if not old_dns:
            logger.error(f"User {username} not found")
            return False

        old_dn = old_dns[0]

        match = re.match(r'CN=([^,]+)', old_dn)
        if not match:
            logger.error(f"Invalid DN: {old_dn}")
            return False

        cn = match.group(1)
        relative_dn = f"CN={cn}"
        new_superior = f"OU={new_ou},{self.base_container}"

        success = self.conn.modify_dn(
            dn=old_dn,
            relative_dn=relative_dn,
            new_superior=new_superior
        )

        if not success:
            logger.error(self.conn.result)
            return False

        logger.info(f"Moved {username} to OU={new_ou}")
        return True

    def __del__(self):
        try:
            if self.conn and self.conn.bound:
                self.conn.unbind()
                logger.info("Disconnected from AD")
        except Exception:
            pass

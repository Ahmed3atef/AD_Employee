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

    def create_user(self, username, password, given_name, surname,
                    mail=None, telephone=None, ou=None):
        """
        Create a new user in Active Directory.

        Args:
            username:    sAMAccountName (e.g. 'ahmed.atef')
            password:    plain-text password
            given_name:  first name
            surname:     last name
            mail:        email address (optional)
            telephone:   phone number (optional)
            ou:          target OU name under base_container (optional)

        Returns:
            (True, message) on success, (False, error_message) on failure.
        """
        self._ensure_bound()

        # Build the DN
        display_name = f"{given_name} {surname}"
        container = f"OU={ou},{self.base_container}" if ou else self.base_container
        user_dn = f"CN={display_name},{container}"
        upn = f"{username}@{self.domain}"

        # Build attributes
        attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'sAMAccountName': username,
            'userPrincipalName': upn,
            'givenName': given_name,
            'sn': surname,
            'displayName': display_name,
            'userAccountControl': '512',  # Normal account, enabled
        }

        if mail:
            attributes['mail'] = mail
        if telephone:
            attributes['telephoneNumber'] = telephone

        # Create the user entry
        success = self.conn.add(user_dn, attributes=attributes)
        if not success:
            error = self.conn.result.get('description', 'Unknown error')
            message = self.conn.result.get('message', '')
            logger.error(f"Failed to create AD user {username}: {error} - {message}")
            return False, f"{error}: {message}" if message else error

        # Set password  (AD requires unicodePwd in modify, UTF-16-LE encoded)
        encoded_pwd = f'"{password}"'.encode('utf-16-le')
        pwd_change = self.conn.modify(
            user_dn,
            {'unicodePwd': [(2, [encoded_pwd])]}  # 2 = MODIFY_REPLACE
        )

        if not pwd_change:
            # User was created but password failed — log warning
            error = self.conn.result.get('description', 'Unknown error')
            logger.warning(f"AD user {username} created but password set failed: {error}")
            return True, f"User created but password set failed: {error}. Set password manually."

        logger.info(f"Created AD user: {username} in {container}")
        return True, f"User '{username}' created successfully in AD."

    def change_password(self, username, new_password):
        """
        Change a user's password in Active Directory.

        Args:
            username:      sAMAccountName (e.g. 'ahmed.atef')
            new_password:  the new plain-text password

        Returns:
            (True, message) on success, (False, error_message) on failure.
        """
        self._ensure_bound()

        # Find the user's DN
        dns = self.search_user_dn(username)
        if not dns:
            return False, f"User '{username}' not found in Active Directory."

        user_dn = dns[0]

        # AD requires the password as a UTF-16-LE encoded, double-quoted string
        encoded_pwd = f'"{new_password}"'.encode('utf-16-le')
        success = self.conn.modify(
            user_dn,
            {'unicodePwd': [(2, [encoded_pwd])]}  # 2 = MODIFY_REPLACE
        )

        if not success:
            error = self.conn.result.get('description', 'Unknown error')
            message = self.conn.result.get('message', '')
            logger.error(f"Failed to change password for {username}: {error} - {message}")
            return False, f"{error}: {message}" if message else error

        logger.info(f"Password changed for AD user: {username}")
        return True, f"Password for '{username}' changed successfully."
    
    def delete_user(self, username):
        """
        Delete a user from Active Directory.

        Args:
            username:      sAMAccountName (e.g. 'ahmed.atef')

        Returns:
            (True, message) on success, (False, error_message) on failure.
        """
        self._ensure_bound()

        dns = self.search_user_dn(username)
        if not dns:
            return False, f"User '{username}' not found in Active Directory."

        user_dn = dns[0]

        success = self.conn.delete(user_dn)
        if not success:
            error = self.conn.result.get('description', 'Unknown error')
            message = self.conn.result.get('message', '')
            logger.error(f"Failed to delete AD user {username}: {error} - {message}")
            return False, f"{error}: {message}" if message else error

        logger.info(f"Deleted AD user: {username}")
        return True, f"User '{username}' deleted successfully from AD."

    def __del__(self):
        try:
            if self.conn and self.conn.bound:
                self.conn.unbind()
                logger.info("Disconnected from AD")
        except Exception:
            pass

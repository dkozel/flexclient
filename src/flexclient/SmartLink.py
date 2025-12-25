import http.client, pdb, socket, ssl, threading, select, json, os
from selenium import (
    webdriver,
)  # Needed to instantiate a browser whose current URL may be set and read
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from time import sleep
from authlib.integrations.requests_client import OAuth2Session
from authlib.oauth2.rfc6749 import OAuth2Token
import keyring
from datetime import datetime, timedelta


class PingServer(threading.Thread):
    """Thread to ping smartlink server whilst user info is inputted"""

    def __init__(self, socket):
        threading.Thread.__init__(self, daemon=True)
        self.socket = socket
        self.running = True

    def run(self):
        # print("\n...Thread started...\n")
        while self.running:
            try:
                self.socket.send("ping from client\n".encode("cp1252"))
            except (ssl.SSLEOFError, OSError, BrokenPipeError) as e:
                # Socket closed or connection lost, stop pinging
                print(f"Ping thread: connection lost ({e}), stopping pings")
                break
            sleep(5)
        # print("\n...Thread ended...\n")


class SmartLink(object):
    """Class which connects and authenticates with the SmartLink Server"""

    HOST_FLEX = "smartlink.flexradio.com"
    HOST_Auth = "frtest.auth0.com"
    AUTH_URL = "https://frtest.auth0.com/authorize"
    TOKEN_URL = "https://frtest.auth0.com/oauth/token"
    REDIRECT_URI = "https://frtest.auth0.com/mobile"
    CLIENT_ID = (
        "4Y9fEIIsVYyQo5u6jr7yBWc4lV5ugC2m"  # was "C1br1uk8UecHZnUGlIFt1yp62ZNizey3"
    )
    SCOPE_LIST = ["openid", "profile", "offline_access"]
    BROWSER = "firefox"
    OS = "Windows_NT"
    KEYRING_SERVICE = "flexclient"
    KEYRING_USERNAME = "oauth_tokens"

    def __init__(self, browser="firefox", force_login=False):
        """
        Initialize SmartLink connection with cached or new OAuth tokens.

        Args:
            browser: Browser to use for login ('firefox' or 'chrome')
            force_login: If True, ignore cached tokens and force browser login
        """
        # Try to load cached tokens first
        token_data = None
        if not force_login:
            token_data = self._load_tokens()
            if token_data:
                print("Using cached authentication tokens")
                # Try to refresh if expired
                if self._is_token_expired(token_data):
                    print("Token expired, attempting refresh...")
                    token_data = self._refresh_tokens(token_data)
                    if not token_data:
                        print("Refresh failed, will re-authenticate")

        # If no valid cached tokens, do browser login
        if not token_data:
            print("Starting browser-based authentication...")
            token_data = self.get_auth0_tokens(browser)
            if token_data:
                self._save_tokens(token_data)
                print("Authentication successful, tokens cached")

        if not token_data:
            raise Exception("Authentication failed - no valid tokens obtained")

        # After authentication, connect to SmartLink server
        context = ssl.create_default_context()
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wrapped_server_sock = context.wrap_socket(
            self.server_sock, server_hostname=self.HOST_FLEX
        )
        self.wrapped_server_sock.connect((self.HOST_FLEX, 443))

        # Start ping thread after connection is established
        self.pingThread = PingServer(self.wrapped_server_sock)
        self.pingThread.start()

        # Send registration command immediately while connection is fresh
        self.radio_list = self.SendRegisterApplicationMessageToServer(
            "flexclient", self.OS, token_data["id_token"]
        )

    def _load_tokens(self):
        """Load OAuth tokens from secure keyring storage."""
        try:
            token_json = keyring.get_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            print(f"Warning: Could not load cached tokens: {e}")
        return None

    def _save_tokens(self, token_data):
        """Save OAuth tokens to secure keyring storage."""
        try:
            token_json = json.dumps(token_data)
            keyring.set_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME, token_json)
        except Exception as e:
            print(f"Warning: Could not save tokens to keyring: {e}")

    def _is_token_expired(self, token_data):
        """Check if the access token is expired or about to expire."""
        if "expires_at" in token_data:
            # Token has explicit expiry timestamp
            expires_at = token_data["expires_at"]
            return datetime.now().timestamp() >= expires_at - 60  # 60s buffer
        elif "expires_in" in token_data and "issued_at" in token_data:
            # Calculate expiry from issued_at + expires_in
            expires_at = token_data["issued_at"] + token_data["expires_in"]
            return datetime.now().timestamp() >= expires_at - 60
        # If no expiry info, assume expired to be safe
        return True

    def _refresh_tokens(self, token_data):
        """Refresh OAuth tokens using refresh_token."""
        if "refresh_token" not in token_data:
            print("No refresh token available")
            return None

        try:
            # Use authlib to refresh tokens
            session = OAuth2Session(
                client_id=self.CLIENT_ID,
                token=token_data,
                token_endpoint=self.TOKEN_URL
            )
            new_token = session.refresh_token(self.TOKEN_URL)

            # Save the new tokens
            self._save_tokens(new_token)
            print("Token refresh successful")
            return new_token
        except Exception as e:
            print(f"Token refresh failed: {e}")
            return None

    def get_auth0_tokens(self, browser):
        """
        Perform browser-based OAuth2 authentication using Auth0.
        Uses authlib for proper OAuth2 flow with browser-based user interaction.

        Args:
            browser: Browser to use ('firefox', 'chrome', or 'chromium')

        Returns:
            dict: Token data including access_token, id_token, refresh_token, and expiry info
        """
        # Create OAuth2 session with authlib
        session = OAuth2Session(
            client_id=self.CLIENT_ID,
            redirect_uri=self.REDIRECT_URI,
            scope=" ".join(self.SCOPE_LIST),
        )

        # Generate authorization URL
        authorization_url, state = session.create_authorization_url(self.AUTH_URL)
        print(f"Authorization URL: {authorization_url[:100]}...")

        # Setup browser with automatic driver management
        if browser == "firefox":
            options = webdriver.FirefoxOptions()
            service = FirefoxService("/snap/bin/geckodriver")
            driver = webdriver.Firefox(service=service, options=options)
        else:  # chrome or chromium
            options = webdriver.ChromeOptions()
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            if browser == "chromium":
                try:
                    options.binary_location = "/snap/bin/chromium"
                except:
                    pass  # Fall back to Chrome if Chromium not found

            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)

        try:
            # Open browser for user to log in
            print("Opening browser for authentication...")
            driver.get(authorization_url)

            # Wait for redirect (user completes login)
            initial_url = driver.current_url
            while driver.current_url == initial_url or not driver.current_url.startswith(
                self.REDIRECT_URI
            ):
                sleep(0.5)

            # Get the redirect URL containing the authorization code
            redirect_response = driver.current_url
            print(f"Received redirect: {redirect_response[:80]}...")

        finally:
            driver.quit()

        # Extract authorization code and exchange for tokens using authlib
        try:
            token = session.fetch_token(
                self.TOKEN_URL, authorization_response=redirect_response
            )

            # Add timestamp for expiry tracking
            token["issued_at"] = datetime.now().timestamp()
            if "expires_in" in token:
                token["expires_at"] = token["issued_at"] + token["expires_in"]

            print(
                f"Successfully obtained tokens (expires in {token.get('expires_in', 'unknown')}s)"
            )
            if "refresh_token" in token:
                print("Refresh token obtained - subsequent logins will be automatic")

            return token

        except Exception as e:
            print(f"ERROR: Failed to exchange authorization code for tokens: {e}")
            return None

    def get_response(self, conn):
        res = conn.getresponse()
        data = res.read()
        return data.decode("utf-8")

    def SendRegisterApplicationMessageToServer(self, appName, platform, token):
        command = (
            "application register name="
            + appName
            + " platform="
            + platform
            + " token="
            + token
            + "\n"
        )
        radioData = []
        if self.wrapped_server_sock.version() != None:
            # print(self.wrapped_server_sock.version())
            print(command)
            self.wrapped_server_sock.send(command.encode("cp1252"))
            """ Communicate with SmartLink Server """
            inputs = [self.wrapped_server_sock]
            while inputs:
                readable, writable, exceptional = select.select(inputs, [], [], 2)
                # pdb.set_trace()

                for s in readable:
                    data = s.recv(1024).decode("utf-8")
                    print(data)
                    if "radio_name" in data:
                        radioData.append(self.ParseRadios(data))
                    # else:
                    # 	""" Never gets here as no longer any sockets in readable """
                    # 	inputs.remove(s)
                if len(readable) < 1:
                    """no sockets are readable so must escape loop"""
                    inputs.clear()

        else:
            print("Socket connection not established....")

        return radioData

    def ParseRadios(self, radioString):
        """retrieve necessary radio info"""
        desirable_txt = {
            "serial": None,
            "public_ip": None,
            "public_upnp_tls_port": None,
            "public_upnp_udp_port": None,
            "upnp_supported": None,
            "public_tls_port": None,
            "public_udp_port": None,
        }
        for ra in radioString.split(" "):
            for txt in desirable_txt.keys():
                if txt in ra:
                    desirable_txt[txt] = ra.split("=")[1]

        return desirable_txt

    def GetRadioFromAvailable(self, serial_no):
        for radio in self.radio_list:
            if radio["serial"] == serial_no:
                return radio
        raise ValueError("Requested serial number not in authorized list")

    def clear_cached_tokens(self):
        """Clear cached OAuth tokens from keyring. Useful for debugging or forcing re-authentication."""
        try:
            keyring.delete_password(self.KEYRING_SERVICE, self.KEYRING_USERNAME)
            print("Cached tokens cleared")
        except Exception as e:
            print(f"Note: No cached tokens to clear ({e})")

    def CloseLink(self):
        self.pingThread.running = False
        self.pingThread.join()  # End thread manually
        # del self
        self.wrapped_server_sock.close()
        self.server_sock.close()

    # def __del__(self):
    # 	self.wrapped_server_sock.close()
    # 	self.server_sock.close()

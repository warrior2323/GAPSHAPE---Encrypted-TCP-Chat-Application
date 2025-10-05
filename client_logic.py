import socket
import threading
from cryptography.fernet import Fernet
import rsa

HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "/quit"

class Client:
    def __init__(self, callbacks):
        """Initializes the client's logic, including networking and cryptography."""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.callbacks = callbacks
        
        # --- Your Cryptography Setup ---
        (self.public_key, self.private_key) = rsa.newkeys(2048)
        self.public_key_pem = self.public_key.save_pkcs1().decode('utf-8')
        self.PUBLIC_KEYS_CACHE = {}
        self.SESSION_KEYS = {}

    def connect(self, server_ip, port, username): 
        """Connects to the server, sends credentials, and starts listening for messages."""
        try:
            self.client.connect((server_ip, port))
            self.client.recv(2048) # Clear the initial "Enter username" prompt from the server
            
            self._send(username)
            self._send(self.public_key_pem)
            
            receive_thread = threading.Thread(target=self._listen_for_messages)
            receive_thread.daemon = True
            receive_thread.start()
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False

    def _send(self, msg):
        """Internal method to encode and send a message with a header."""
        try:
            message = msg.encode(FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b' ' * (HEADER - len(send_length))
            self.client.send(send_length)
            self.client.send(message)
        except (BrokenPipeError, ConnectionResetError):
            self.callbacks.get('on_disconnected', lambda: None)()

    def _listen_for_messages(self):
        """Runs in a background thread to handle all incoming messages."""
        while True:
            try:
                msg_length_str = self.client.recv(HEADER).decode(FORMAT)
                if not msg_length_str: break
                
                msg_length = int(msg_length_str.strip())
                msg = self.client.recv(msg_length).decode(FORMAT)
                
                # --- Your Message Parsing Logic ---
                parts = msg.split(' ', 2)
                command = parts[0]

                if command == "/key" and len(parts) == 3:
                    print("hi /key")
                    username, key_pem = parts[1], parts[2]
                    self.PUBLIC_KEYS_CACHE[username] = rsa.PublicKey.load_pkcs1(key_pem.encode('utf-8'))
                    self.callbacks.get('on_system_message', lambda m: None)(f"[INFO] Received public key for {username}.")
                
                elif command == "/privatemsg" and len(parts) == 3:
                    print("jeevan hai to jiyenge")
                    sender, content = parts[1], parts[2]
                    content_parts = content.split(' ', 1)
                    if len(content_parts) < 2: continue
                    msg_type, data = content_parts[0], content_parts[1]

                    if msg_type == "SESSION_KEY":
                        print("/hi session key")
                        encrypted_session_key = bytes.fromhex(data)
                        session_key = rsa.decrypt(encrypted_session_key, self.private_key)
                        self.SESSION_KEYS[sender] = session_key
                        self.callbacks.get('on_system_message', lambda m: None)(f"[SECURE] Secure session established with {sender}.")
                    
                    elif msg_type == "MESSAGE":

                        if sender in self.SESSION_KEYS:

                            f = Fernet(self.SESSION_KEYS[sender])
                            decrypted_msg = f.decrypt(bytes.fromhex(data)).decode(FORMAT)
                            self.callbacks.get('on_message_received', lambda m: None)(f"[Private from {sender}]: {decrypted_msg}")
                        else:
                            self.callbacks.get('on_system_message', lambda m: None)(f"[ERROR] Received private message from {sender} but no session key is established.")
                else:
                    
                    self.callbacks.get('on_message_received', lambda m: None)(msg)

            except Exception:
                break
        
        self.callbacks.get('on_disconnected', lambda: None)()

    def send_public_message(self, msg):
        """Sends a regular, public message."""
        self._send(msg)

    def send_private_message(self, recipient, message):
        """Handles the full logic for sending an encrypted private message."""
        if recipient not in self.SESSION_KEYS:
            if recipient not in self.PUBLIC_KEYS_CACHE:
                self.callbacks.get('on_system_message', lambda m: None)(f"[INFO] Public key for '{recipient}' not cached. Requesting from server...")
                self._send(f"/getkey {recipient}")
                self.callbacks.get('on_system_message', lambda m: None)("[INFO] Please wait a moment for the key to arrive, then try sending your message again.")
                return

            recipient_public_key = self.PUBLIC_KEYS_CACHE[recipient]
            session_key = Fernet.generate_key()
            self.SESSION_KEYS[recipient] = session_key

            encrypted_session_key = rsa.encrypt(session_key, recipient_public_key)
            self._send(f"/privatemsg {recipient} SESSION_KEY {encrypted_session_key.hex()}")
            self.callbacks.get('on_system_message', lambda m: None)(f"[SECURE] Sent a secure session key to {recipient}.")

        f = Fernet(self.SESSION_KEYS[recipient])
        encrypted_message = f.encrypt(message.encode(FORMAT))
        self._send(f"/privatemsg {recipient} MESSAGE {encrypted_message.hex()}")

    def disconnect(self):
        """Sends the disconnect message to the server."""
        self._send(DISCONNECT_MESSAGE)
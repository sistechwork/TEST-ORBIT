import os
from cryptography.fernet import Fernet
import base64
from hashlib import sha256

class EncryptionService:
    def __init__(self):
        encryption_key = os.environ.get("ENCRYPTION_KEY")
        if not encryption_key:
            encryption_key = os.environ.get("SESSION_SECRET", "default-secret-key-change-me")
        
        key_bytes = sha256(encryption_key.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))
    
    def encrypt(self, value):
        if not value:
            return ""
        return self.fernet.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value):
        if not encrypted_value:
            return ""
        try:
            return self.fernet.decrypt(encrypted_value.encode()).decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""

encryption_service = EncryptionService()

"""
AES-256 Encryption Module
Handles encryption/decryption of sensitive patient data fields
"""

import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# Load or generate AES key (in production: use proper KMS)
KEY_FILE = os.path.join(os.path.dirname(__file__), 'instance', 'encryption.key')

def _get_or_create_key():
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    key = get_random_bytes(32)  # 256-bit AES key
    with open(KEY_FILE, 'wb') as f:
        f.write(key)
    # Restrict file permissions (Unix)
    try:
        os.chmod(KEY_FILE, 0o600)
    except Exception:
        pass
    return key

AES_KEY = _get_or_create_key()

def encrypt_field(plaintext: str) -> str:
    """Encrypt a string field using AES-256-CBC."""
    if not plaintext:
        return ''
    try:
        iv = get_random_bytes(16)
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        padded = pad(plaintext.encode('utf-8'), AES.block_size)
        ciphertext = cipher.encrypt(padded)
        # Store as base64(iv + ciphertext)
        combined = base64.b64encode(iv + ciphertext).decode('utf-8')
        return combined
    except Exception:
        return ''

def decrypt_field(encrypted: str) -> str:
    """Decrypt an AES-256-CBC encrypted field."""
    if not encrypted:
        return ''
    try:
        raw = base64.b64decode(encrypted)
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted.decode('utf-8')
    except Exception:
        return '[DECRYPTION ERROR]'

"""Encryption utilities for secure data storage."""

import base64
import os
from typing import Optional

import keyring
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""

    SERVICE_NAME = "email-summarizer"
    KEY_NAME = "encryption_key"
    SALT_NAME = "encryption_salt"

    def __init__(self):
        """Initialize encryption manager."""
        self._fernet: Optional[Fernet] = None

    def _get_or_create_key(self) -> bytes:
        """Get encryption key from keyring or create new one.

        Returns:
            Encryption key bytes
        """
        # Try to get existing key
        key_str = keyring.get_password(self.SERVICE_NAME, self.KEY_NAME)

        if key_str:
            return base64.urlsafe_b64decode(key_str.encode())

        # Generate new key
        key = Fernet.generate_key()

        # Store in keyring
        key_str = base64.urlsafe_b64encode(key).decode()
        keyring.set_password(self.SERVICE_NAME, self.KEY_NAME, key_str)

        return key

    def _get_fernet(self) -> Fernet:
        """Get or create Fernet cipher instance.

        Returns:
            Fernet cipher instance
        """
        if self._fernet is None:
            key = self._get_or_create_key()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, data: str) -> str:
        """Encrypt string data.

        Args:
            data: Plain text string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        fernet = self._get_fernet()
        encrypted_bytes = fernet.encrypt(data.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string data.

        Args:
            encrypted_data: Base64-encoded encrypted string

        Returns:
            Decrypted plain text string

        Raises:
            ValueError: If decryption fails
        """
        try:
            fernet = self._get_fernet()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt binary data.

        Args:
            data: Binary data to encrypt

        Returns:
            Encrypted binary data
        """
        fernet = self._get_fernet()
        return fernet.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt encrypted binary data.

        Args:
            encrypted_data: Encrypted binary data

        Returns:
            Decrypted binary data

        Raises:
            ValueError: If decryption fails
        """
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(encrypted_data)
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    @staticmethod
    def derive_key_from_passphrase(
        passphrase: str, salt: Optional[bytes] = None
    ) -> tuple[bytes, bytes]:
        """Derive encryption key from user passphrase.

        Args:
            passphrase: User-provided passphrase
            salt: Optional salt bytes. If None, generates new salt.

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = kdf.derive(passphrase.encode("utf-8"))

        return key, salt

    def reset_encryption_key(self) -> None:
        """Delete encryption key from keyring.

        Warning: This will make all encrypted data unrecoverable!
        """
        try:
            keyring.delete_password(self.SERVICE_NAME, self.KEY_NAME)
            keyring.delete_password(self.SERVICE_NAME, self.SALT_NAME)
        except keyring.errors.PasswordDeleteError:
            pass  # Key doesn't exist

        self._fernet = None


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get global encryption manager instance.

    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt(data: str) -> str:
    """Convenience function to encrypt string data.

    Args:
        data: Plain text string

    Returns:
        Encrypted string
    """
    return get_encryption_manager().encrypt(data)


def decrypt(encrypted_data: str) -> str:
    """Convenience function to decrypt string data.

    Args:
        encrypted_data: Encrypted string

    Returns:
        Decrypted plain text string
    """
    return get_encryption_manager().decrypt(encrypted_data)

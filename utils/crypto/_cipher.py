from django.conf import settings
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64
import hashlib

SALT_PREFIX = b"Salted__"


def get_key_and_iv(password, salt, keylen=32, ivlen=AES.block_size):
    password = password.encode('ascii', 'ignore')

    try:
        tmp = keyiv = b''
        while len(keyiv) < keylen + ivlen:
            tmp = hashlib.md5(tmp + password + salt).digest()
            keyiv += tmp
        return keyiv[:keylen], keyiv[keylen:keylen + ivlen]
    except UnicodeDecodeError:
        return None, None


class OpensslAESCipher:
    def __init__(self, passphrase):
        self.__passphrase = passphrase

    def encrypt(self, message):
        message = pad(message.encode(), AES.block_size)
        salt = get_random_bytes(AES.block_size - len(SALT_PREFIX))
        key, iv = get_key_and_iv(self.__passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return SALT_PREFIX + salt + cipher.encrypt(message)

    def b64encrypt(self, message):
        encrypted_data = self.encrypt(message)
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, data):
        salt = data[len(SALT_PREFIX):AES.block_size]
        key, iv = get_key_and_iv(self.__passphrase, salt)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(data[AES.block_size:]), AES.block_size).decode()

    def b64decrypt(self, b64string):
        data = base64.b64decode(b64string.encode())
        return self.decrypt(data)


cipher = OpensslAESCipher(settings.CRYPTO_AES_PASSPHRASE)

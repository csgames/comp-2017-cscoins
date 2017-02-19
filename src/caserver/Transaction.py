import decimal
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5

class Transaction:
    def __init__(self, id, source, recipient, amount, timestamp=0):
        self.id = id
        self.source = source
        self.recipient = recipient
        self.amount = amount
        self.timestamp = int(timestamp)
        self.signature = ""

    def sign_with(self, source_private_key):
        message = "{0},{1},{2:.5f}".format(self.source, self.recipient, self.amount)
        hasher = SHA256.new()
        hasher.update(message.encode('ascii'))
        signer = PKCS1_v1_5.new(source_private_key)
        bytes = signer.sign(hasher)
        self.signature = ""
        for b in bytes:
            self.signature += "{0:02x}".format(b)

    def verify_signature(self, source_public_key):
        message = "{0},{1},{2:.5f}".format(self.source, self.recipient, self.amount)
        hasher = SHA256.new()
        hasher.update(message.encode('ascii'))
        signer = PKCS1_v1_5.new(source_public_key)
        sign_bytes = bytes.fromhex(self.signature)

        return signer.verify(hasher, sign_bytes)

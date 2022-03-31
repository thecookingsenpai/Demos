import json
import binascii
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

class TRANSACTION:
    def __init__(self) -> None:
        self.data = {
            "from": "",
            "to": "",
            "value": 0,
            "instructions": {}
        }
        self.signature = ""
        self.signature_ascii = ""
    
    def sign(self, signing_key):
        preparatory_hash = SHA256.new(self.data)
        self.signature = pkcs1_15.new(signing_key).sign(preparatory_hash)
        self.signature_ascii = binascii.hexlify(self.signature).decode("utf-8")
    
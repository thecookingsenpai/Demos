import time
import communications
import pickle
import hashlib

class block:
    
    # Except for the genesis one, the blocks contains the previous block hash.
    # This is a classic anti tamper method: any spoofing will result in a
    # fork of the chain and thus in a rejection from the other nodes
    def __init__(self, old_block) -> None:
        self.number = 0
        self.timestamp = time.time()
        self.txs = {}
        self.block_hash = ""
        self.previous_hash = old_block.block_hash
        self.validator_0
        self.validator_1
        self.validator_2
        self.validator_3
        self.validator_4
        self.validator_5
        self.validator_6
        
    # Every added tx is hashed and the correspondant hash is added to the proper
    # variable. Containing the nonce, a tx is always different from the same one
    # even with the same address
    def add_tx(self, tx):
        if isinstance(tx, communications.tx):
            binary_tx = pickle.dumps(tx)
            hashof = hashlib.sha512(binary_tx).hexdigest() 
            self.txs[hashof] = binary_tx
    
    # The block_hash is generated containing the whole block object.
    # This hash is rebuilt once again and compared on submission, spotting
    # any kind of spoofing on the fly
    def generate_hash(self):
        hashed = hashlib.sha512(self).hexdigest()
        self.block_hash = hashed
        
class blockchain:
    def __init__(self) -> None:
        self.last_block
        self.blocks = []
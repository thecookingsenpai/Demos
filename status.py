from tinydb import TinyDB, Query

# STATUS is a class that manages statuses in the chain, included status changes.
# Generally speaking, "Return False, message" is an execution reverted for some reason.
# Return True is emitted on status change confirmed

class STATUS:
    
    def __init__(self, path="./node_data/blockchain.json") -> None:
        self.path = path
        self.db = TinyDB(path)
        self.extract = Query()
        self.chaindata = []
    
    def get_chain(self):
        query = self.db.search(self.extract.chain)
        return query 
    
    def mine(self, block, genesis=False):
        block_json = {}
        if not genesis:
            block_json["block_number"] = block.block_number
        else:
             block_json["block_number"] = 0
        block_json["tx_list"] = block.tx_list
        block_json["signers"] = block.signers
        block_json["signing_proofs"] = block.signing_proofs
        block_json["timestamp"] = block.timestamp
        self.db.insert(block_json)
        
    # Basic state change: usually operate in a pair with add and sub respectively
    def change_balance(self, address, direction, quantity):
        entry = self.db.search((self.extract.type == 'account') & (self.extract.address == address))
        if len(entry) == 0:
            self.db.insert({"type": "account", "address": address, "balance": 0})
            balance = 0
        elif len(entry) == 1:
            balance = entry[0].get("balance")
        else:
            return False, "WTF"
        # Mathematical operations and state preparation
        if direction == "add":
            balance += quantity
        elif direction == "sub":
            if balance < quantity:
                return False, "Not enough funds"
            balance -= quantity          
        # Had no problems, so editing the result
        self.db.update({"balance": (balance)}, (self.extract.type == 'account') & (self.extract.address == address))
        return  True, "Success"
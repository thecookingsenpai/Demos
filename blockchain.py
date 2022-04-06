import blocks
import transactions
import os
import pickle
import status
import json

class BLOCKCHAIN:
    def __init__(self, genesis="genesis.json") -> None:
        # Trying to load existing chain
        self.status = status.STATUS()
        try:
            self.last_block = self.status.chaindata[0].get("block_number")
        except:
            self.last_block = 0
        if self.last_block == 0:
            # Genesis
            with open(genesis, "r") as genesis_file:
                self.genesis = json.loads(genesis_file.read())
                self.initialize_first_block()
        # Genesis variables
        self.genesis_timestamp = self.genesis.get("timestamp")
    
    def initialize_first_block(self):
        # Conditions
        if not isinstance(self.genesis, dict):
            return False, "Genesis is not readable"
        if not self.last_block == 0:
            return False, "Block number is too high"
        # All the blocks
        are_blocks = self.status.db.search(self.status.extract.block_number == "*")
        if not len(are_blocks) == 0:
            return False, "Blockchain isn't empty"
        # Create the block and switch the last_block to 1
        first_block = blocks.BLOCK()
        genesis_tx = transactions.TRANSACTION()
        genesis_tx.data["instructions"] = self.genesis
        self.last_block = 1
        self.status.mine(first_block, genesis=True)

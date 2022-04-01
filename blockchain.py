import blocks
import transactions
import os
import pickle


class BLOCKCHAIN:
    def __init__(self, genesis="genesis.json") -> None:
        with open(genesis, "r") as genesis_file:
            self.genesis = genesis_file.read()
            self.initialize_first_block()
        self.blocks = []
        self.last_block = 0
        self.last_chunk = 0
        # Genesis variables
        # A chunk is a file containing chunk_size blocks
        self.chunk_size = self.genesis.get("chunk_size")
        self.genesis_timestamp = self.genesis.get("timestamp")
    
    def initialize_first_block(self):
        # Conditions
        if not isinstance(self.genesis, dict):
            return False, "Genesis is not readable"
        if not self.last_block == 0 or not self.last_chunk == 0:
            return False, "Block number is too high"
        if not len(self.blocks) == 0:
            return False, "Blockchain isn't empty"
        # Create the block, add init to the first chunk and switch the last_block to 1
        first_block = blocks.BLOCK()
        genesis_tx = transactions.TRANSACTION()
        genesis_tx.data["instructions"] = self.genesis
        self.last_block = 1
        self.blocks.append(first_block)
    
    def add_chunk_to_chain(self):
        destination = "node_data/chain/" + "chunk_" + str(self.last_chunk)
        empty_new = "node_data/chain/" + "chunk_" + str(self.last_chunk + 1)
        # This chunk is already written
        if os.path.exists(destination) and not(os.stat(destination).st_size == 0):            
            return False, "Chunk already taken"
        # Writing the chunk and unloading memory
        with open(destination, "wb") as chunk_file:
            pickle.dump(chunk_file, self.blocks)
        self.blocks = []
        # Creating the empty one to avoid filled chunk locking
        with open(empty_new, "a") as empty:
            pass
        # Writing the number
        with open("node_data/chain/last_chunk", "w+") as counter:
            counter.write(str(self.last_chunk))
        
    def load_chunk_from_chain(self, chunk_number):
        with open("node_data/chunk_" + str(chunk_number), "rb") as chunk_file:
            loaded_chunk = pickle.load(chunk_file)
            return loaded_chunk
        
    def get_chunk_from_block_number(self, number):
        provisioned_chunk = 0
        remaining = number
        # How many times chunk_size is in total number of chunks
        while (remaining > 0):
            provisioned_chunk += 1
            remaining -= self.chunk_size
        return (provisioned_chunk - 1)
    
    # Get and load the last chunk
    def get_last_chunk(self, load=False):
        with open("node_data/chain/last_chunk", "r") as counter:
            if not load:
                return counter.read()
            else:
                # Mimick the last chunk, block list and last block
                self.last_chunk = counter.read()
                content = self.load_chunk_from_chain(counter.read())
                self.blocks = content
                self.last_block = content[-1].block_number
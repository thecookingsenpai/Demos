from copyreg import pickle
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import binascii
import requests
import blocks
import consensus
import blockchain
import time
import json
import random
import os
import executor

class ENTITY:
    
    # Subclass to interact
    class OtherNode:
        def __init__(self, ip: str, port: int):
            self.base_url = "http://" + str(ip) + ":" + str(port) 
        
        # Time sync
        def sync(self):
            dest_url = self.base_url + "/time"
            response = requests.get(dest_url)
            time_json = json.loads(response.text)
            return time_json.get("time")
    
        # Communication method
        def transact(self, tx):
            endpoint = self.base_url + "/transactions"
            # Building a json tx data
            tx_data_signed = {
                "data": tx.data,
                "signature": tx.signature
            }
            # Sending to this node entity
            request_outcome = requests.post(endpoint, json=tx_data_signed)
            if not request_outcome.status_code == 200:
                return False
            else:
                return True

        def propagate_block(self, block):
            if not isinstance(block, blocks.BLOCK):
                return False, "Malformed block"
            endpoint = self.base_url + "/blocks"
            # Preparing json to send
            block_json = {
                "block_number": block.block_number,
                "tx_lst": block.tx_list,
                "signers": block.signers,
                "signing_proofs": block.signing_proofs
            }
            request_outcome = requests.post(endpoint, json=block_json)
            if not request_outcome.status_code == 200:
                return False
            else:
                return True
        
        # Send a votation for a consensus round
        def vote_on(self, candidate, address, signature):
            endpoint = self.base_url + "/voting"
            # Preparing json to send
            block_json = {
                "from": address,
                "vote": candidate,
                "signature": signature
            }
            request_outcome = requests.post(endpoint, json=request_outcome)
            if not request_outcome.status_code == 200:
                return False
            else:
                return True
    
    # Proper node structure
    def __init__(self, existing_private="", to_file=False, peerFile="", genesis="genesis.json") -> None:
        # Load genesis node option
        self.checkpoint_time = time.time()
        with open(genesis, "r") as genesis_file:
            self.genesis = json.loads(genesis_file.read())
            self.block_time = self.genesis.get("block_time")
        # Creating or restoring a wallet
        if existing_private=="":
            if not os.path.exists("public.pub"):
                self.key = RSA.generate(2048)
                self.pubkey = self.key.publickey()
                if to_file:      
                    with open('public.pub','w') as f:
                        f.write(self.pubkey.exportKey('PEM'))
                    with open('private.pem','w') as f:
                        f.write(self.key.exportKey('PEM'))
                else:
                    print("Your public address is: " + str(hex(self.pubkey.n)))
                    print("\nWARNING: Your private key follows: do not give it to anyone.")
                    print(hex(self.key.n))
        else:
            with open(existing_private) as f:
                self.key = RSA.import_key(f.read())
                self.pubkey = self.key.publicKey()
                
        # Importing eventual peers (with structure: [[ip, port], [ip, port], ...])
        if not peerFile=="":
            with open(peerFile) as peers:
                self.peers = peers.read()
                syncing_peer = self.OtherNode(peers[0][0], str(peers[0][1]))
                self.start_time = time.time()
                self.synced_time = syncing_peer.sync()
        else:
            self.start_time = time.time()
            self.peers = []
        # Load the consensus method
        self.democracy = consensus.CONSENSUS()
        self.agreement_pool = consensus.AGREEMENT_POOL()
        # Prepare the data to handle the whole chain
        self.chain = blockchain.BLOCKCHAIN()
    
    # Given a transaction it validate the signature
    def validate_signature(self,public_key, transaction):
        usable_key = RSA.import_key(public_key)
        hashed_tx = SHA256.new(transaction.get("data"))
        try:
            pkcs1_15.new(usable_key).verify(hashed_tx, transaction.get("signature"))
            return True
        except:
            return False
        
    # Broadcast a tx to a list of nodes
    def broadcast(self, tx, specified_nodes = []):
        nodes = specified_nodes.extend(self.peers)
        for node in nodes:
            try:
                destination = self.OtherNode(node[0], node[1])
                destination.transact(tx)
                return 200, "Broadcasted to " + node[0]
            except requests.ConnectionError:
                return 404, "Node " + node[0] + " is offline"    
    
    # Retrieve pickled mempool
    def get_txs_from_memory(self):
        with open("node_data/mempool", "rb") as mempool:
            return mempool.read()
        
    # Register the execution of a tx
    def execute_tx(tx):        
        tx_data = tx.get("data")
        # "instructions" key contains (at the moment 1) methods
        instructions = tx_data.get("instructions")
        total_instructions = len(instructions)
        for operation in instructions:
            type_of = instructions.get(operation)
            # Arguments are then used to build an execute class
            arguments = instructions.get("arguments")
            execute = executor.EXECUTE(type_of, arguments)
            # Which then is ran
            get_result, get_why = execute.run()
            if not get_result:
                return False, get_why
            # If we are here, everything is ok
            
        
                
        
    # Retrieve pickled mempool
    def clear_mempool(self):
        os.remove("node_data/mempool")
        with open("node_data/mempool", "wb") as mempool:
            mempool.write("MEMPOOL\n".encode("UTF-8"))
        
    # Store a valid tx in the mempool
    def mempool_tx(self, tx_json):
       actual_mempool =pickle.load(self.get_txs_from_memory())
       new_mempool = actual_mempool.append(tx_json)
       with open("node_data/mempool", "wb") as mempool:
           pickle.dump(mempool, new_mempool)
    
    def create_block(self):
        tx_list = self.get_txs_from_memory()
        if len(tx_list) == 0:
            return False, "No tx"
        block = blocks.BLOCK()
        next_block = self.chain.last_block+1
        block.block_number = next_block
        block.tx_list = tx_list
        block.signers.append(self.pubkey)
        block.signing_proofs.append(self.sign_data(block.block_number))
        return block
               
    def broadcast_block(self, block, specified_nodes = []):
        nodes = specified_nodes.extend(self.peers)
        for node in nodes:
            try:
                destination = self.OtherNode(node[0], node[1])
                destination.propagate_block(block)
            except requests.ConnectionError:
                pass  
    
    # Random extraction
    def decide_votation(self):
        range_max = len(self.peers) - 1
        indication = random.randint(0, range_max)
        candidate = self.peers[indication]
        self.broadcast_vote(candidate)
    
    def broadcast_vote(self, candidate):
        # Sign the vote
        vote_to_sign = {
            "from": self.pubkey,
            "vote": candidate
        }
        signature = self.sign_data(vote_to_sign)  
        # Broadcast to all
        for node in self.peers:
            try:
                destination = self.OtherNode(node[0], node[1])
                destination.vote_on(candidate, self.pubkey, signature)
                return 200, "Broadcasted to " + node[0]
            except requests.ConnectionError:
                return 404, "Node " + node[0] + " is offline"
        self.democracy.has_voted.append(self.pubkey)
        
    # To be valid, a vote must be signed and unique
    def validate_vote(self, voter, votation, signature):
        if voter in self.democracy.has_voted:
            return False
        usable_key = RSA.import_key(voter)
        hashed_tx = SHA256.new(votation)
        try:
            pkcs1_15.new(usable_key).verify(hashed_tx, signature)
            return True
        except:
            return False
            
            
    def sign_data(self, data):
        signing_key = self.key
        preparatory_hash = SHA256.new(self.data)
        self.signature = pkcs1_15.new(signing_key).sign(preparatory_hash)
        self.signature_ascii = binascii.hexlify(self.signature).decode("utf-8")
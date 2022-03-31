from base64 import decode
import ipfsApi
# import socket programming library
import time
from sympy import public
import zmq
import os
from ecdsa import SigningKey, VerifyingKey
from hashlib import sha512
import cPickle as pickle
from types.api import *
from types.communications import *
from types import *
import consensus
import types.blocks as blocks
import pathlib
import hashlib

class node:

    # Keys creation and identity

    def __init__(self) -> None:
        # Fingerprinting the situation to add a tamper proof method
        working_dir = pathlib.Path(__file__).parent.resolve()
        hashes = []
        modules = ["federator.py", "consensus.py", "types/communications.py", "types/blocks.py"]
        for to_check in modules:
            with open(working_dir + "/"  + to_check, "r") as current_file:
                buffer = current_file.read()
                hashes.append(hashlib.sha512(buffer).hexdigest())
        self.integrity = hashes
        # IPFS node MUST be running
        self.api = ipfsApi.Client('127.0.0.1', 5001)
        # Voting prototype
        self.votes = ""
        self.voting = False
        # Peers and bootstrappeers starts empty
        self.peers = []
        self.bootstrappeers = []
        # Declaring a communicator
        self.communicator = communicate() 
        # Preparing server side things
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:9080")
        # Personal block storage (index is block num)
        self.block_list = []
        self.created = time.time()
        # Nonce
        self.nonce = 0        
        # Loading identities
        if os.path.exists(".ipfschain/priv_key") and os.path.exists(".ipfschain/pub_key"):
            priv_handle = open(".ipfschain/priv_key", "rb")
            self.sk = SigningKey.from_string(priv_handle.read())
            self.sk_string = self.sk.to_string()
            pub_handle = open(".ipfschain/pub_key", "rb") 
            self.vk = VerifyingKey.from_string(pub_handle.read())
            self.vk_string = self.vk.to_string()
        else:
            self.sk = SigningKey.generate() # uses NIST192p
            self.sk_string = self.sk.to_string()
            self.vk = self.sk.verifying_key
            self.vk_string = self.vk.to_string()
            with open(".ipfschain/priv_key", "wb+") as keyfile:
                keyfile.write(self.sk_string)
            with open(".ipfschain/pub_key", "wb+") as keyfile:
                keyfile.write(self.vk_string)
            # PRINT
        
        print(self.sk_string.hex()) 
        print(self.vk_string.hex())
 
    

    # Federation management
    
    def set_peer(self, peer):
        if not peer in self.peers:
            self.peers.append(peer)
            return "OK", ""
        else:
            return "NOK", "Peer is already in list"

    def unset_peer(self, peer):
        if peer in self.peers:
            index = 0
            for p in self.peers:
                if peer in p:
                    self.peers.delete(index)
                    return "OK", ""
                index+=1
            return "NOK", "Peer not found"
        else:
            return "NOK", "Peer not found"
    
    def bootstrap_peers(self, from_peer=0):
        try:
            selected_peer = self.peers[from_peer]
            straplist = self.communicator.instruct_peer(selected_peer, "BOOTSTRAP")
            if len(straplist) > 0:
                for new_peer in straplist:
                    self.set_peer(new_peer)
                return "OK", "Added " + str(len(straplist)) + " peers"
        except:
            return "NOK", "Peer not found"
        
    # Assured the message is valid, it is executed and the reply is sent unencrypted 
    # to the original sender
    def execute_data(self, data, peer):
        method = data.get["method"]
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://" + peer + ":9080")
        
        if method == "bootstrap":
            if len(self.peers) > 0:
                self.socket.send(pickle.dumps(node.peers, 1))
            else:
                self.socket.send(b"")
        else:           
                self.socket.send(b"Received, thanks... but how to '" + str(cmd) + "' ?")    

    def download_from_federates(self, hash):
        pass

    def become_federated(self):
        pass
    
    # Consensus system

    def consensus_control(self):
        pass

    def consensus_candidate(self):
        pass

    def consensus_vote(self, proposal, voting_team):
        if len(proposal.already_signed ) < 6 and not(proposal.already_signed[self.public_key]):
            pass
            
        

    # Data elaboration and instruction
    # For reference:
    # data need to be sent as serialized json data, using pickle as shown
    # The format is, for example:
    # {
    #   "type": "cmd",
    #   "prompt": "inspect shard 10",
    #   "input": "some other data"
    # }
        
    def upload_to_ipfs(self, file):    
        res = self.api.add(file)
        return res


if __name__ == '__main__':
    # Eternal loop to receive and act
    entity = node()
    while True:
        try:
            # Are we voting?
            if entity.voting:
                if entity.votes == "":
                    # This method initialize (if is not initalized, the voting)
                    entity.votes = consensus.vote()
                # Preparing server side things
                encoded_message = entity.votes.socket.recv(flags=zmq.NOBLOCK)
                # If there is something, verify validity and elaborate
                message = pickle.loads(encoded_message)
                status, tx_data, route = communicator.elaborate_from_peer(message, entity)
                # Elaborate voting once the message is considered valid
                if status == "OK":
                    success, report = entity.votes.elaborate_vote(message)
                
                # Vote through a tx. The return result is already pre filled by
                # the voting class, needs only to be signed and routed to the voting_pool
                if not entity.votes.voted:
                    result = entity.votes.do_vote(entity.nonce)
                    entity.nonce += 1
                    result.sender = entity.public
                    result.to = entity.votes.voting_pool
                    result.signature = communicator.sign_message(result, entity.sk)
                    result.send(result.to, False)
                    entity.votes.register_vote()
                    
                # Back to checking voting
                continue
            
            # Cleanup voting
            if not entity.votes == "":
                entity.votes.votebook = {}
                entity.votes.voted = False
                entity.votes == ""

            # If we are not voting, here is the normal function
            encoded_message = entity.socket.recv(flags=zmq.NOBLOCK)
            message = pickle.loads(encoded_message)
            #a message has been received
            print("Message received:" + str(message))
            # Command messages are sent to elaboration
            if message.get("type") == "cmd":
                cmd = message.get("prompt")
                print("Command is: " + cmd)
                status, tx_data, route = communicator.elaborate_from_peer(message, entity)
                if status == "OK":
                    node.execute_data(tx_data, route)
            # Fallback for replying gracefully
            else:
                entity.socket = entity.context.socket(zmq.REQ)
                entity.socket.connect("tcp://" + route + ":9080")
                entity.socket.send(b"Received, thanks. However, I don't know what to do.")
        # Non blocking logic
        except zmq.Again as e:
            pass

        # perform other stuff
        time.sleep(1)


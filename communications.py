import pickle
import zmq
import time
# Example:
# transaction = tx()
# transaction.data = [...]
# [...]
# signed_tx = communications.sign_message(transaction, pk)
# transaction.signed = signed_tx
# transaction.send(peer)
class tx:
    def __init__(self) -> None:
        self.data = ""
        self.nonce = 0
        self.to = ""
        self.sender = ""
        self.signed = ""
        self.communicator = communicate()
        self.mode = ""
        self.closed = False
        self.timestamp = time.time
        
    def send(self, peer, closed):        
        # Expect an already signed tx object and a peer
        self. closed = closed
        self.communicator.instruct_peer(peer, pickle.dumps(self))

class communicate():
    def __init__(self) -> None:
        pass
    # Sign / Verify functions

    # sign expect a key
    def sign_message(self, msg, sk):
        signature =  sk.sign(msg)
        return signature

    # public must be a valid vk
    def verify_message(self, msg, public, signature):
        try:
            public.verify(signature, msg)
            return "OK", ""
        except:
            return "NOK", "Unverified"
    
    # Instruct peer is the method that allows class tx to execute transactions
    # so the message need to be signed properly. Another point of view: instruct_peer
    # send things that are executed (so need auth), responses are harmless and 
    # ignored if not to check an expected outcome
    def instruct_peer(self, peer, message):
        encoded_message = pickle.dumps(message, -1)
        # Contacting a peer on the right port
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://" + peer + ":9080")
        self.socket.send(encoded_message)
        #  Get the reply.
        if not message.closed:
            message = self.socket.recv()
            decoded_message = pickle.loads(message)
            resp = "Received reply: " + str(decoded_message)
            return resp

    
    # Example
    # cmd = [...]
    # cmd.mode== "bootstrap"
    # cmd.data.get("method") == "bootstrap"
    
    def elaborate_from_peer(self, encoded_cmd):
        cmd = pickle.loads(encoded_cmd)
        if not isinstance(cmd, tx):
            return "NOK", "TX is invalid", ""
        if not isinstance(cmd.data, list):
                return "NOK", "Corrupted message", ""
        # Verify signature
        verification = self.verify_message(cmd, cmd.public, 
                                            cmd.signature)
        if not verification == "OK":
            return "NOK", "Unverified signature", ""
        
        # Message accepted, parsing
        if cmd.mode == "COMMAND":
           return "OK", cmd.data, cmd.sender
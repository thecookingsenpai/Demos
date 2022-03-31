from distutils.log import debug
from flask import Flask, request
import entity
import transactions
import blocks
import blockchain
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15
import time
import multiprocessing

node = entity.ENTITY(existing_private="account/keystore/accountPrivateKey")

app = Flask(__name__)

# API to receive votes
@app.route("/vote", methods=['POST'])
def process_json():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # The vote is validated
        actual_vote = {
            "from": json.get("from"),
            "vote": json.get("vote")
        }
        valid = node.validate_vote(json.get("from"), actual_vote, json.get("signature"))
        # If is valid, the vote is counted
        if valid:
            node.democracy.has_voted.append(actual_vote.get("from"))
            node.democracy.votes[actual_vote.get("from")] = actual_vote.get("vote")
            return True, "Ok"
        else:
            return False, "Bad signature"
    

def is_a_tx(json):
    try:
        if "data" in json.keys() and "signature" in json.keys:
            if "from" in json.get("data") and \
               "to" in json.get("data") and \
               "value" in json.get("data") and \
               "instructions" in json.get("data"):
                    return True
    except:
        return False    

# API to receive transactions (require a json sent with { "data": tx_json, "signature": sign} )
@app.route("/transactions", methods=['POST'])
def process_json():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # The transaction is validated
        if is_a_tx(json):
            # A transaction object is forged
            tx = transactions.TRANSACTION()
            tx.data = json
            # Signature is verified
            valid = node.validate_signature(tx.data.get("from"), tx)
            if valid:
                node.mempool_tx(json)
                return "Ok!", 200
            else:
                return "Bad signature", 403
        else:
            return "Not a valid tx!", 400
    else:
        return 'Content-Type not supported!', 400
    

def validate_signatures(signers, proofs):
    # Without wasting time, lengths need to be the same
    if not len(signers) == len(proofs):
        return False
    # Parse signers and proofs to determine if are legit
    cursor = 0
    for sign in signers:
        usable_key = RSA.import_key(sign)
        hashed_proof = SHA256.new(proofs[cursor])
        try:
            pkcs1_15.new(usable_key).verify(hashed_proof, signers[cursor])
        except:
            return False
        cursor += 1
    return True
    
@app.route("/blocks", methods=['POST'])
def validate_block():
    content = request.json
    if not "block_number" in content or not "signers" in content \
        or not "tx_list" in content or not "signing_proofs"in content:
            return False, "Malformed block received"
    # Loading the json into an actual block
    loaded_block = blocks.BLOCK()
    loaded_block.block_number = content.get("block_number")
    loaded_block.tx_list = content.get("tx_list")
    loaded_block.signers = content.get("signers")
    loaded_block.signing_proofs = content.get("signing_proof")
    # Ensuring signature validity
    result = self.validate_signatures(loaded_block.signers, loaded_block.signing_proofs)
    if not result:
        return False, "Signatures are incorrect"
    # Load blockchain status in memory to add the chunk
    chain_handler = blockchain.BLOCKCHAIN()  
    chain_handler.get_last_chunk(load=True)
    # Adding this block to the chunk and checking if it needs to be written 
    chain_handler.blocks.append(loaded_block)
    if len(chain_handler.blocks) > chain_handler.chunk_size:
        chain_handler.add_chunk_to_chain()
        
@app.route("/time", methods=['GET'])
def time_response():
    return {
        "time": str(time.time)
    }
    
# While the rpc is waiting, a continuos process is available to perform tasks
def heartbeat():
    forge_time = False
    while True:
        time.sleep(1)
        # TODO is hardcoded to false while consensus is still in development
        if forge_time:
            pass
        
# Booting the node
if __name__ == "__main__":
    # A joined subprocess ensure non blocking tasks
    beat = multiprocessing.Process(target=heartbeat)
    beat.start()
    app.run(debug=True, use_reloader=False)
    beat.join()
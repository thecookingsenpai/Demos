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
from multiprocessing import connection
from gevent.pywsgi import WSGIServer
import votes

node = entity.ENTITY()#existing_private="account/keystore/accountPrivateKey")
vote = votes.VOTE()

forge_period = False

app = Flask(__name__)

  ################################################################################
 ######################## SMART CONTRACTS #######################################
################################################################################


  ################################################################################
 ######################## TRANSACTIONS ##########################################
################################################################################

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
                print("Accepted tx " + json.get("signature"))
                return "Ok!", 200
            else:
                print("Bad signature (403)")
                return "Bad signature", 403
        else:
            print("Not a TX (400)")
            return "Not a valid tx!", 400
    else:
        print("Content unsupported (400)")
        return 'Content-Type not supported!', 400

  ################################################################################
 ######################## VOTING ################################################
################################################################################

# API to receive votes
@app.route("/vote", methods=['POST'])
def process_vote_json():
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
            print("Voting succeeded.")
            return True, "Ok"
        else:
            print("Invalid signature")
            return False, "Bad signature"
                 
# Wait for the vote to be finished (thanks to multiprocessing, still receiving new votes)
def wait_for_vote_finish(self):
    timeout = 10.000
    while not vote.has_vote_finish(node.democracy):
        timer += 0.300
        if timer > timeout:
            return False, "Timeout"
    return True, "Finished"
        
def wait_for_validation():
    timeout = 10.000
    step = 0.333
    counter = 0.000
    going = False
    # Keep checking for values of validators in the pool
    while counter < timeout:
        counter += step
        for validator in node.agreement_pool:
            value = node.agreement_pool.get(validator)
            if value == "":
                # Detected an empty one
                going = True
        # Completed
        if not going:
            break
    # Timeout
    if going:
        return False, "Timeout", []
    # Coherency check
    else:
        coherency_status, message, penalities = node.agreement_pool.coherency()
        return coherency_status, message, penalities


# Voting interface
def voting_routine():
    # Vote for a candidate and broadcast it
    candidate = node.decide_votation()
    node.broadcast_vote(candidate)
    # Cycle until everybody voted or timed out
    success, reason = wait_for_vote_finish()
    if not success:
        print("Voting failed: " + reason)
        return False, "Voting failed: " + str(reason)
    else:
        print("Votation done!")
        # Determine winners
        validators, controllers = node.democracy.count_winners()
        # If is a validator or controller, 
        if node.pubkey in validators or node.pubkey in controllers:
            proposed_block = node.create_block()
            node.broadcast_block(proposed_block)
            result, valid_block, penalities = wait_for_validation()
        else:
            # Cycle until the validators did their job
            result, valid_block, penalities = wait_for_validation()
        # Accept block and execute all the tx
        if result:
            for tx in valid_block.tx_list:
                success, result = node.execute_tx(tx)
                if not success:
                    result = "Execution reverted: " + result      
                valid_block.tx_result.append(result)
                    
            node.db.insert(valid_block)
            # TODO just record penalties
            # Clear the mempool to not include double tx
            node.clear_mempool()
        # Ignore this consensus
        else:
            pass
        
# If and only if a validator propose, the block is registered in the agreement_pool
#@app.route("/blocks", methods=['POST'])
def accpet_validated_block(content):
    if not "block_number" in content or not "signer" in content \
        or not "tx_list" in content or not "signing_proof"in content:
            print("Malformed block received")
            return False, "Malformed block received"
    # Loading the json into an actual block
    loaded_block = blocks.BLOCK()
    loaded_block.block_number = content.get("block_number")
    loaded_block.tx_list = content.get("tx_list")
    loaded_block.signer = content.get("signer")
    loaded_block.signing_proof = content.get("signing_proof")
    # Ensuring signature validity
    result = node.validate_signatures(loaded_block.signer, loaded_block.signing_proof)
    if not result:
        print("Incorrect signatures, refusing to continue")
        return False, "Signatures are incorrect"
    # Populate the agreement pool with a new block on the first free validator
    for validator in node.agreement_pool:
        if node.agreement_pool.get(validator) == "":
            node.agreement_pool[validator]["from"] = loaded_block.signer
            node.agreement_pool[validator]["data"] = loaded_block.tx_list
            return True, ""
    # If no space, return
    return False, "Out of space"



  ################################################################################
 ######################## TIME ##################################################
################################################################################


@app.route("/time", methods=['GET'])
def time_response():
    print("Called time")
    return {
        "time": str(time.time())
    }


  ################################################################################
 ######################## MAIN ROUTINE ##########################################
################################################################################
    
# While the rpc is waiting, a continuos process is available to perform tasks
def heartbeat():
    global forge_period
    print("OK: Heartbeat service started successfully")
    forge_period = False
    while True:
        time.sleep(0.5)
        # Every n seconds, a block is forged
        if time.time() - node.checkpoint_time >= node.block_time:
            forge_period = True
        # TODO is hardcoded to false while consensus is still in development
        # Detecting time passed from timestamp and syncing, it is easy to detect when is time to vote
        if forge_period:
            voting_routine()
            forge_period = False
            node.checkpoint_time = time.time()



  ################################################################################
 ######################## ENTRY POINT ###########################################
################################################################################ 
        
# Booting the node
if __name__ == "__main__":
    version = 0.1
    print("\n=====\nDoch - The Domus Chain official implementation v. " + str(version) + "\n")
    host = '0.0.0.0'
    port = 7200
    print("\n--------------------------------------------\n")
    # A joined subprocess ensure non blocking tasks
    beat = multiprocessing.Process(target=heartbeat)
    beat.start()
    http_server = WSGIServer((host, port), app)
    serve = multiprocessing.Process(target=http_server.serve_forever)
    serve.start()
    print("\nListening on " + str(host) + ":" + str(port))
    connection.wait([beat.sentinel, serve.sentinel])
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
import base64
import socket
import requests
from sys import argv
            

node = entity.ENTITY()#existing_private="account/keystore/accountPrivateKey")
vote = votes.VOTE()

forge_period = False

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024


  ################################################################################
 ######################## AUTODISCOVER ##########################################
################################################################################

def autodiscover():
    print("[0] Autodiscover started")
    local_ip = (([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0]
    if not "127." in local_ip and "192." in local_ip or "10." in local_ip:
        print("Local ip retrieved: " + str(local_ip))
    else:
        local_ip = ""
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if "192." in ip or "10." in ip:
                local_ip = ip
        if local_ip == "":  
            print("Autodiscover not possible")
        else:
            print("Local ip retrieved: " + str(local_ip))
        # Taking the subnet
        subnet = local_ip.split(".")[0] + "." +  local_ip.split(".")[1] + "." + local_ip.split(".")[2] + "."
        discovered = []
        for i in range(1,255):
            sub_ip = subnet + "." + str(i)
            try:
                res = requests.get(sub_ip + "/autodiscover", timeout=5)
                if "Node Available" in res.text:
                    discovered.append([sub_ip, 80])
                    print("[*] Peer found at " + str(sub_ip) + "/autodiscover")
            except:
                pass
        # Collect the results
        if len(discovered) == 0:
            print("[!] Autodiscover finished: 0 found")
        else:
            print("[*] Autodiscover finished: found " + str(len(discovered)) + " peers")
            node.peers.extend(discovered)
    print("[0] Autodiscover ended")

  ################################################################################
 ######################## API ENDPOINTS #########################################
################################################################################

# Reply to autodiscover
@app.route("/autodiscover", methods=['GET'])
def reply_to():
    return {
        "Message": "Node Available"
    }

# Inquiry data
@app.route("/get_from_chain", methods=['GET'])
def reply_to(item="", address="", limit=100):
    if not item == "" and not address == "":
        # Getting blocks
        if "block" in item:
            # Retrieve block number n
            block_number_target = item.split("block")[1]
            retrieved = node.chain.status.db.search((node.chain.status.extract.block_number == block_number_target))
            if len(retrieved) == 0:
                return {
                    "Message": "No block retrieved for " + str(block_number_target)
                }
            else:
                return {
                    "Message": "Block " + str(block_number_target) + ":\n" + str(retrieved)
                }
        pass 
    # Invalid request   
    else:
        return {
            "Message": "Unknown item or address"
        }

# Simply retrieve balancese
@app.route("/balanceof",  methods=['GET'])
def get_balance(address):
    entry = node.chain.status.db.search((node.chain.status.extract.type == 'account') & (node.chain.status.extract.address == address))
    if len(entry) == 0:
        node.chain.status.db.insert({"type": "account", "address": address, "balance": 0})
        balance = 0
    elif len(entry) == 1:
        balance = entry[0].get("balance")
    else:
        return {
            "Status": False,
            "Message": "no sense"
        }
    return {
        "Status": True,
        "Message": str(balance)
    }
    
@app.route('/chainstore', methods=['POST'])
def upload_file():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # The transaction is validated
        if is_a_tx(json, "file"):
            # A transaction object is forged
            tx = transactions.TRANSACTION()
            tx.data = json
            # Signature is verified
            valid = node.validate_signature(tx.data.get("from"), tx)
            if valid:
                # Checking if file is valid
                file_b64 = json.get("data").get("instructions").get("b64")
                file_name  = json.get("data").get("instructions").get("file_name")
                file_content=base64.b64decode(file_b64)
                node.mempool_tx(json)
                print("Accepted file tx " + json.get("signature"))
                return "Ok!", 200
            else:
                print("Bad signature (403)")
                return "Bad signature", 403
        else:
            print("Not a file TX (400)")
            return "Not a valid file tx!", 400
    else:
        print("Content unsupported (400)")
        return 'Content-Type not supported!', 400


  ################################################################################
 ######################## SMART CONTRACTS #######################################
################################################################################


  ################################################################################
 ######################## TRANSACTIONS ##########################################
################################################################################

def is_a_tx(json, type=""):
    try:
        if "data" in json.keys() and "signature" in json.keys:
            if "from" in json.get("data") and \
               "to" in json.get("data") and \
               "value" in json.get("data") and \
               "instructions" in json.get("data"):
                   if type=="file":
                       if "b64" in json.get("data").get("instructions") and \
                          "file_name" in json.get("data").get("instructions"):
                           return True
                       else:
                           return False
                   else:
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
    if len(node.peers) < 12:
        return
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
            # Execute the transactions
            indexof = 0
            for tx in valid_block.tx_list:
                success, result = node.execute_tx(tx)
                if not success:
                    result = "Execution reverted: " + result
                validated_tx = tx
                validated_tx.executed = success
                validated_tx.receipt = result
                # Include in the block the result of the various tx  
                valid_block.tx_list[indexof] = validated_tx
                indexof += 1
            # Create a block from the result
            proposed_block = node.create_block()
            node.broadcast_block(proposed_block)
            result, valid_block, penalities = wait_for_validation()
        else:
            # Cycle until the validators did their job
            result, valid_block, penalities = wait_for_validation()
            
        # Accept block
        if result:
            node.chain.status.mine(valid_block)
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
    print("[1] Heartbeat service started successfully")
    forge_period = False
    warning = True
    while True:
        try:
            time.sleep(0.5)
            # Every n seconds, a block is forged
            if time.time() - node.checkpoint_time >= node.block_time:
                if len(node.peers) < 11 and warning:
                    warning = False
                    print("[!] Not enough peers! We have " + str(len(node.peers)) + " but we need at least 11")
                    continue
                else:
                    warning = True
                    forge_period = True
            # Detecting time passed from timestamp and syncing, it is easy to detect when is time to vote
            if forge_period:
                voting_routine()
                forge_period = False
                node.checkpoint_time = time.time()
        except:
            break
    print("[1] Heartbeat Died")


  ################################################################################
 ######################## ARGUMENTS #############################################
################################################################################ 

def help():
    return "Welcome to Domus chain official client.\n" \
           "In this BETA version, expect bugs and report them\n" \
           "at administrator@blockdrops.com.\n" \
           "\nAccepted arguments are:\n" \
           "--help : shows this help\n" \
           "--nodiscover : don't try to autodiscover\n" \
           "--hidden : disable autodisoverable self\n" \
           "--nofile : don't accept files in a tx\n" \
           "--flush : delete the whole chain (resync)\n"  

def parse_args(argv):
    for args in argv:
        if args == argv[0]:
            continue
        # Options
        if args.startswith("--"):
            args = args.replace("--", "")
        # Values
        if args == "help":
            print(help())
        elif args == "nodiscover":
            pass
        elif args == "hidden":
            pass
        elif args == "nofile":
            pass
        elif args == "flush":
            pass
    exit()   


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
    # Parse args
    if len(argv) > 1:
        parse_args(argv)
    # A joined subprocess ensure non blocking tasks
    discover = multiprocessing.Process(target=autodiscover)
    discover.start()
    beat = multiprocessing.Process(target=heartbeat)
    beat.start()
    print("[2] WSGI Server started")
    http_server = WSGIServer((host, port), app)
    serve = multiprocessing.Process(target=http_server.serve_forever)
    serve.start()
    print("\nListening on " + str(host) + ":" + str(port))
    connection.wait([beat.sentinel, serve.sentinel, discover.sentinel])
    print("[2] WSGI Server died")

import random
                   
class CONSENSUS:    
    
    def __init__(self) -> None:
        self.voting_block = 0
        # Structure: { node: candidate }
        self.votes = {}
        self.winners = []
        self.has_voted = []
        self.agreement_pool = AGREEMENT_POOL()
    
    # Voting examination
    def count_winners(self):
        results = {}
        for vote in self.votes:
            if not vote in results:
                results[vote] = 1
            else:
                results[vote] += 1
        # Sorting the votes to get the best six
        sorted_values = sorted(results.values()) # Sort the values
        sorted_vote = {}
        validators = []
        
        selector = 12
        for amount in sorted_values: # Match values and voted
            selector -= 1 # Save power by just iterating the first six
            if selector < 0:
                break
            for voted in results.keys():
                if results[voted] == amount:
                    sorted_vote[voted] = results[voted]
                    validators.append(voted)
                    break
        # Shuffle validators, extract 6 valid and 6 fake 
        random.shuffle(sorted_vote)
        validators = sorted_vote[0:6]
        controllers = sorted_vote[6:12]
        self.consider_vote_closed()
        # List with 6 validators
        return validators, controllers
        
    def consider_vote_closed(self):
        self.voting_block += 1
        self.votes = {}

# Subclass for proposal pool
class AGREEMENT_POOL:
    def __init__(self) -> None:
        # Filled progressively with validator$n  
        self.cursor = 0          
        self.proposed = {
            "validator1": {
                "from": "",
                "data": ""
            },
            "validator2": {
                "from": "",
                "data": ""
            },
            "validator3": {
                "from": "",
                "data": ""
            },
            "validator4": {
                "from": "",
                "data": ""
            },
            "validator5": {
                "from": "",
                "data": ""
            },
            "validator6": {
                "from": "",
                "data": ""
            }
        }
    
    # Take the most identical blocks. Need at least 4/6
    def coherency(self):
        blocks_proposed = {}
        appearance = []
        penalized = []
        # Iterate and memorize each appearance of a block
        for content in self.proposed:
            validator = self.proposed.get(content)
            proposed = validator.get("data")
            if not proposed in appearance:
                appearance.append(proposed)
            list_index = appearance.index(proposed)
            # Create or add to the index in the list
            if str(list_index) in blocks_proposed:
                blocks_proposed[str(list_index)] += 1
            else:
                blocks_proposed[str(list_index)] = 1          
        # We now have a list of proposed blocks with the relative frequency
        # If we have full coherency, block is chosen
        if len(blocks_proposed) == 1:
            return True, appearance[0], penalized
        else:
            # If coherency is 4/6 and up, block is chosen and unreliable validators are penalized
            if blocks_proposed.get("0") >= 4:
                penalized = self.check_incoherent_validators(appearance[0])
                return True, appearance[0], penalized
            else:
                # If no consensus is produced, the jury is disbanded
                return False, "Consensus not reached", penalized
            
def check_incoherent_validator(self, chosen):
    spotted = []
    # Iterating comparing chosen block and block from validator
    for validator in self.proposed:
        if not self.proposed.get(validator).get("data") == chosen:
            # Compile a list with invalid validators
            spotted.append(self.proposed.get("validator").get("from"))    
 
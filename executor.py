from ast import operator
import blockchain
class EXECUTE:
    def __init__(self, tyo, arg) -> None:
        self.type_of = tyo
        self.arguments = arg
        self.chain = blockchain.BLOCKCHAIN()
        
    def run(self):
        # On any tx: arguments[0] = from, arguments[1] = to, arguments[3] = value 
        # Transfer is made by constructing the two operations, executing both and reverting on any error
        if self.type_of == "transfer":
            if self.arguments[2] == "add":
                operator == "sub"
            elif self.arguments[2] == "sub":
                operator = "add"
            else: 
                return False, "Unknown operation"
            try:
                success_origin, msg = self.chain.status.change_balance(self.arguments[0], operator, self.arguments[3])
                success_destination, msg = self.chain.status.change_balance(self.arguments[1], self.arguments[2], self.arguments[3])
                if not success_origin or not success_destination:
                    raise Exception
            except:
                if success_origin:
                    # Reverting the first iteration if happened
                    self.chain.status.change_balance(self.arguments[0], self.argument[2], self.arguments[3])
                    return False, "Reverted"
            # Tx has been executed and the state has been registered
            return True, "Success"
        else:
            return False, "Not yet supported"
        
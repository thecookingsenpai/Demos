
class demoscript:
    def __init__(self) -> None:
        pass
    def transact(data):
        pass
    def receipt(tx):
        pass
    
    # Subclasses
    class address:
        def __init__(self) -> None:
            self.value = ""
            self.balance = 0
            self.last_tx = 0
            self.tx_number = 0
    
    class DET:
        def __init__(self) -> None:
            self.name = ""
            self.ticker = ""
            self.totalSupply = 0
            self.circulatingSupply = 0
            self.creator = ""
            self.origin_tx = 0
            self.owner = ""
            
        def transfer(self, sender, recipient, amount):
            pass
        def received():
            pass
    
    class DENFT_Token:
        def __init__(self) -> None:
            self.origin = 0
            self.origin_tx = 0
            self.name = ""
            self.ticker = ""
            self.address = 0
            self.id = 0
            self.owner = ""
            
        def transfer(self, sender, recipient, amount):
            pass
        def received():
            pass
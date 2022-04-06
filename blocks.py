
class BLOCK:
    def __init__(self) -> None:
        self.block_number = 0
        self.tx_list = []
        self.signers = []
        self.signing_proofs = []
        self.timestamp = 0
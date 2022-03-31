class CONSENSUS:
    def __init__(self) -> None:
        self.voting_block = 0
        # Structure: { node: candidate }
        self.votes = {}
        self.winners = []
        self.has_voted = []
    
    def count_winners(self):
        pass
    
    def consider_vote_closed(self):
        self.voting_block += 1
        self.votes = {}
        self.winners = []
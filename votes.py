class VOTE:
    def __init__(self) -> None:
        self.timeout = 10.000
        self.timer = 0.000 
        
        
    def has_vote_finish(self, democracy, peers):
            totals = len(peers)
            quorum = round((totals * 66) / 100)
            if len(democracy.votes) >= quorum:
                return True, "Quorum"
                
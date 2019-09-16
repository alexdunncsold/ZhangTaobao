class AuctionInstance:
    def __init__(self, auction_post, constraints):
        self.auction_post = auction_post
        self.constraints = constraints

    def __lt__(self, other):
        return self.constraints.expiry < other.constraints.expiry
class BiddingAttempt:
    credentials = None
    auction_group = None
    target_auction = None
    max_bid_amount = None
    my_active_bid = None

    def __init__(self, credentials, auction_group, target_auction, max_bid_amount):
        self.credentials = credentials
        self.auction_group = auction_group
        self.target_auction = target_auction
        self.max_bid_amount = max_bid_amount
        self.my_active_bid = None

        assert credentials is not None
        assert auction_group is not None
        assert target_auction is not None
        assert max_bid_amount is not None

        assert max_bid_amount > self.target_auction.min_bid_amount

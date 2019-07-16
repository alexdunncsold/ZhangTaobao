class AuctionContext:
    credentials = None
    facebook_group = None
    auction = None
    max_bid_amount = None
    my_active_bid = None
    mode = None

    def __init__(self, credentials, facebook_group, auction, max_bid_amount, mode):
        self.credentials = credentials
        self.facebook_group = facebook_group
        self.auction = auction
        self.max_bid_amount = max_bid_amount
        self.my_active_bid = 0
        self.mode = mode

        assert credentials is not None
        assert facebook_group is not None
        assert auction is not None
        assert max_bid_amount is not None

        assert max_bid_amount > self.auction.min_bid_amount

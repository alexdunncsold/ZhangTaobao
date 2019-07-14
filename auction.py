class Auction:
    auction_id = ''
    end_datetime = None
    min_bid_step = None
    min_bid_amount = None

    def __init__(self, auction_id, end_datetime, min_bid_step, min_bid_amount):
        self.auction_id = auction_id
        self.end_datetime = end_datetime
        self.min_bid_step = min_bid_step
        self.min_bid_amount = min_bid_amount

        # todo perform sanity checks on all attributes

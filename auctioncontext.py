from datetime import datetime, timedelta
from pytz import utc


class AuctionContext:
    credentials = None
    facebook_group = None
    auction = None
    max_bid_amount = None
    my_facebook_id = None
    my_active_bid = None
    run_config = None

    def __init__(self, credentials, facebook_group, auction, max_bid_amount, run_config):
        self.credentials = credentials
        self.facebook_group = facebook_group
        self.auction = auction
        self.max_bid_amount = max_bid_amount
        self.my_facebook_id = ''
        self.my_active_bid = 0
        self.bids_placed = 0
        self.run_config = run_config

        assert self.credentials is not None
        assert self.facebook_group is not None
        assert self.auction is not None
        assert self.max_bid_amount is not None

        assert max_bid_amount > self.auction.min_bid_amount

    def critical_period_active(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        return now > self.auction.end_datetime - timedelta(seconds=5)

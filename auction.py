from datetime import datetime
from pytz import utc


class Auction:
    id = ''
    end_datetime = None
    min_bid_step = None
    min_bid_amount = None

    def __init__(self, id, end_datetime, min_bid_amount, min_bid_step):
        if not 15 <= len(id) <= 16:
            raise ValueError('Auction __init__(): supplied id {} invalid'.format(id))
        if end_datetime <= datetime.utcnow().replace(tzinfo=utc):
            raise ValueError('Auction __init__(): supplied end_datetime is in the past')
        if min_bid_amount < 1:
            raise ValueError('Auction __init__(): min_bid_amount must be a positive integer')
        if min_bid_step < 1:
            raise ValueError('Auction __init__(): min_bid_step must be a positive integer')

        self.id = id
        self.end_datetime = end_datetime
        self.min_bid_step = min_bid_step
        self.min_bid_amount = min_bid_amount



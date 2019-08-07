from datetime import datetime, timedelta
from pytz import utc
from config import SANE_UPPER_BOUND, SANE_LOWER_BOUND


class Auction:
    id = ''
    end_datetime = None
    expired = False
    total_extensions = 0
    min_bid_step = None
    min_bid_amount = None

    def __init__(self, id, end_datetime, min_bid_amount, min_bid_step, extensions=0):
        if not 15 <= len(id) <= 16:
            raise ValueError('Auction __init__(): supplied id {} invalid'.format(id))
        if end_datetime <= datetime.utcnow().replace(tzinfo=utc):
            raise ValueError('Auction __init__(): supplied end_datetime is in the past')
        if not 0 <= extensions <= 2:
            raise ValueError('Auction __init__(): Valid range for extension quantity is [0,2]')
        if not SANE_LOWER_BOUND <= min_bid_amount <= SANE_UPPER_BOUND:
            print('Min bid beyond sane parsing bounds.  Setting min_bid_amount = {}'.format(SANE_LOWER_BOUND))
            min_bid_amount = SANE_LOWER_BOUND
        if min_bid_step < 1:
            raise ValueError('Auction __init__(): min_bid_step must be a positive integer')

        self.id = id
        self.end_datetime = end_datetime
        self.total_extensions = extensions
        self.min_bid_step = min_bid_step
        self.min_bid_amount = min_bid_amount

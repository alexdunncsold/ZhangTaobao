class Bid:
    bidder = None
    value = 0
    timestamp = None

    def __init__(self, bidder=None, value=0, timestamp=None):
        self.bidder = bidder
        self.value = value
        self.timestamp = timestamp

        if (value is None or value is 0) and bidder is not None:
            raise RuntimeError("Bid::__init__(): A bid must specify both bidder and value, or neither.")

    def __gt__(self, other):
        return self.value > other.value

class Bid:
    bidder = None
    value = 0

    def __init__(self, bidder=None, value=0):
        self.bidder = bidder
        self.value = value

        if (value is None or value is 0) and bidder is not None:
            raise RuntimeError("Bid::__init__(): A bid must specify both bidder and value, or neither.")
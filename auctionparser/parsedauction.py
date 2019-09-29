import auctionparser.auctionparser as parse


class ParsedAuction:
    def __init__(self, full_post_text):
        self.full_text = full_post_text
        self.seller = parse.parse_seller(full_post_text)
        self.producer = parse.parse_producer(full_post_text)
        self.production = parse.parse_production(full_post_text)
        self.production_year = parse.parse_production_year(full_post_text)
        self.weight = parse.parse_weight(full_post_text)
        self.tea_type = parse.parse_tea_type(full_post_text)
        self.storage_type = parse.parse_storage_type(full_post_text)
        self.expiry = parse.parse_expiry(full_post_text)
        self.bid_step = parse.parse_bid_step(full_post_text)
        self.starting_bid = parse.parse_starting_bid(full_post_text)

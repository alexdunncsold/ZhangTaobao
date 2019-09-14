import configparser


class AuctionPost:
    name = None

    def __init__(self, id, group_id):
        self.id = id
        self.group_id = group_id

from configparser import ConfigParser

from auctionpost import AuctionPost
from facebookhandler import FacebookHandler as Fb
from webdriver import get_webdriver


class AuctionSearcher:
    def __init__(self, webdriver=None):
        if webdriver:
            self.webdriver = webdriver
        else:
            self.webdriver = get_webdriver('alex.dunn.773', True)

        search_config = ConfigParser()
        search_config.read('search_parameters.ini')

        group_config = ConfigParser()
        group_config.read('../group_config.ini')
        group_ids = [group_config[group]['id'] for group in group_config.sections()]

        seen_auctions = ConfigParser()
        seen_auctions.read('seen_auctions.ini')
        self.seen_auctions = [AuctionPost(auction_id, group_id) for group_id in group_ids for auction_id in
                              seen_auctions[group_id].split(' ')]

        self.relevant_producers = search_config['search_for']['producers'].split(' ')
        self.relevant_productions = search_config['search_for']['productions'].split(' ')
        self.limit_year_low = search_config['limit_to']['production_year_min']
        self.limit_year_high = search_config['limit_to']['production_year_max']

        self.matching_auctions = self.get_matching_auctions()
        self.new_matching_auctions = self.get_new_matching_auctions()

    def get_auctions(self):
        return []  # todo implement

    def get_matching_auctions(self):
        matching_auctions = [auction for auction in self.get_auctions()
                             if self.producer_match(auction)
                             or self.production_match(auction)]
        return matching_auctions

    def producer_match(self, auction):
        if auction.producer:
            for producer in self.relevant_producers:
                if producer in auction.producer:
                    return True
        else:
            for producer in self.relevant_producers:
                if producer in auction.full_text:
                    return True
        return False

    def production_match(self, auction):
        if auction.production:
            for production in self.relevant_productions:
                if production in auction.production:
                    return True
        else:
            for production in self.relevant_productions:
                if production in auction.full_text:
                    return True
        return False

    def get_new_matching_auctions(self):
        new_matching_auctions = [auction for auction in self.get_matching_auctions()
                                 if auction.id not in self.seen_auctions[auction.group_id]]
        return new_matching_auctions

    def print_matching_auctions(self):
        self.print_auctions(self.get_matching_auctions())

    def print_new_matching_auctions(self):
        self.print_auctions(self.get_new_matching_auctions())

    def print_auctions(self, auctions):
        for auction in auctions:
            print(f'https://www.facebook.com/groups/{auction.group_id}/permalink/{auction.id}/')

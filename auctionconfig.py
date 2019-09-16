from configparser import ConfigParser
from datetime import datetime
from pytz import utc

from auctioninstance import AuctionInstance
from auctionpost import AuctionPost
from constraintset import ConstraintSet


def get_unexpired_auctions(**kwargs):
    group_ids_config = ConfigParser()
    group_ids_config.read('group_config.ini')

    try:
        dev_mode = kwargs['dev']
    except KeyError:
        dev_mode = False

    planned_auctions = []
    auctions_config = load_config(dev=dev_mode)

    for auction_section_header in auctions_config.sections():
        auction_section = auctions_config[auction_section_header]
        group_nickname = auction_section['GroupNickname']
        group_id = group_ids_config[group_nickname]['id']

        if (dev_mode and group_nickname != 'dev') or (not dev_mode and group_nickname == 'dev'):
            raise RuntimeError('Mismatch between dev/non-dev mode and auction config.')

        auction_post = AuctionPost(auction_section['AuctionId'], group_id)
        constraints = ConstraintSet(auction_section)

        if constraints.expiry > datetime.utcnow().replace(tzinfo=utc):
            planned_auctions.append(AuctionInstance(auction_post, constraints))

    return planned_auctions


def load_config(**kwargs):
    try:
        dev_mode = kwargs['dev']
    except KeyError:
        dev_mode = False

    planned_auctions_config = ConfigParser()
    planned_auctions_config.read('test_config.ini' if dev_mode else 'live_config.ini')

    return planned_auctions_config








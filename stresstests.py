from selenium.common.exceptions import StaleElementReferenceException
from pytz import timezone, utc

from auction import Auction
from auctioncontext import AuctionContext
from facebookinteractions import *
from facebookcredentials import FacebookCredentials
from facebookgroup import FacebookGroup
from webdriverhelper import get_webdriver

from timesync import get_short_expiry, get_offset, get_post_registered

from secrets import *

loc_tz = timezone('America/Los_Angeles')

#########################################################################################
run_config = 'dev'
extension_count = 0
PLACE_INITIAL_BID = False
minimum_bids_to_save_face = 0
POST_ID = '1319918928185105'
AUCTION_END = get_short_expiry()
STARTING_BID = 1
BID_STEP = 1
YOUR_MAX_BID = 5000

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup(GROUP_NAMES[run_config], GROUP_IDS[run_config])
auction = Auction(POST_ID, AUCTION_END, STARTING_BID, BID_STEP, extension_count)
auction_context = AuctionContext(credentials, auction_group, auction,
                                 YOUR_MAX_BID, minimum_bids_to_save_face, run_config)
driver = get_webdriver()

try:

    login_to_facebook(driver, auction_context)
    posting_delay = get_offset(driver, auction_context)
    load_auction_page(driver, auction_context)

    bid_tests = 15
    tests_complete = 0
    failures = 0

    now = datetime.utcnow().replace(tzinfo=utc) + posting_delay
    while now < auction_context.auction.end_datetime:
        if now > auction_context.auction.end_datetime - timedelta(milliseconds=100):
            print(f'Bidding at adjusted system time {now.strftime("%H:%M (%S.%fsec)")}')
            make_bid(driver, auction_context, 500)

            driver.get(driver.current_url)
            post_registered = get_post_registered(driver)
            if auction_context.auction.end_datetime.second - post_registered.second > post_registered.second:
                spare_seconds = auction_context.auction.end_datetime - post_registered
            else:
                spare_seconds = 60 + auction_context.auction.end_datetime.second - post_registered.second

            if post_registered < auction_context.auction.end_datetime:
                print(f'    Passed with {spare_seconds} seconds to spare (1sec optimal)')
            else:
                failures += 1
                print(f'    Failed to bid before auction expiry T_T')

            tests_complete += 1
            auction_context.auction.end_datetime = auction_context.auction.end_datetime + timedelta(minutes=1)

            if tests_complete >= bid_tests:
                print(f'Ran {tests_complete} tests - {failures} failed.')
                break
        now = datetime.utcnow().replace(tzinfo=utc) + posting_delay
finally:
    driver.quit()

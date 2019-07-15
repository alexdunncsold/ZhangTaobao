from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime, timedelta
from pytz import timezone, utc
from time import sleep
from sys import platform

from auction import Auction
from auctioncontext import AuctionContext
from facebookinteractions import *
from facebookcredentials import FacebookCredentials
from facebookgroup import FacebookGroup
from secrets import *

#########################################################################################
run_config = 'dev'
POST_ID = 1309908152519516
AUCTION_END = timezone(TIMEZONES[run_config]).localize(datetime(2019, 7, 14, 22, 59, 59))
AUCTION_END = datetime.utcnow().replace(tzinfo=utc) + timedelta(seconds=20) if run_config == 'dev' else AUCTION_END
STARTING_BID = 500
BID_STEP = 100
YOUR_MAX_BID = 8888
#########################################################################################

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup(GROUP_NAMES[run_config], GROUP_IDS[run_config])
auction = Auction(POST_ID, AUCTION_END, STARTING_BID, BID_STEP)
auction_context = AuctionContext(credentials, auction_group, auction, YOUR_MAX_BID)

options = Options()
if platform == 'win32':
    options.add_argument('--disable-notifications')
elif platform == 'linux':
    options = Options()
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument('--remote-debugging-port=9222')
else:
    raise RuntimeError('Error while setting webdriver options: platform {} not supported.'.format(platform))
print('Platform identified as {}.  Instantiating driver...'.format(platform))
driver = webdriver.Chrome(options=options)
print('Driver instantiated. Initiating login...')

try:
    # Perform Login
    login_to_facebook(driver, credentials)

    # Load auction page
    load_auction_page(driver, auction_context)

    now = datetime.utcnow().replace(tzinfo=utc)
    while now < AUCTION_END + timedelta(seconds=15):
        now = datetime.utcnow().replace(tzinfo=utc)
        if now > AUCTION_END - timedelta(seconds=5):
            try:
                valid_bid_history = parse_bid_history(driver, auction_context)

                lowest_valid_bid = max(auction.min_bid_amount, valid_bid_history[-1] + auction.min_bid_step)

                if auction_context.my_active_bid == valid_bid_history[-1]:
                    charlie_sheen = '#Winning'
                elif lowest_valid_bid <= auction_context.max_bid_amount:
                    print('Bid condition triggered.')
                    make_bid(driver, lowest_valid_bid)
                    sleep(0.5)
                    auction_context.my_active_bid = lowest_valid_bid
                else:
                    print('Currently outbid and minimum valid bid {} exceeds upper limit {} - quitting...'.format(
                        lowest_valid_bid, auction_context.max_bid_amount))
                    break

            except StaleElementReferenceException as err:
                # This will occur when a comment posts during iteration through the comments
                # It can be safely ignored, as the bid will process during the next iteration
                print("DOM updated while attempting to bid - bid skipped, iteration continues")

except Exception as err:
    print(repr(err))
finally:
    print('Quitting webdriver...')
    driver.quit()
    print('Complete.')

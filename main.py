from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime, timedelta
from pytz import timezone, utc
from time import sleep

from auction import Auction
from biddingattempt import BiddingAttempt
from commenttextparser import *
from facebookinteractions import *
from facebookcredentials import FacebookCredentials
from facebookgroup import FacebookGroup
from secrets import *

#########################################################################################
run_config = 'dev'
POST_ID = 1309908152519516
AUCTION_END = timezone(TIMEZONES[run_config]).localize(datetime(2019, 7, 14, 22, 59, 59))
STARTING_BID = 500
BID_STEP = 100
YOUR_MAX_BID = 8888
#########################################################################################

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup(GROUP_NAMES[run_config], GROUP_IDS[run_config])
auction = Auction(POST_ID, AUCTION_END, STARTING_BID, BID_STEP)
bidding_attempt = BiddingAttempt(credentials, auction_group, auction, YOUR_MAX_BID)

options = Options()
options.add_argument('--disable-notifications')
driver = webdriver.Chrome(options=options)

# Perform Login
login_to_facebook(driver, MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)

# Monitor auction status
POST_PERMALINK = 'https://www.facebook.com/groups/{}/permalink/{}/'.format(GROUP_IDS[run_config], POST_ID)
driver.get(POST_PERMALINK)

now = datetime.utcnow().replace(tzinfo=utc)
while now < AUCTION_END + timedelta(seconds=15):
    now = datetime.utcnow().replace(tzinfo=utc)
    if now > AUCTION_END - timedelta(seconds=5):
        try:
            remove_all_child_comments(driver)

            valid_bid_history = [0, ]
            comment_elem_list = driver.find_elements_by_class_name('_3l3x')
            for comment in comment_elem_list:
                try:
                    comment_bid_amount = parse_bid(comment.text)
                    if comment_bid_amount >= valid_bid_history[-1] + auction.min_bid_step:
                        valid_bid_history.append(comment_bid_amount)
                except ValueError as err:
                    pass

            lowest_valid_bid = max(auction.min_bid_amount, valid_bid_history[-1]+auction.min_bid_step)

            if bidding_attempt.my_active_bid == valid_bid_history[-1]:
                charlie_sheen = '#Winning'
            elif lowest_valid_bid <= bidding_attempt.max_bid_amount:
                make_bid(driver, lowest_valid_bid)
                sleep(0.5)
                bidding_attempt.my_active_bid = lowest_valid_bid
            else:
                break
        except StaleElementReferenceException as err:
            # This will occur when a comment posts during iteration through the comments
            # It can be safely ignored, as the bid will process during the next iteration
            print("DOM updated while attempting to bid - bid skipped, iteration continues")

driver.quit()

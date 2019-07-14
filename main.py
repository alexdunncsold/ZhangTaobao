from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime, timezone, timedelta

from auction import Auction
from biddingattempt import BiddingAttempt
from commenttextparser import *
from facebookinteractions import *
from facebookcredentials import FacebookCredentials
from facebookgroup import FacebookGroup
from secrets import *

GROUP_ID = GROUP_IDS['dev']
POST_ID = 1309908152519516
POST_PERMALINK = 'https://www.facebook.com/groups/{}/permalink/{}/'.format(GROUP_ID, POST_ID)

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup("Battlefield Pu'er", GROUP_ID)
auction = Auction(POST_ID, datetime, 100, 500)
bidding_attempt = BiddingAttempt(credentials, auction_group, auction, 8888)

options = Options()
options.add_argument('--disable-notifications')
driver = webdriver.Chrome(options=options)

# Perform Login
driver.get("https://www.facebook.com/")
assert 'Facebook - Log In or Sign Up' in driver.title

email_elem = driver.find_element_by_id('email')
email_elem.clear()
email_elem.send_keys(MY_FB_EMAIL_ADDRESS)

password_elem = driver.find_element_by_id('pass')
password_elem.clear()
password_elem.send_keys(MY_FB_PASSWORD)

password_elem.send_keys(Keys.RETURN)

# Monitor auction status
driver.get(POST_PERMALINK)
while True:
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
            bidding_attempt.my_active_bid = lowest_valid_bid
        else:
            # make_bid(driver, "I'm out, guys!")  # debug message for end
            break
    except StaleElementReferenceException as err:
        # This will occur when a comment posts during iteration through the comments
        # It can be safely ignored, as the bid will process during the next iteration
        print("DOM updated while attempting to bid - bid skipped, iteration continues")

driver.quit()

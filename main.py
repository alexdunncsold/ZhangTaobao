from selenium.common.exceptions import StaleElementReferenceException
from pytz import timezone, utc

from auction import Auction
from auctioncontext import AuctionContext
from facebookinteractions import *
from facebookcredentials import FacebookCredentials
from facebookgroup import FacebookGroup
from webdriverhelper import get_webdriver

from secrets import *

loc_tz = timezone('America/Los_Angeles')

#########################################################################################
run_config = 'battlefield'  # dev, battlefield, storm
extension_count = 0
PLACE_INITIAL_BID = False
minimum_bids_to_save_face = 0
POST_ID = '603869066686545'
AUCTION_END = timezone(TIMEZONES[run_config]).localize(datetime(2019, 7, 29, 21, 19, 59))
STARTING_BID = 100
BID_STEP = 100
YOUR_MAX_BID = 3800

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup(GROUP_NAMES[run_config], GROUP_IDS[run_config])
auction = Auction(POST_ID, AUCTION_END, STARTING_BID, BID_STEP, extension_count)
auction_context = AuctionContext(credentials, auction_group, auction,
                                 YOUR_MAX_BID, minimum_bids_to_save_face, run_config)
driver = get_webdriver()

try:
    # Perform Login
    login_to_facebook(driver, auction_context)

    # Load auction page
    load_auction_page(driver, auction_context)

    now = datetime.utcnow().replace(tzinfo=utc)
    competing_bid_logged = None  # todo move to Auction_Context
    next_bid_scheduled = None  # todo move to Auction_Context

    try:
        item_name = driver.find_element_by_class_name('_l53').text
    except NoSuchElementException:
        item_name = 'NoNameFound'

    print(
        f"Bidding as {auction_context.my_facebook_id} on {item_name} to a maximum of {auction_context.max_bid_amount} in steps of {auction_context.auction.min_bid_step}")  # todo move all these prints to a Auction_Context helper function
    print('Auction ends {}'.format(auction_context.auction.end_datetime.astimezone(
        loc_tz)))  # todo move all these prints to a Auction_Context helper function

    auction_context.refresh_bid_history(driver)  # todo move all these prints to a Auction_Context init function
    auction_context.print_bid_history()  # todo move all these prints to a Auction_Context helper function

    while now < auction_context.auction.end_datetime + timedelta(seconds=3):

        now = datetime.utcnow().replace(tzinfo=utc)

        try:
            auction_context.refresh_bid_history(driver)
            lowest_valid_bid = max(auction.min_bid_amount,
                                   auction_context.get_current_winning_bid().value + auction.min_bid_step)  # todo add to AuctionContext

            # if currently winning
            if auction_context.get_current_winning_bid().bidder == auction_context.my_facebook_id \
                    and (
                    run_config != 'dev' or auction_context.get_current_winning_bid() == auction_context.my_active_bid):
                charlie_sheen = '#Winning'

            # if we're priced out of further bids, quit
            elif lowest_valid_bid > auction_context.max_bid_amount:
                print('Minimum valid bid {} exceeds upper limit {} - quitting...'.format(
                    lowest_valid_bid, auction_context.max_bid_amount))
                break

            # if auction_context corrupted
            elif auction_context.my_active_bid > auction_context.get_current_winning_bid().value:
                raise RuntimeError('main(): Active bid not reflected in bid history, auction state corrupted.')

            # if initial bid needs to be placed
            elif PLACE_INITIAL_BID \
                    and auction_context.bids_placed == 0 \
                    and lowest_valid_bid <= auction_context.max_bid_amount:

                print('Placing initial bid.')
                make_bid(driver, auction_context, lowest_valid_bid)

            # if it's time to snipe
            elif auction_context.critical_period_active() \
                    and auction_context.get_current_winning_bid().bidder != auction_context.my_facebook_id \
                    and lowest_valid_bid <= auction_context.max_bid_amount:  # todo make winning check a helper function of AuctionContext

                print('Bid condition detected during critical period.')
                make_bid(driver, auction_context, lowest_valid_bid)

            # if currently outbid, and more courtesy bids required, schedule a courtesy bid
            elif auction_context.get_current_winning_bid().bidder != auction_context.my_facebook_id \
                    and auction_context.bids_placed < auction_context.minimum_bids_to_save_face \
                    and lowest_valid_bid <= auction_context.max_bid_amount \
                    and competing_bid_logged is None:

                competing_bid_logged = datetime.utcnow().replace(tzinfo=utc)
                print("Competing bid logged at {}".format(competing_bid_logged.astimezone(loc_tz)))

                next_bid_scheduled = (competing_bid_logged + (1 / 10 if auction_context.run_config == 'dev' else 1) * (
                            auction_context.auction.end_datetime - competing_bid_logged) / 2).astimezone(loc_tz)
                print('Next outbid scheduled for {}'.format(next_bid_scheduled))

            # if it's time to make a scheduled courtesy bid, make a bid
            elif next_bid_scheduled \
                    and now > next_bid_scheduled \
                    and lowest_valid_bid <= auction_context.max_bid_amount:

                print('Courtesy bid triggered.')
                make_bid(driver, auction_context, lowest_valid_bid)

                competing_bid_logged = None
                next_bid_scheduled = None

        except StaleElementReferenceException as err:
            # This will occur when a comment posts during iteration through the comments
            # It can be safely ignored, as the bid will process during the next iteration
            # print("DOM updated while attempting to bid - bid skipped, iteration continues")
            pass

finally:
    print('Final Auction State:')
    auction_context.print_bid_history()
    print('Quitting webdriver...')
    driver.quit()
    print('Complete.')

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
run_config = 'dev'  # dev, precipice_test, battlefield, storm
extension_count = 0
PLACE_INITIAL_BID = True
minimum_bids_to_save_face = 10 if run_config == 'dev' else 3
POST_ID = '1312495965594068'
AUCTION_END = timezone(TIMEZONES[run_config]).localize(datetime(2019, 7, 18, 21, 30, 00))
AUCTION_END = datetime.utcnow().replace(tzinfo=utc) + timedelta(
    minutes=3) if run_config == 'dev' else AUCTION_END
STARTING_BID = 1
BID_STEP = 50
YOUR_MAX_BID = 17000
#########################################################################################

credentials = FacebookCredentials(MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)
auction_group = FacebookGroup(GROUP_NAMES[run_config], GROUP_IDS[run_config])
auction = Auction(POST_ID, AUCTION_END, STARTING_BID, BID_STEP)
auction_context = AuctionContext(credentials, auction_group, auction, YOUR_MAX_BID, run_config)
driver = get_webdriver()

try:
    # Perform Login
    login_to_facebook(driver, auction_context)

    # Load auction page
    load_auction_page(driver, auction_context)

    now = datetime.utcnow().replace(tzinfo=utc)
    competing_bid_logged = None
    next_bid_scheduled = None
    print('Auction ends {}'.format(auction_context.auction.end_datetime.astimezone(loc_tz)))

    while now < auction_context.auction.end_datetime + timedelta(seconds=5):
        now = datetime.utcnow().replace(tzinfo=utc)
        try:
            valid_bid_history = parse_bid_history(driver, auction_context)

            lowest_valid_bid = max(auction.min_bid_amount, valid_bid_history[-1].value + auction.min_bid_step)

            # if currently winning
            if valid_bid_history[-1].bidder == auction_context.my_facebook_id \
                    and (run_config != 'dev' or valid_bid_history[-1] == auction_context.my_active_bid):
                charlie_sheen = '#Winning'

            # if auction_context corrupted
            elif auction_context.my_active_bid > valid_bid_history[-1].value:
                raise RuntimeError('main(): Active bid not reflected in bid history, auction state corrupted.')

            # if initial bid needs to be placed
            elif PLACE_INITIAL_BID \
                    and auction_context.bids_placed == 0 \
                    and lowest_valid_bid <= auction_context.max_bid_amount:

                print('Placing initial bid.')
                make_bid_without_submit(driver, auction_context,
                                        lowest_valid_bid) if run_config == 'precipice_test' else make_bid(
                    driver, auction_context, lowest_valid_bid)

            # if currently outbid, and more courtesy bids required
            elif valid_bid_history[-1].bidder != auction_context.my_facebook_id \
                    and auction_context.bids_placed < minimum_bids_to_save_face \
                    and lowest_valid_bid <= auction_context.max_bid_amount \
                    and competing_bid_logged is None:

                competing_bid_logged = datetime.utcnow().replace(tzinfo=utc)
                print("Competing bid {} logged at {}".format(valid_bid_history[-1].value,
                                                             competing_bid_logged.astimezone(loc_tz)))

                next_bid_scheduled = (competing_bid_logged + (
                            auction_context.auction.end_datetime - competing_bid_logged) / 2).astimezone(loc_tz)
                print('Next outbid scheduled for {}'.format(next_bid_scheduled))

            # if it's time to make a scheduled courtesy bid
            elif next_bid_scheduled \
                    and now > next_bid_scheduled \
                    and lowest_valid_bid <= auction_context.max_bid_amount:

                print('Courtesy bid triggered.')
                make_bid(driver, auction_context, lowest_valid_bid)

                competing_bid_logged = None
                next_bid_scheduled = None

            # if it's time to snipe
            elif auction_context.critical_period_active() \
                    and valid_bid_history[-1].bidder != auction_context.my_facebook_id \
                    and lowest_valid_bid <= auction_context.max_bid_amount:

                print('Bid condition detected during critical period.')

                # extend auction immediately to avoid inaccuracy
                if extension_count:
                    extension_count -= 1
                    print('Extending auction by 5min ({} extensions remaining)'.format(extension_count))
                    auction_context.auction.end_datetime += timedelta(minutes=1 if run_config == 'dev' else 5)
                    print('Auction end extended to {}'.format(auction_context.auction.end_datetime.astimezone(loc_tz)))

                make_bid(driver, auction_context, lowest_valid_bid)

            elif lowest_valid_bid > auction_context.max_bid_amount:
                print('Minimum valid bid {} exceeds upper limit {} - quitting...'.format(
                    lowest_valid_bid, auction_context.max_bid_amount))
                break

        except StaleElementReferenceException as err:
            # This will occur when a comment posts during iteration through the comments
            # It can be safely ignored, as the bid will process during the next iteration
            # print("DOM updated while attempting to bid - bid skipped, iteration continues")
            pass

finally:
    print('Quitting webdriver...')
    driver.quit()
    print('Complete.')

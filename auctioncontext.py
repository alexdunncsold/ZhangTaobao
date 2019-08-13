from bid import Bid
from commenttextparser import parse_bid
from datetime import datetime, timedelta
from facebookinteractions import remove_all_child_comments, take_screenshot
from math import ceil
from performance_testing import *
from pytz import utc
from selenium.common.exceptions import NoSuchElementException
from timesync import get_offset


class AuctionContext:
    my_facebook_id = ''
    my_active_bid = 0
    bids_placed = 0
    valid_bid_history = []
    my_valid_bid_count = 0
    latest_time_notification = None
    sync_time_at = timedelta(minutes=10)
    posting_delay = None

    def __init__(self, credentials, facebook_group, auction,
                 max_bid_amount, minimum_bids_to_save_face, run_config):
        self.credentials = credentials
        self.facebook_group = facebook_group
        self.auction = auction
        self.extensions_remaining = self.auction.total_extensions
        self.max_bid_amount = max_bid_amount
        self.minimum_bids_to_save_face = minimum_bids_to_save_face
        self.run_config = run_config

        assert self.credentials is not None
        assert self.facebook_group is not None
        assert self.auction is not None
        assert self.max_bid_amount is not None

        assert max_bid_amount >= self.auction.min_bid_amount

    def critical_period_active(self):
        return self.get_time_remaining() < timedelta(seconds=5)

    def get_time_remaining(self):
        time_remaining = self.auction.end_datetime - datetime.utcnow().replace(tzinfo=utc)
        if self.posting_delay:
            time_remaining -= self.posting_delay
        return time_remaining

    def trigger_extension(self):
        if self.extensions_remaining > 0 \
                and self.get_time_remaining() < timedelta(minutes=5):
            self.auction.end_datetime += timedelta(minutes=(5 if self.run_config != 'dev' else 1))
            self.extensions_remaining -= 1
            print('Bid placed in final 5min - auction time extended to {}'.format(self.auction.end_datetime))

    def get_current_winning_bid(self):
        if self.valid_bid_history:
            current_winning_bid = self.valid_bid_history[-1]
        else:
            current_winning_bid = Bid()
        return current_winning_bid

    def print_bid(self, bid):
        max_placed_bid_digits = len(str(self.valid_bid_history[-1].value))
        print(f'    {str(bid.value).rjust(max_placed_bid_digits)} ({bid.bidder})')

    def get_comment_author(self, comment):
        comment_author_elem = comment.find_element_by_class_name('_6qw4')
        comment_author = comment_author_elem.get_attribute('href').split('https://www.facebook.com/')[1]
        return comment_author

    def get_comment_text(self, comment):
        try:
            comment_text_elem = comment.find_element_by_class_name('_3l3x')
            comment_text = comment_text_elem.text
        except Exception as err:
            comment_text = ''
        return comment_text

    def refresh_bid_history(self, webdriver):
        remove_all_child_comments(webdriver)

        valid_bid_history = []
        my_valid_bid_count = 0

        comment_elem_list = webdriver.find_elements_by_class_name('_6qw3')

        # If response speed is more critical than maintaining an accurate record
        if self.critical_period_active():
            valid_bid_history = self.valid_bid_history
            valid_bid_found = False

            # Print console notifications
            if not self.auction.expired:
                time_remaining = self.get_time_remaining()
                if time_remaining.days == -1:
                    self.auction.expired = True
                    take_screenshot(webdriver)
                    print('Auction complete!')
                elif not self.latest_time_notification:
                    self.latest_time_notification = time_remaining
                    print(f'{time_remaining.seconds + 1} seconds remaining - critical period active!')
                elif time_remaining.seconds != self.latest_time_notification.seconds:
                    self.latest_time_notification = time_remaining
                    print(f'{time_remaining.seconds + 1} seconds remaining!')

            # Look for the most recent bid gte the known high bid and consider that to be the high bid
            for comment in reversed(comment_elem_list):
                comment_author = self.get_comment_author(comment)
                comment_text = self.get_comment_text(comment)

                # distinguish automated bids from manual bids in dev configuration
                if '(autobid)' in comment_text:
                    comment_author += '/dev'

                # Inspect comment for a valid bid
                try:
                    comment_bid_amount = parse_bid(comment_text)

                    if not valid_bid_history \
                            or comment_bid_amount >= valid_bid_history[-1].value + self.auction.min_bid_step:
                        new_bid = Bid(comment_author, comment_bid_amount)

                        if self.valid_bid_history and new_bid > self.valid_bid_history[-1]:
                            print(f'New bid detected (desperation mode)!')
                            self.print_bid(new_bid)

                        valid_bid_history.append(new_bid)
                        valid_bid_found = True

                    elif comment_bid_amount == valid_bid_history[-1].value:
                        valid_bid_found = True

                except ValueError as err:
                    pass

                if valid_bid_found:
                    # Break out of the loop and respond to the new bid immediately
                    break
        # Else if operating in non-critical mode
        else:
            for comment in comment_elem_list:
                try:
                    comment_author = self.get_comment_author(comment)
                    comment_text = self.get_comment_text(comment)

                    # distinguish automated bids from manual bids in dev configuration
                    if '(autobid)' in comment_text:
                        comment_author += '/dev'

                    comment_bid_amount = parse_bid(comment_text)

                    if not valid_bid_history \
                            or comment_bid_amount >= valid_bid_history[-1].value + self.auction.min_bid_step:
                        new_bid = Bid(comment_author, comment_bid_amount)
                        if new_bid.bidder == self.my_facebook_id:
                            my_valid_bid_count += 1

                        if self.valid_bid_history and new_bid > self.valid_bid_history[-1]:
                            print(f'New bid detected!')
                            self.print_bid(new_bid)

                        valid_bid_history.append(new_bid)
                except ValueError as err:
                    pass
                except NoSuchElementException as err:
                    pass

        self.valid_bid_history = valid_bid_history
        self.my_valid_bid_count = my_valid_bid_count

    def print_bid_history(self):
        print('Current Bid History:')
        for bid in self.valid_bid_history:
            self.print_bid(bid)
        if not self.auction.expired:
            print(
                f'{self.my_facebook_id} has made {self.my_valid_bid_count} valid bids so far ({self.minimum_bids_to_save_face} required)')

    def sync_time(self, webdriver):
        print('Syncing time with fb server...')
        self.posting_delay = get_offset(webdriver, self)

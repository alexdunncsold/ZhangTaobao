import configparser
from time import sleep
from pytz import utc
from datetime import datetime, timedelta
from auctionconfig import  get_unexpired_auctions
import os

from archiver import Archiver
from bid import Bid

import bidparse

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from auctionpost import AuctionPost
from constraintset import ConstraintSet
from countdowntimer import CountdownTimer
from facebookgroup import FbGroup
from facebookhandler import FacebookHandler
from facebookauctionclock import FacebookAuctionClock
from user import User
from webdriver import get_webdriver


class Supervisor:
    auctionpost = None
    constraints = None
    extensions_remaining = None
    fbclock = None
    countdown = None

    valid_bid_history = None
    my_valid_bid_count = 0

    initial_bid_made = False
    initial_snipe_performed = False
    most_recent_bid_submission = None

    def __init__(self, user_nickname='alex', **kwargs):
        config = configparser.ConfigParser()

        if 'dev' in kwargs and kwargs['dev']:  # todo clean up kwargs - there must be a better way
            self.dev_mode = True
            config.read('test_config.ini')
        else:
            self.dev_mode = False
            config.read('live_config.ini')

        if 'archive' in kwargs:
            self.archive_mode = kwargs['archive']
        else:
            self.archive_mode = True

        if 'prevent_shutdown' in kwargs:
            self.prevent_shutdown = kwargs['prevent_shutdown']
        else:
            self.prevent_shutdown = False


        self.user = User(user_nickname)
        self.webdriver = get_webdriver(self.user.id, self.dev_mode)
        self.archiver = Archiver(self.webdriver) if self.archive_mode else None
        self.fb = FacebookHandler(self.webdriver)

        try:
            self.init_selenium()
        except Exception as err:
            print(f'Encountered exception in selenium init:{err.__repr__()}')
            self.webdriver.quit()
            raise err

        self.pending_auctions = get_unexpired_auctions(dev=self.dev_mode)
        self.run()

    def init_selenium(self):
        self.fb.login_with(self.user)
        self.user.id = self.fb.get_facebook_id(dev=self.dev_mode)

    def run(self):
        try:
            for auction in self.pending_auctions:
                self.prepare_for_auction(auction)
                self.perform_main_loop()
        finally:
            if not self.prevent_shutdown:
                print('Quitting webdriver...')
                self.webdriver.quit()
            else:
                print("Webdriver quit intentionally prevented (running in shutdown=False mode)")

    print('Finished gracefully')

    def prepare_for_auction(self, auction_instance):
        self.fbgroup = FbGroup()
        self.auctionpost = auction_instance.auction_post
        self.constraints = auction_instance.constraints
        self.extensions_remaining = auction_instance.constraints.extensions
        self.fbclock = FacebookAuctionClock(self.fb, auction_instance.constraints, self.dev_mode)
        self.countdown = CountdownTimer(self.fbclock)

        self.load_auction_page()
        self.auctionpost.name = self.fb.get_auction_name()
        self.print_preamble()
        self.refresh_bid_history(True)
        self.print_bid_history()

    def load_auction_page(self):
        self.fb.load_auction_page(self.fbgroup, self.auctionpost)

    def print_preamble(self):
        print(
            f'Bidding as {self.user.id} on {self.auctionpost.name} to a maximum of {self.constraints.max_bid} '
            f'in steps of {self.constraints.min_bid_step}')
        print(f'    Auction ends {self.constraints.expiry.astimezone(self.user.tz)} user-locale time')

    def perform_main_loop(self):
        try:
            while not self.fbclock.auction_last_call():
                self.iterate()
        except Exception as err:
            print(f'Error in perform_main_loop(): {err.__repr__()}')
            self.save_error_dump_html()
            raise err
        finally:
            self.perform_final_state_output()

    def save_error_dump_html(self):
        try:
            base_dir = os.getcwd()
            timestamp = str(datetime.now().timestamp())
            with open(os.path.join(base_dir, 'err_dump', f'{timestamp}.html'), 'wb+') as out:
                out.write(self.webdriver.page_source.encode('utf-8'))
                out.close()
        except Exception as err:
            print(f'Error writing error dump: {err.__repr__()}')

    def iterate(self):
        try:
            self.sync_clock_if_required()
            self.refresh_bid_history()
            self.countdown.proc()

            if self.winning():
                pass

            elif not self.can_bid():
                pass

            elif self.time_to_snipe():
                print('time to snipe')
                if not self.initial_snipe_performed \
                        and self.constraints.max_bid >= self.get_lowest_valid_bid_value() + 8:
                    # Add a lucky 8 to the initial snipe
                    self.make_bid(1, 8)
                else:
                    self.make_bid()

                self.initial_snipe_performed = True

            elif self.initial_bid_due():
                print('time to make initial bid')
                self.make_bid()

        except StaleElementReferenceException as err:
            print(f'Stale:{err.__repr__()}')

    def sync_clock_if_required(self):
        if self.fbclock.sync_required():
            self.fbclock.init_maximal_delay(10, self.get_auction_url())

    def get_auction_url(self):
        return f'https://www.facebook.com/groups/{self.fbgroup.id}/permalink/{self.auctionpost.id}/'

    def winning(self):
        try:
            return self.valid_bid_history[-1].bidder == self.user.id
        except IndexError:
            return False

    def can_bid(self):
        return self.get_lowest_valid_bid_value() <= self.constraints.max_bid

    def get_lowest_valid_bid_value(self, steps=1):
        try:
            return max(self.constraints.starting_bid,
                       self.valid_bid_history[-1].value + self.constraints.min_bid_step * steps)
        except IndexError:
            return self.constraints.starting_bid

    def time_to_snipe(self):
        initial_snipe_threshold = timedelta(seconds=4)
        return (self.fbclock.get_current_time() > self.constraints.expiry - initial_snipe_threshold
                and not self.initial_snipe_performed) \
               or self.fbclock.auction_last_call()

    def make_bid(self, steps=1, extra=0):
        bid_value = self.get_lowest_valid_bid_value(steps) + extra
        if bid_value != self.most_recent_bid_submission:
            print(f'Preparing to bid {bid_value}')
            if bid_value > self.constraints.max_bid:
                raise ValueError("make_bid(): You cannot bid more than your max_bid_amount!")
            comment_content = f'{bid_value}(autobid)' if self.dev_mode else str(bid_value)
            print(f'Submitting "{comment_content}"')
            self.fb.post_comment(comment_content)

            self.initial_bid_made = True
            self.most_recent_bid_submission = bid_value
            self.trigger_extension()
            sleep(0.05)
        else:
            print('Duplicate bid submission avoided')

    def trigger_extension(self):
        if self.extensions_remaining > 0 \
                and self.fbclock.get_time_remaining() < timedelta(minutes=5):
            self.constraints.expiry += timedelta(minutes=(1 if self.dev_mode else 5))
            self.countdown.reset()
            self.extensions_remaining -= 1
            print(f'Bid placed in final 5min - auction time extended to {self.constraints.expiry}')

    def initial_bid_due(self):
        return self.constraints.make_initial_bid and not self.initial_bid_made

    def perform_final_state_output(self):
        sleep(1)
        self.refresh_final_state()
        if self.archiver:
            self.archive_final_state()
        self.print_final_state()

    def refresh_final_state(self):
        print('Performing final refresh of page and bid history...')
        self.load_auction_page()
        self.refresh_bid_history(True)
        print('    Refreshed!')

    def archive_final_state(self):
        self.archiver.take_screenshot()
        self.archiver.save_final_state_html()

    def print_final_state(self):
        print('Final Auction State:')
        self.print_bid_history()

    def refresh_bid_history(self, force_accurate=False):
        self.fb.remove_all_child_comments()
        comment_elem_list = self.fb.get_comments()

        # If response speed is more critical than maintaining an accurate record
        if self.critical_period_active() and not force_accurate:
            valid_bid_history = self.get_bid_history_quickly(comment_elem_list)
        # Else if operating in non-critical mode
        else:
            valid_bid_history = self.get_bid_history_accurately(comment_elem_list)

        my_valid_bid_count = 0
        for bid in valid_bid_history:
            if bid.bidder == self.user.id:
                my_valid_bid_count += 1

        self.my_valid_bid_count = my_valid_bid_count
        self.initial_bid_made = (my_valid_bid_count > 0)
        self.valid_bid_history = valid_bid_history

    def get_bid_history_quickly(self, comment_elem_list):
        valid_bid_history = []

        # for idx, comment in enumerate(comment_elem_list, start=len(self.valid_bid_history)):
        for idx, comment in enumerate(comment_elem_list):
            try:
                candidate_bid = bidparse.comment_parse(comment)

                if candidate_bid.timestamp >= self.constraints.expiry:
                    raise ValueError()

                if self.potentially_contested(idx, comment_elem_list):
                    print(f"User's bid of {candidate_bid.value} may be contested - disregarding bid")
                    raise ValueError

                if not valid_bid_history \
                        or candidate_bid.value >= valid_bid_history[-1].value + self.constraints.min_bid_step:

                    # If this isn't running during initialisation
                    if self.valid_bid_history and candidate_bid > self.valid_bid_history[-1]:
                        print(f'New bid detected! (fast-mode)')
                        self.print_bid(candidate_bid)

                    valid_bid_history.append(candidate_bid)
            except ValueError:
                pass
            except NoSuchElementException:
                pass
            except Exception:
                pass

        return valid_bid_history

    # Detects user's bids that appear to precede competing bids in client but may not on server
    def potentially_contested(self, comment_idx, comment_elem_list):
        if comment_idx != len(comment_elem_list) - 1:
            comment_elem = comment_elem_list[comment_idx]
            next_comment_elem = comment_elem_list[comment_idx + 1]
            if comment_elem.author == self.user.id \
                    and (comment_elem.timestamp == next_comment_elem.timestamp \
                         or comment_elem.timestamp == next_comment_elem.timestamp + timedelta(seconds=1)) \
                    and not bidparse.comment_parse(comment_elem).value > bidparse.comment_parse(
                next_comment_elem).value:
                return True
        return False

    def get_bid_history_accurately(self, comment_elem_list):
        valid_bid_history = []

        for comment in comment_elem_list:
            try:
                candidate_bid = bidparse.comment_parse(comment)

                if candidate_bid.timestamp >= self.constraints.expiry:
                    raise ValueError()

                if not valid_bid_history \
                        or candidate_bid.value >= valid_bid_history[-1].value + self.constraints.min_bid_step:

                    # If this isn't running during initialisation
                    if self.valid_bid_history and candidate_bid > self.valid_bid_history[-1]:
                        print(f'New bid detected!')
                        self.print_bid(candidate_bid)

                    valid_bid_history.append(candidate_bid)
            except ValueError:
                pass
            except NoSuchElementException:
                pass
            except Exception:
                pass

        return valid_bid_history

    def more_bids_required(self):
        return self.my_valid_bid_count < self.constraints.minimum_bids

    def critical_period_active(self):
        return self.fbclock.get_time_remaining() < timedelta(seconds=5)

    def print_bid(self, bid):
        max_placed_bid_digits = len(str(self.valid_bid_history[-1].value))
        print(f'    {str(bid.value).rjust(max_placed_bid_digits)}NTD '
              f'at {bid.timestamp.month}月{bid.timestamp.day}日 {bid.timestamp.strftime("%H:%M:%S")} '
              f'({bid.bidder})')

    def print_bid_history(self):
        print('Current Bid History:')
        for bid in self.valid_bid_history:
            self.print_bid(bid)
        if self.fbclock.auction_last_call():
            self.print_auction_result()
        else:
            print(f'{self.user.id} has made {self.my_valid_bid_count} valid bids so far '
                  f'({self.constraints.minimum_bids} required)')

    def print_auction_result(self):
        try:
            if self.auction_won():
                print(f'Auction won for {self.valid_bid_history[-1].value}NTD')
            else:
                print(f'Auction lost to {self.valid_bid_history[-1].bidder} ({self.valid_bid_history[-1].value}NTD)')
        except IndexError:
            print(f'Auction contains no valid bids... wtf happened?')

    def auction_won(self):
        try:
            return self.valid_bid_history[-1].bidder == self.user.id \
                   and self.valid_bid_history[-1].timestamp < self.constraints.expiry
        except IndexError:
            return False

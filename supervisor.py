import configparser
from time import sleep
from pytz import utc
from datetime import datetime, timedelta

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
    valid_bid_history = None
    my_valid_bid_count = 0
    courtesy_bid_scheduled = None
    safety_margin = timedelta(milliseconds=100)

    def __init__(self, user_nickname='alex', **kwargs):
        config = configparser.ConfigParser()

        if 'dev' in kwargs and kwargs['dev']:
            self.dev_mode = True
            config.read('test_config.ini')
        else:
            self.dev_mode = False
            config.read('live_config.ini')

        self.auctionpost = AuctionPost(config['Auction']['AuctionId'])
        self.constraints = ConstraintSet(self.dev_mode)
        self.extensions_remaining = self.constraints.extensions
        self.user = User(user_nickname)

        self.webdriver = get_webdriver(self.user.id)
        self.archiver = Archiver(self.webdriver)
        self.fb = FacebookHandler(self.webdriver)
        self.fbgroup = FbGroup(config['Auction']['GroupNickname'])
        self.fbclock = FacebookAuctionClock(self.fb, self.constraints, self.dev_mode)
        self.countdown = CountdownTimer(self.fbclock)

        try:
            self.init_selenium()
        except Exception as err:
            print(f'Encountered exception in supervisor init:{err.__repr__()}')
            self.webdriver.quit()
            raise err

    def init_selenium(self):
        self.fb.login_with(self.user)
        self.user.id = self.fb.get_facebook_id(dev=self.dev_mode)
        self.fb.load_auction_page(self.fbgroup, self.auctionpost)
        self.auctionpost.name = self.fb.get_auction_name()
        self.print_preamble()
        self.refresh_bid_history(True)
        self.print_bid_history()

    def print_preamble(self):
        print(
            f'Bidding as {self.user.id} on {self.auctionpost.name} to a maximum of {self.constraints.max_bid} '
            f'in steps of {self.constraints.min_bid_step}')
        print(f'    Auction ends {self.constraints.expiry.astimezone(self.user.tz)} user-locale time')

    def perform_main_loop(self):
        try:
            while not self.fbclock.auction_expired():
                self.iterate()
        except Exception as err:
            print(f'Error in perform_main_loop(): {err.__repr__()}')
            self.archiver.save_error_dump_html()
            raise err
        finally:
            try:
                self.shutdown()
            finally:
                print('Quitting webdriver...')
                self.webdriver.quit()
            print('Exited gracefully')

    def iterate(self):
        try:
            self.fbclock.sync_if_required()
            self.refresh_bid_history()
            self.countdown.proc()

            if self.winning():
                pass
            elif not self.can_bid():
                pass
            elif self.time_to_snipe():
                print('time to snipe')
                self.make_bid()
            elif self.initial_bid_due():
                print('time to make initial bid')
                self.make_bid()
            elif (not self.critical_period_active()) and self.courtesy_bid_due():
                print('time to make courtesy bid')  # doesn't seem to trigger correctly
                self.make_bid()

        except StaleElementReferenceException as err:
            print(f'Stale:{err.__repr__()}')

    def winning(self):
        try:
            return self.valid_bid_history[-1].bidder == self.user.id
        except IndexError:
            return False

    def can_bid(self):
        return self.get_lowest_valid_bid_value() <= self.constraints.max_bid

    def get_lowest_valid_bid_value(self):
        try:
            return max(self.constraints.starting_bid,
                       self.valid_bid_history[-1].value + self.constraints.min_bid_step)
        except IndexError:
            return self.constraints.starting_bid

    def time_to_snipe(self):
        return self.fbclock.get_current_time() > self.constraints.expiry - self.safety_margin

    def make_bid(self):
        bid_value = self.get_lowest_valid_bid_value()
        print(f'Preparing to bid {bid_value}')
        if bid_value > self.constraints.max_bid:
            raise ValueError("make_bid(): You cannot bid more than your max_bid_amount!")
        comment_content = f'{bid_value}(autobid)' if self.dev_mode else str(bid_value)
        print(f'Submitting "{comment_content}"')
        self.fb.post_comment(comment_content)

        self.trigger_extension()
        self.courtesy_bid_scheduled = None
        self.valid_bid_history.append(Bid(self.user.id, bid_value))
        sleep(0.05)

    def trigger_extension(self):
        if self.extensions_remaining > 0 \
                and self.fbclock.get_time_remaining() < timedelta(minutes=5):
            self.constraints.expiry += timedelta(minutes=(1 if self.dev_mode else 5))
            self.countdown.reset()
            self.extensions_remaining -= 1
            print(f'Bid placed in final 5min - auction time extended to {self.constraints.expiry}')

    def initial_bid_due(self):
        return self.my_valid_bid_count < 1 and self.constraints.make_initial_bid

    def courtesy_bid_due(self):
        return False if not self.courtesy_bid_scheduled \
            else (self.my_valid_bid_count < self.constraints.minimum_bids
                  and self.fbclock.get_current_time() > self.courtesy_bid_scheduled)

    def shutdown(self):
        print('Performing final refresh of page and bid history...')
        self.fb.load_auction_page(self.fbgroup, self.auctionpost)
        self.refresh_bid_history(True)
        print('    Refreshed!')

        self.archiver.take_screenshot()
        self.archiver.save_final_state_html()

        print('Final Auction State:')
        self.print_bid_history()

    def refresh_bid_history(self, force_accurate=False):
        self.fb.remove_all_child_comments()
        comment_elem_list = self.fb.get_comments()

        # If response speed is more critical than maintaining an accurate record
        if self.critical_period_active() and not force_accurate:
            print('critical')
            valid_bid_history = self.get_bid_history_quickly(comment_elem_list)
        # Else if operating in non-critical mode
        else:
            valid_bid_history = self.get_bid_history_accurately(comment_elem_list)

        my_valid_bid_count = 0
        for bid in valid_bid_history:
            if bid.bidder == self.user.id:
                my_valid_bid_count += 1

        self.my_valid_bid_count = my_valid_bid_count
        self.valid_bid_history = valid_bid_history

    def get_bid_history_quickly(self, comment_elem_list):
        valid_bid_history = self.valid_bid_history if self.valid_bid_history else []
        valid_bid_found = False

        # Look for the most recent bid gte the known high bid and consider that to be the high bid
        for comment in reversed(comment_elem_list):
            try:
                candidate_bid = bidparse.comment_parse(comment)

                if not valid_bid_history \
                        or candidate_bid.value >= valid_bid_history[-1].value + self.constraints.min_bid_step:
                    if self.valid_bid_history and candidate_bid > self.valid_bid_history[-1]:
                        print(f'New bid detected (desperation mode)!')
                        self.print_bid(candidate_bid)

                    valid_bid_history.append(candidate_bid)
                    valid_bid_found = True

                elif candidate_bid.value == valid_bid_history[-1].value:
                    valid_bid_found = True

            except ValueError:
                pass
            except StaleElementReferenceException:
                pass
            except NoSuchElementException as err:
                print(err.__repr__())
                pass
            except Exception as err:
                print('Exception in get_bid_history_quickly')
                raise err

            if valid_bid_found:
                # Break out of the loop and respond to the new bid immediately
                break

        return valid_bid_history

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
                        if not self.courtesy_bid_scheduled:
                            self.schedule_courtesy_bid()

                    valid_bid_history.append(candidate_bid)
            except ValueError:
                pass
            except NoSuchElementException:
                pass
            except Exception:
                pass

        return valid_bid_history

    def schedule_courtesy_bid(self):
        if self.more_bids_required():
            now = self.fbclock.get_current_time()
            print(f'Scheduling bid for {now}')
            self.courtesy_bid_scheduled = now if self.dev_mode else now + (self.constraints.expiry - now) / 2

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
        if self.fbclock.auction_expired():
            self.print_auction_result()
        else:
            print(f'{self.user.id} has made {self.my_valid_bid_count} valid bids so far '
                  f'({self.constraints.minimum_bids} required)')

    def print_auction_result(self):
        if self.auction_won():
            print(f'Auction won for {self.valid_bid_history[-1].value}NTD')
        else:
            print(f'Auction lost to {self.valid_bid_history[-1].bidder} ({self.valid_bid_history[-1].value}NTD)')

    def auction_won(self):
        return self.valid_bid_history[-1].bidder == self.user.id \
               and self.valid_bid_history[-1].timestamp < self.constraints.expiry

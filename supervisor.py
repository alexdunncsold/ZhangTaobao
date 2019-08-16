from bid import Bid
import bidparse
import configparser
import facebook as fb
from datetime import datetime, timedelta
from time import sleep
from pytz import utc

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from auctionpost import AuctionPost
from constraintset import ConstraintSet
from fbgroup import FbGroup
from fbtimesync import FbTimeSync
from user import User
from webdriver import get_webdriver


class Supervisor:
    valid_bid_history = None
    my_valid_bid_count = 0
    courtesy_bid_scheduled = None
    countdown_seconds_notifications = [1, 2, 3, 4, 5, 10, 30]
    countdown_complete = False
    safety_margin = timedelta(milliseconds=100)

    def __init__(self, mode, user_nickname='alex'):
        config = configparser.ConfigParser()

        if mode == 'dev' or mode == 'test':
            self.mode = 'dev'
            config.read('test_config.ini')
        elif mode == 'live':
            self.mode = 'live'
            config.read('live_config.ini')
        else:
            raise ValueError(f'Invalid mode "{mode}" specified')

        self.auctionpost = AuctionPost(config['Auction']['AuctionId'])
        self.constraints = ConstraintSet(mode)
        self.extensions_remaining = self.constraints.extensions
        self.fbgroup = FbGroup(config['Auction']['GroupNickname'])
        self.sync = FbTimeSync()
        self.user = User(user_nickname)

        self.driver = get_webdriver(self.user.id)
        try:
            self.init_selenium()
        except Exception as err:
            print(f'Encountered exception in supervisor init:{err.__repr__()}')
            self.driver.quit()
            raise err

    def init_selenium(self):
        fb.login_with(self.driver, self.user)
        self.user.id = fb.get_facebook_id(self.driver, dev=(self.mode == 'dev'))
        fb.load_auction_page(self.driver, self.fbgroup, self.auctionpost)
        self.auctionpost.name = fb.get_auction_name(self.driver)
        self.print_preamble()
        self.refresh_bid_history(True)
        self.print_bid_history()

    def print_preamble(self):
        print(
            f"Bidding as {self.user.id} on {self.auctionpost.name} to a maximum of {self.constraints.max_bid} in steps of {self.constraints.min_bid_step}")
        print(f'    Auction ends {self.constraints.expiry.astimezone(self.user.tz)}')

    def perform_main_loop(self):
        try:
            while self.get_current_time() < self.constraints.expiry:
                self.iterate()
        except Exception as err:
            print(f'Error in perform_main_loop(): {err.__repr__()}')
            with open('err_dump.html', 'wb+') as out:
                out.write(self.driver.page_source.encode('utf-8'))
                out.close()
            raise err
        finally:
            try:
                self.shutdown()
            finally:
                print('Quitting webdriver...')
                self.driver.quit()
            print('Exited gracefully')

    def iterate(self):
        try:
            if self.sync_required():
                self.sync.init_maximal_delay(self.driver, 10 if self.mode != 'dev' else 3)

            self.refresh_bid_history()
            self.proc_countdown()

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
                print('time to make courtesy bid')
                self.make_bid()

        except StaleElementReferenceException as err:
            print(f'Stale:{err.__repr__()}')

    def sync_required(self):
        system_time = datetime.utcnow().replace(tzinfo=utc)
        return self.constraints.expiry - system_time < self.sync.sync_threshold and not self.sync.maximal_delay

    def winning(self):
        try:
            return self.valid_bid_history[-1].bidder == self.user.id
        except IndexError as err:
            return False

    def can_bid(self):
        return self.get_lowest_valid_bid_value() <= self.constraints.max_bid

    def get_lowest_valid_bid_value(self):
        try:
            return max(self.constraints.starting_bid,
                       self.valid_bid_history[-1].value + self.constraints.min_bid_step)
        except IndexError as err:
            return self.constraints.starting_bid

    def time_to_snipe(self):
        return self.get_current_time() > self.constraints.expiry - self.safety_margin

    def make_bid(self):
        bid_value = self.get_lowest_valid_bid_value()
        print(f'Preparing to bid {bid_value}')
        if bid_value > self.constraints.max_bid:
            raise ValueError("make_bid(): You cannot bid more than your max_bid_amount!")
        comment_content = f'{bid_value}(autobid)' if self.mode == 'dev' else str(bid_value)
        print(f'Submitting "{comment_content}"')
        fb.post_comment(self.driver, comment_content)

        self.trigger_extension()
        self.courtesy_bid_scheduled = None
        self.valid_bid_history.append(Bid(self.user.id, bid_value))
        sleep(0.05)

    def trigger_extension(self):
        if self.extensions_remaining > 0 \
                and self.get_time_remaining() < timedelta(minutes=5):
            self.constraints.expiry += timedelta(minutes=(1 if self.mode == 'dev' else 5))
            self.extensions_remaining -= 1
            print(f'Bid placed in final 5min - auction time extended to {self.constraints.expiry}')

    def initial_bid_due(self):
        return self.my_valid_bid_count < 1 and self.constraints.make_initial_bid

    def courtesy_bid_due(self):
        return False if not self.courtesy_bid_scheduled else self.my_valid_bid_count < self.constraints.minimum_bids \
                                                             and self.get_current_time() > self.courtesy_bid_scheduled

    def shutdown(self):
        print('Performing final refresh of page and bid history...')
        fb.load_auction_page(self.driver, self.fbgroup, self.auctionpost)
        self.refresh_bid_history(True)
        print('    Refreshed!')

        fb.take_screenshot(self.driver)

        try:
            with open('final_state_dump.html', 'wb+') as out:
                out.write(self.driver.page_source.encode('utf-8'))
                out.close()
        except Exception as err:
            print(f'Error writing final-state html: {err.__repr__()}')

        print('Final Auction State:')
        self.print_bid_history()

    def refresh_bid_history(self, force_accurate=False):
        fb.remove_all_child_comments(self.driver)
        comment_elem_list = fb.get_comments(self.driver)

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

    def proc_countdown(self):  # todo extract to class later
        try:
            if self.get_time_remaining() >= timedelta(minutes=1):
                raise ValueError

            if not self.auction_expired() \
                    and self.get_time_remaining() < timedelta(seconds=self.countdown_seconds_notifications[-1]):
                print(f'{str(self.countdown_seconds_notifications.pop()).rjust(10)} seconds remaining!')
            elif self.auction_expired() and not self.countdown_complete:
                self.countdown_complete = True
                print(f'Auction Complete! at {self.get_current_time()} with {self.get_time_remaining()} left')
        except IndexError as err:
            pass
        except ValueError as err:
            pass

    def auction_expired(self):
        return self.get_time_remaining().days == -1

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
                        self.schedule_courtesy_bid()

                    valid_bid_history.append(candidate_bid)
            except ValueError as err:
                pass
            except NoSuchElementException as err:
                pass
            except Exception as err:
                pass

        return valid_bid_history

    def schedule_courtesy_bid(self):
        if self.more_bids_required():
            now = self.get_current_time()
            print(f'Scheduling bid for {now}')
            self.courtesy_bid_scheduled = now if self.mode == 'dev' else (self.constraints.expiry - now) / 2

    def more_bids_required(self):
        return self.my_valid_bid_count < self.constraints.minimum_bids

    def critical_period_active(self):
        return self.get_time_remaining() < timedelta(seconds=45)  # timedelta(seconds=5)

    def get_current_time(self):
        return datetime.utcnow().replace(tzinfo=utc) + self.sync.get_maximal_delay()

    def get_time_remaining(self):
        time_remaining = self.constraints.expiry - self.get_current_time()
        return time_remaining

    def print_bid(self, bid):
        max_placed_bid_digits = len(str(self.valid_bid_history[-1].value))
        print(f'    {str(bid.value).rjust(max_placed_bid_digits)}NTD '
              f'at {bid.timestamp.month}月{bid.timestamp.day}日 {bid.timestamp.strftime("%H:%M:%S")} '
              f'({bid.bidder})')

    def print_bid_history(self):
        print('Current Bid History:')
        for bid in self.valid_bid_history:
            self.print_bid(bid)
        if self.auction_expired():
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

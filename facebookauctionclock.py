import configparser
from datetime import datetime, timedelta
from facebookhandler import FacebookHandler
from facebookgroup import FbGroup
from pytz import utc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import math
import statistics

import random


class FacebookAuctionClock:

    def __init__(self, fb, constraints, dev_mode=False):
        self.fb = fb
        self.constraints = constraints
        self.dev_mode = dev_mode

        config = configparser.ConfigParser()
        config.read('sync_config.ini')

        self.maximal_delay = None
        self.group = FbGroup('sync')
        self.url = f"https://www.facebook.com/groups/{self.group.id}/permalink/{config['post']['Id']}/"

        self.sync_threshold = timedelta(minutes=int(config['settings']['SyncThresholdMinutes']))
        self.abort_threshold = timedelta(seconds=int(config['settings']['SyncAbortThresholdSeconds']))
        self.maximal_delay_safety_buffer = timedelta(
            milliseconds=int(config['settings']['DelaySafetyBufferMilliseconds']))
        self.default_posting_delay = timedelta(seconds=int(config['settings']['SafeDefaultPostingDelaySeconds']))

    def sync_if_required(self):
        if self.sync_required():
            self.init_maximal_delay(3)

    def sync_required(self):
        system_time = datetime.utcnow().replace(tzinfo=utc)
        return self.constraints.expiry - system_time < self.sync_threshold and not self.maximal_delay

    def auction_expired(self):
        return self.get_raw_time_remaining().days == -1
        return

    # Get actual time, without posting-delay adjustment
    def get_raw_time_remaining(self):
        system_time = datetime.utcnow().replace(tzinfo=utc)
        time_remaining = self.constraints.expiry - system_time
        return time_remaining

    # Get an adjusted representation of time, accounting for maximal posting delay
    def get_time_remaining(self):
        time_remaining = self.constraints.expiry - self.get_current_time()
        return time_remaining

    def get_current_time(self):
        return datetime.utcnow().replace(tzinfo=utc) + self.get_maximal_delay()

    def get_maximal_delay(self):
        return self.maximal_delay if self.maximal_delay else timedelta(seconds=0)

    def init_maximal_delay(self, trials, return_to_url=None):
        if not return_to_url:
            return_to_url = self.fb.webdriver.current_url

        try:
            self.load_sync_page()
            mean_posting_delay = self.get_mean_posting_delay(trials)
            self.maximal_delay = mean_posting_delay \
                                 + self.maximal_delay_safety_buffer
            print(f'\n    Mean posting delay = {self.timedelta_to_ms(mean_posting_delay)}ms')

        except RuntimeError:
            self.maximal_delay = timedelta(seconds=5)
            print(f'\n    Error when determining posting delay')

        print(
            f'    Maximal delay set to {self.timedelta_to_ms(self.maximal_delay)}ms')

        # Navigate back to the auction page
        print(f'    Navigating back to {return_to_url}')
        self.fb.webdriver.get(return_to_url)
        print(f'    Successfully navigated back to {return_to_url}')

    def load_sync_page(self):
        print('    Attempting to load sync page')
        self.fb.webdriver.get(self.url)
        if self.group.name in self.fb.webdriver.title:
            print("    Loaded sync page!  Please be patient", end='')
        else:
            raise RuntimeError(
                "load_auction_page(): Failed to load sync page")

    @staticmethod
    def timedelta_to_ms(td):
        if td < timedelta(0):
            return -1 * (math.ceil(abs(td).seconds * 1000 + abs(td).microseconds / 1000))
        else:
            return math.ceil(td.seconds * 1000 + td.microseconds / 1000)

    def get_mean_posting_delay(self, trials):
        delay_results_ms = []
        try:
            for trial in range(0, trials):
                posting_delay = self.get_posting_delay_datum()
                if posting_delay < timedelta(0):
                    delay_ms = self.timedelta_to_ms(posting_delay)
                else:
                    delay_ms = self.timedelta_to_ms(posting_delay)
                delay_results_ms.append(delay_ms)

                if self.get_time_remaining() < self.abort_threshold:  # todo find out why this never seems to trigger
                    raise RuntimeError(
                        f'Less than {self.abort_threshold.seconds} seconds left in auction, aborting test after ' +
                        f'{len(delay_results_ms)} tests')
        except RuntimeError as err:
            print(f'\n    {err.__repr__()}')

        print(f'\ndelay-data ({statistics.mean(delay_results_ms)}ms): {sorted(delay_results_ms)}')
        print(
            f'culled to  ({statistics.mean(self.strip_outliers(delay_results_ms))}ms): {sorted(self.strip_outliers(delay_results_ms))}')
        print(
            f'lows-culled ({statistics.mean(self.strip_low_outliers(delay_results_ms))}ms): {sorted(self.strip_outliers(delay_results_ms))}')
        return timedelta(milliseconds=statistics.mean(delay_results_ms)) if delay_results_ms \
            else self.default_posting_delay

    @staticmethod
    def strip_outliers(data, factor=1.5):
        mean = statistics.mean(data)
        sd = statistics.stdev(data, mean)
        return [item for item in data if abs(item - mean) < factor * sd]

    @staticmethod
    def strip_low_outliers(data, factor=1.5):
        mean = statistics.mean(data)
        sd = statistics.stdev(data, mean)
        return [item for item in data if item >= mean or abs(item - mean) < factor * sd]

    def get_posting_delay_datum(self):
        # If this method is called without being on sync page, load sync page
        if self.group.name not in self.fb.webdriver.title:
            self.load_sync_page()

        print('.', end='')
        post_attempted = self.fb.post_comment(self.nonsense() if self.dev_mode else '    Syncing...')
        self.fb.webdriver.get(self.url)
        post_registered = self.fb.get_last_comment_registered_at()
        posting_delay = post_registered - post_attempted + timedelta(milliseconds=500)

        # Perform cleanup
        sleep(1)  # todo use implicit_wait
        self.fb.delete_last_comment()

        return posting_delay

    @staticmethod
    def nonsense():
        word_count = random.randint(3, 10)
        word_list = ('here', 'are', 'some', 'words', 'to', 'try', 'and', 'beat', 'the', 'spam', 'filter')
        output = ' '.join([word_list[random.randint(0, len(word_list) - 1)] for word in range(0, word_count)])
        return output

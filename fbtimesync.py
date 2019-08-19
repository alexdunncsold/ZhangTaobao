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


class FbTimeSync:

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

    def sync_if_required(self):
        if self.sync_required():
            self.init_maximal_delay(10 if self.dev_mode else 3)

    def sync_required(self):
        system_time = datetime.utcnow().replace(tzinfo=utc)
        return self.constraints.expiry - system_time < self.sync_threshold and not self.maximal_delay

    def auction_expired(self):
        return self.get_time_remaining().days == -1

    def get_time_remaining(self):
        time_remaining = self.constraints.expiry - self.get_current_time()
        return time_remaining

    def get_current_time(self):
        return datetime.utcnow().replace(tzinfo=utc) + self.get_maximal_delay()

    def get_maximal_delay(self):
        return self.maximal_delay if self.maximal_delay else timedelta(seconds=0)

    def init_maximal_delay(self, trials):
        auction_url = self.fb.webdriver.current_url
        try:
            self.load_sync_page()
            mean_posting_delay = self.get_mean_posting_delay(trials)
            self.maximal_delay = mean_posting_delay + timedelta(milliseconds=500)
            print(
                f'    Mean posting delay = {self.timedelta_to_ms(mean_posting_delay)}ms')

        except RuntimeError:
            self.maximal_delay = timedelta(seconds=5)
            print(f'    Error when determining posting delay')

        print(
            f'    Maximal delay set to {self.timedelta_to_ms(self.maximal_delay)}ms')

        # Navigate back to the auction page
        print(f'    Navigating back to {auction_url}')
        self.fb.webdriver.get(auction_url)

    def load_sync_page(self):
        print('    Attempting to load sync page')
        self.fb.webdriver.get(self.url)
        if self.group.name in self.fb.webdriver.title:
            print("    Loaded sync page!  Please be patient...")
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
        start_time = datetime.now()
        abort_threshold = timedelta(minutes=3)  # todo store abort threshold in config in future
        delay_results_ms = []
        try:
            for trial in range(0, trials):
                posting_delay = self.get_posting_delay_datum()
                if posting_delay < timedelta(0):
                    delay_ms = self.timedelta_to_ms(posting_delay)
                else:
                    delay_ms = self.timedelta_to_ms(posting_delay)
                delay_results_ms.append(delay_ms)

                # Having completed at least one test, abort if the auction will end in tne near future
                sync_time_elapsed = datetime.now() - start_time
                auction_time_remaining = self.sync_threshold - sync_time_elapsed
                if auction_time_remaining < abort_threshold:
                    raise RuntimeError(
                        f'Less than {abort_threshold.seconds / 60} minutes left in auction, aborting test after ' +
                        f'{len(delay_results_ms)} tests')
        except RuntimeError as err:
            print(f'    {err.__repr__()}')

        return timedelta(milliseconds=statistics.mean(delay_results_ms)) if delay_results_ms else timedelta(
            seconds=5)  # store safe value in config in future

    def get_posting_delay_datum(self):
        # If this method is called without being on sync page, load sync page
        if self.group.name not in self.fb.webdriver.title:
            self.load_sync_page()

        accuracy_tolerance = 0
        while datetime.now().microsecond > 1000 + accuracy_tolerance:
            # Do nothing - we want to sync as close to on-the-second as possible
            accuracy_tolerance += 100

        post_attempted = datetime.utcnow().replace(tzinfo=utc)
        self.fb.post_comment('    Syncing...')
        self.fb.webdriver.get(self.url)
        post_registered = self.fb.get_last_comment_registered_at()
        posting_delay = post_registered - post_attempted + timedelta(seconds=1)

        # Perform cleanup
        sleep(1)
        el = self.fb.webdriver.find_elements_by_class_name('_2f3a')
        action = ActionChains(self.fb.webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys('d').send_keys(Keys.ENTER).send_keys(
            Keys.ENTER).perform()
        sleep(0.5)
        el = self.fb.webdriver.find_elements_by_class_name('_4jy0')
        action = ActionChains(self.fb.webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys(Keys.ENTER).perform()
        self.fb.webdriver.get(self.url)

        return posting_delay

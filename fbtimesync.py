import configparser
from datetime import datetime, timedelta
import facebook as fb
from fbgroup import FbGroup
from pytz import utc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import math
import statistics


class FbTimeSync:
    maximal_delay = None

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('sync_config.ini')

        self.group = FbGroup('sync')
        self.url = f"https://www.facebook.com/groups/{self.group.id}/permalink/{config['post']['Id']}/"
        self.sync_threshold = timedelta(minutes=int(config['settings']['SyncThresholdMinutes']))

    def get_maximal_delay(self):
        return self.maximal_delay if self.maximal_delay else timedelta(seconds=0)

    def init_maximal_delay(self, webdriver):
        auction_url = webdriver.current_url
        try:
            self.load_sync_page(webdriver)
            mean_posting_delay = self.get_mean_posting_delay(webdriver, 10)
            self.maximal_delay = mean_posting_delay + timedelta(milliseconds=500)
            print(
                f'    Mean posting delay = {mean_posting_delay.seconds * 1000 + mean_posting_delay.microseconds / 1000}ms')

        except RuntimeError as err:
            self.maximal_delay = timedelta(seconds=5)
            print(f'    Error when determining posting delay')

        print(
            f'    Maximal delay set to {self.maximal_delay.seconds * 1000 + self.maximal_delay.microseconds / 1000}ms')

        # Navigate back to the auction page
        print(f'    Navigating back to {auction_url}')
        webdriver.get(auction_url)

    def load_sync_page(self, webdriver):
        print('    Attempting to load sync page')
        webdriver.get(self.url)
        if self.group.name in webdriver.title:
            print("    Loaded sync page!  Please be patient...")
        else:
            raise RuntimeError(
                "load_auction_page(): Failed to load sync page")

    def timedelta_to_ms(self, td):
        if td < timedelta(0):
            return -1 * (math.ceil(abs(td).seconds * 1000 + abs(td).microseconds / 1000))
        else:
            return math.ceil(td.seconds * 1000 + td.microseconds / 1000)

    def get_mean_posting_delay(self, webdriver, trials):
        delay_results_ms = []
        for trial in range(0, trials):
            posting_delay = self.get_posting_delay_datum(webdriver)
            if posting_delay < timedelta(0):
                delay_ms = self.timedelta_to_ms(posting_delay)
            else:
                delay_ms = self.timedelta_to_ms(posting_delay)
            delay_results_ms.append(delay_ms)

        return timedelta(milliseconds=statistics.mean(delay_results_ms))

    def get_posting_delay_datum(self, webdriver):
        # If this method is called without being on sync page, load sync page
        if not self.group.name in webdriver.title:
            webdriver.get(self.url)

        accuracy_tolerance = 0
        while datetime.now().microsecond > 1000 + accuracy_tolerance:
            # Do nothing - we want to sync as close to on-the-second as possible
            accuracy_tolerance += 100

        post_attempted = datetime.utcnow().replace(tzinfo=utc)
        fb.post_comment(webdriver, '    Syncing...')
        webdriver.get(self.url)
        post_registered = fb.get_last_comment_registered_at(webdriver)
        posting_delay = post_registered - post_attempted + timedelta(seconds=1)

        # Perform cleanup
        sleep(1)
        el = webdriver.find_elements_by_class_name('_2f3a')
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys('d').send_keys(Keys.ENTER).send_keys(
            Keys.ENTER).perform()
        sleep(0.5)
        el = webdriver.find_elements_by_class_name('_4jy0')
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys(Keys.ENTER).perform()
        webdriver.get(self.url)

        return posting_delay

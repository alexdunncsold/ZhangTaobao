import configparser
from datetime import datetime, timedelta
import facebook as fb
from fbgroup import FbGroup
from pytz import utc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep


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
        # print('initialising maximal delay')
        # self.maximal_delay = timedelta(seconds=1)
        auction_url = webdriver.current_url
        print('    Attempting to load sync page')
        webdriver.get(self.url)
        if self.group.name in webdriver.title:
            print("    Loaded sync page!")
        else:
            raise RuntimeError(
                "load_auction_page(): Failed to load sync page")

        accuracy_tolerance = 0
        while datetime.now().microsecond > 1000 + accuracy_tolerance:
            # Do nothing - we want to sync as close to on-the-second as possible
            accuracy_tolerance += 100

        post_attempted = datetime.utcnow().replace(tzinfo=utc)
        fb.post_comment(webdriver, '    Syncing...')
        webdriver.get(self.url)
        post_registered = fb.get_last_comment_registered_at(webdriver)

        self.maximal_delay = post_registered - post_attempted + timedelta(seconds=1)
        print(f'    Posting with an approximate maximal delay of {self.maximal_delay}')

        # Perform cleanup
        sleep(1)
        el = webdriver.find_elements_by_class_name('_2f3a')
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys('d').send_keys(Keys.ENTER).send_keys(
            Keys.ENTER).perform()
        sleep(500)
        el = webdriver.find_elements_by_class_name('_4jy0')
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(el[-1], 2, 2).click().perform()

        # Navigate back to the auction page
        print(f'    Navigating back to {auction_url}')
        webdriver.get(auction_url)

from datetime import datetime, timedelta
from facebookinteractions import *
from pytz import utc


def get_short_expiry():
    t = datetime.utcnow().replace(tzinfo=utc)
    new_minutes = t.minute + 1 if t.second < 45 else t.minute + 2
    return datetime(t.year, t.month, t.day, t.hour, new_minutes, 0, 0, tzinfo=utc)


def get_offset(webdriver, context):
    sync_thread_url = 'https://www.facebook.com/groups/1309664552543876/permalink/1327444900765841/'

    print('    Attempting to load sync page')
    webdriver.get(sync_thread_url)
    if "Battlefield Pu'er" in webdriver.title:
        print("    Loaded sync page!")
    else:
        raise RuntimeError(
            "load_auction_page(): Failed to load sync page")

    while datetime.now().microsecond > 1000:
        # Do nothing - we want to sync as close to on-the-second as possible
        pass

    post_attempted = datetime.utcnow().replace(tzinfo=utc)
    post_comment(webdriver, '    Syncing...')
    webdriver.get(sync_thread_url)
    post_registered = get_post_registered(webdriver)

    posting_delay = post_registered - post_attempted + timedelta(seconds=1)
    print(f'Posting with an approximate maximal delay of {posting_delay}')

    return posting_delay


def get_post_registered(webdriver):
    # refresh page to ensure that correct timestamp is loaded in DOM
    webdriver.get(webdriver.current_url)

    timestamp_element = webdriver.find_elements_by_class_name('livetimestamp')[-1]
    timestamp_str = timestamp_element.get_attribute('data-utime')
    post_registered = datetime.utcfromtimestamp(int(timestamp_str)).replace(tzinfo=utc)
    return post_registered

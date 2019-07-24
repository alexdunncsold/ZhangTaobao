from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from commenttextparser import parse_bid
from datetime import datetime, timedelta
from time import sleep

from bid import Bid


def login_to_facebook(webdriver, auction_context):
    print("Attempting to load https://www.facebook.com/ ...")
    webdriver.get("https://www.facebook.com/")
    if 'facebook' in webdriver.title.lower() \
            and 'log in or sign up' in webdriver.title.lower():
        print("Loaded Facebook login page!")

        email_elem = webdriver.find_element_by_id('email')
        email_elem.clear()
        email_elem.send_keys(auction_context.credentials.email)

        password_elem = webdriver.find_element_by_id('pass')
        password_elem.clear()
        password_elem.send_keys(auction_context.credentials.password)

        print("Logging in...")
        password_elem.send_keys(Keys.RETURN)

    elif 'facebook' in webdriver.title.lower():
        print("Already logged in.")
    else:
        raise RuntimeError('login_to_facebook(): Failed to load www.facebook.com')

    auction_context.my_facebook_id = \
    webdriver.find_element_by_class_name('_606w').get_attribute('href').split('https://www.facebook.com/')[1]
    if auction_context.run_config == 'dev':
        auction_context.my_facebook_id += '/dev'


def load_auction_page(webdriver, context):
    post_permalink = 'https://www.facebook.com/groups/{}/permalink/{}/'.format(context.facebook_group.id, context.auction.id)
    print('Attempting to load {}'.format(post_permalink))
    webdriver.get(post_permalink)
    if context.facebook_group.name in webdriver.title:
        print("Loaded auction page!")
    else:
        raise RuntimeError("load_auction_page(): Failed to load page with title {}".format(context.facebook_group.name))


def remove_all_child_comments(webdriver):
    child_comment_removal_script = '''
                elements = document.getElementsByClassName("_2h2j");
                for (let e of elements) {e.innerHTML='';};
            '''
    webdriver.execute_script(child_comment_removal_script)


def make_bid(webdriver, auction_context, bid_amount):
    print('Preparing to bid {}'.format(bid_amount))
    if bid_amount > auction_context.max_bid_amount:
        raise ValueError("make_bid(): You cannot bid more than your max_bid_amount!")
    all_comments_elem = webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")
    reply_elem.send_keys(str(bid_amount) + '(autobid)' if auction_context.run_config == 'dev' else str(bid_amount))

    print('    Submitting {}'.format(bid_amount))
    auction_context.auction.trigger_extension()
    reply_elem.send_keys(Keys.RETURN)
    sleep(0.2)

    auction_context.my_active_bid = bid_amount
    auction_context.bids_placed += 1

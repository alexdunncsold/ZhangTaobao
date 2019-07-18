from selenium.webdriver.common.keys import Keys
from commenttextparser import parse_bid
from datetime import datetime, timedelta
from time import sleep


def login_to_facebook(webdriver, credentials):
    print("Attempting to load https://www.facebook.com/ ...")
    webdriver.get("https://www.facebook.com/")
    if 'facebook' in webdriver.title.lower() \
            and 'log in or sign up' in webdriver.title.lower():
        print("Loaded Facebook login page!")

        email_elem = webdriver.find_element_by_id('email')
        email_elem.clear()
        email_elem.send_keys(credentials.email)

        password_elem = webdriver.find_element_by_id('pass')
        password_elem.clear()
        password_elem.send_keys(credentials.password)

        print("Logging in...")
        password_elem.send_keys(Keys.RETURN)

    elif 'facebook' in webdriver.title.lower():
        print("Already logged in.")
    else:
        raise RuntimeError('login_to_facebook(): Failed to load www.facebook.com')


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


def parse_bid_history(webdriver, context):
    remove_all_child_comments(webdriver)

    valid_bid_history = [0, ]
    comment_elem_list = webdriver.find_elements_by_class_name('_3l3x')
    for comment in comment_elem_list:
        try:
            comment_bid_amount = parse_bid(comment.text)
            if comment_bid_amount >= valid_bid_history[-1] + context.auction.min_bid_step:
                valid_bid_history.append(comment_bid_amount)
        except ValueError as err:
            pass
    return valid_bid_history


def make_bid(webdriver, auction_context, bid_amount):
    print('Preparing to bid {}'.format(bid_amount))
    if bid_amount > auction_context.max_bid_amount:
        raise ValueError("make_bid(): You cannot bid more than your max_bid_amount!")
    all_comments_elem = webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")
    reply_elem.send_keys(str(bid_amount) + '(autobid)' if auction_context.run_config == 'dev' else str(bid_amount))
    print('Submitting bid of {}'.format(bid_amount))
    reply_elem.send_keys(Keys.RETURN)
    sleep(0.5)

    auction_context.my_active_bid = bid_amount
    auction_context.bids_placed += 1


def make_bid_without_submit(webdriver, auction_context, bid_amount):
    print('Preparing to bid {}'.format(bid_amount))
    all_comments_elem = webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")
    reply_elem.send_keys(str(bid_amount))
    print('Ready to submit bid of {} - halting for 5 seconds'.format(bid_amount))
    sleep(0.5)

    auction_context.my_active_bid = bid_amount
    auction_context.bids_placed += 1

    then = datetime.now()
    while (datetime.now() < then + timedelta(seconds=5)):
        pass
    for i in range(0, 10):
        reply_elem.send_keys(Keys.BACKSPACE)

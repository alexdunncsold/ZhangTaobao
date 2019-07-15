from selenium.webdriver.common.keys import Keys


def login_to_facebook(webdriver, credentials):
    print("Attempting to load https://www.facebook.com/ ...")
    webdriver.get("https://www.facebook.com/")
    if 'Facebook - Log In or Sign Up' in webdriver.title:
        print("Loaded Facebook login page!")
    else:
        raise RuntimeError('login_to_facebook(): Failed to load page with title {}'.format('Facebook - Log In or Sign Up'))

    #todo check if logged in already

    email_elem = webdriver.find_element_by_id('email')
    email_elem.clear()
    email_elem.send_keys(credentials.email)

    password_elem = webdriver.find_element_by_id('pass')
    password_elem.clear()
    password_elem.send_keys(credentials.password)

    print("Logging in...")
    password_elem.send_keys(Keys.RETURN)


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


def make_bid(webdriver, bid_amount):
    print('Preparing to bid {}'.format(bid_amount))
    all_comments_elem = webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")
    reply_elem.send_keys(str(bid_amount))
    print('Submitting bid of {}'.format(bid_amount))
    reply_elem.send_keys(Keys.RETURN)
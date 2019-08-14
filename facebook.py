from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
from pytz import utc
from time import sleep
import os


def continue_security_process(webdriver):
    continue_button = webdriver.find_elements_by_id('checkpointSubmitButton')
    if continue_button:
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(continue_button[0], 5, 5).click().perform()
        sleep(3)
    else:
        print("Failed to select a security continue button...")


def process_facebook_security_check(webdriver):
    print('Security check activated!')
    print('You have ten seconds to approve this login...')

    continue_security_process(webdriver)

    external_approval_button = webdriver.find_elements_by_id('u_3_1')
    if external_approval_button:
        action = ActionChains(webdriver)
        action.move_to_element_with_offset(external_approval_button[0], 2, 2).click().perform()
        sleep(0.1)
    else:
        print('Failed to select external-approval radio button.')

    continue_security_process(webdriver)
    continue_security_process(webdriver)
    continue_security_process(webdriver)


def login_with(webdriver, user):
    print("    Attempting to load https://www.facebook.com/ ...")
    webdriver.get("https://www.facebook.com/")
    if 'facebook' in webdriver.title.lower() \
            and 'log in or sign up' in webdriver.title.lower():
        print("    Loaded Facebook login page!")

        email_elem = webdriver.find_element_by_id('email')
        email_elem.clear()
        email_elem.send_keys(user.email)

        password_elem = webdriver.find_element_by_id('pass')
        password_elem.clear()
        password_elem.send_keys(user.password)

        print("Logging in...")
        password_elem.send_keys(Keys.RETURN)

    elif 'facebook' in webdriver.title.lower():
        print("    Already logged in.")
    else:
        raise RuntimeError('login_to_facebook(): Failed to load www.facebook.com')

    if webdriver.find_elements_by_id('checkpointSubmitButton'):
        process_facebook_security_check(webdriver)


def get_facebook_id(webdriver, **kwargs):
    id = \
        webdriver.find_element_by_class_name('_606w').get_attribute('href').split('https://www.facebook.com/')[1]
    if 'dev' in kwargs and kwargs.get('dev') == True:
        id += '/dev'
    return id


def get_auction_name(webdriver):
    try:
        item_name = webdriver.find_element_by_class_name('_l53').text
    except NoSuchElementException:
        item_name = 'NoNameFound'
    return item_name


def load_auction_page(webdriver, group, post):
    url = f'https://www.facebook.com/groups/{group.id}/permalink/{post.id}/'
    print(f'Attempting to load {url}')
    webdriver.get(url)
    if group.name in webdriver.title:
        print('    Loaded auction page!')
    else:
        raise RuntimeError(f'load_auction_page(): Failed to load page with title {group.name}')


def get_comments(webdriver):
    return webdriver.find_elements_by_class_name('_6qw3')


def get_comment_author(comment):
    comment_author_elem = comment.find_element_by_class_name('_6qw4')
    comment_author = comment_author_elem.get_attribute('href').split('https://www.facebook.com/')[1]
    return comment_author


def get_comment_text(comment):
    try:
        comment_text_elem = comment.find_element_by_class_name('_3l3x')
        comment_text = comment_text_elem.text
    except Exception as err:
        comment_text = ''
    return comment_text


def remove_all_child_comments(webdriver):
    child_comment_removal_script = '''
                elements = document.getElementsByClassName("_2h2j");
                for (let e of elements) {e.innerHTML='';};
            '''
    webdriver.execute_script(child_comment_removal_script)


def post_comment(webdriver, content):
    all_comments_elem = webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")

    reply_elem.send_keys(content)
    reply_elem.send_keys(Keys.RETURN)


def get_last_comment_registered_at(webdriver):
    # refresh page to ensure that correct timestamp is loaded in DOM
    webdriver.get(webdriver.current_url)
    timestamp_element = webdriver.find_elements_by_class_name('livetimestamp')[-1]
    timestamp_str = timestamp_element.get_attribute('data-utime')
    post_registered = datetime.utcfromtimestamp(int(timestamp_str)).replace(tzinfo=utc)

    return post_registered


def take_screenshot(webdriver):
    now = datetime.now()
    BASE_DIR = os.getcwd()
    SCREENSHOTS_FOLDER = os.path.join(BASE_DIR, 'screenshots')
    webdriver.save_screenshot(os.path.join(f'{SCREENSHOTS_FOLDER}{now.timestamp()}.png'))
    print('    Screenshot saved!')

from selenium.webdriver.common.keys import Keys

def login_to_facebook(driver, email, password):
    driver.get("https://www.facebook.com/")
    assert 'Facebook - Log In or Sign Up' in driver.title

    email_elem = driver.find_element_by_id('email')
    email_elem.clear()
    email_elem.send_keys(email)

    password_elem = driver.find_element_by_id('pass')
    password_elem.clear()
    password_elem.send_keys(password)

    password_elem.send_keys(Keys.RETURN)


def remove_all_child_comments(webdriver):
    child_comment_removal_script = '''
                elements = document.getElementsByClassName("_2h2j");
                for (let e of elements) {e.innerHTML='';};
            '''
    webdriver.execute_script(child_comment_removal_script)


def make_bid(browser_driver, bid_amount):
    all_comments_elem = browser_driver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
    comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
    comment_form.click()
    reply_elem = comment_form.find_element_by_class_name("_5rpu")
    reply_elem.send_keys(str(bid_amount))
    reply_elem.send_keys(Keys.RETURN)
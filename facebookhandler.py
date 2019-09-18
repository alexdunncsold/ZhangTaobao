from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime
from pytz import utc
from time import sleep


class FacebookHandler:
    def __init__(self, webdriver):
        self.webdriver = webdriver

    def continue_security_process(self):
        continue_button = self.webdriver.find_elements_by_id('checkpointSubmitButton')
        if continue_button:
            action = ActionChains(self.webdriver)
            action.move_to_element_with_offset(continue_button[0], 5, 5).click().perform()
            sleep(3)
        else:
            print("Failed to select a security continue button...")

    def process_facebook_security_check(self):
        print('Security check activated!')
        print('You have ten seconds to approve this login...')

        self.continue_security_process()

        external_approval_button = self.webdriver.find_elements_by_id('u_3_1')
        if external_approval_button:
            action = ActionChains(self.webdriver)
            action.move_to_element_with_offset(external_approval_button[0], 2, 2).click().perform()
            sleep(0.1)
        else:
            print('Failed to select external-approval radio button.')

        self.continue_security_process()
        self.continue_security_process()
        self.continue_security_process()

    def login_with(self, user):
        print("    Attempting to load https://www.facebook.com/ ...")
        self.webdriver.get("https://www.facebook.com/")
        if 'facebook' in self.webdriver.title.lower() \
                and 'log in or sign up' in self.webdriver.title.lower():
            print("    Loaded Facebook login page!")

            email_elem = self.webdriver.find_element_by_id('email')
            email_elem.clear()
            email_elem.send_keys(user.email)

            password_elem = self.webdriver.find_element_by_id('pass')
            password_elem.clear()
            password_elem.send_keys(user.password)

            print("Logging in...")
            password_elem.send_keys(Keys.RETURN)

        elif 'facebook' in self.webdriver.title.lower():
            print("    Already logged in.")
        else:
            raise RuntimeError('login_to_facebook(): Failed to load www.facebook.com')

        if self.webdriver.find_elements_by_id('checkpointSubmitButton'):
            self.process_facebook_security_check()

    def get_facebook_id(self, **kwargs):
        facebook_id = \
            self.webdriver.find_element_by_class_name('_606w').get_attribute('href') \
                .split('https://www.facebook.com/')[1]
        if 'dev' in kwargs and kwargs.get('dev'):
            facebook_id += '/dev'
        return facebook_id

    def get_auction_name(self):
        try:
            item_name = self.webdriver.find_element_by_class_name('_l53').text
        except NoSuchElementException:
            item_name = 'NoNameFound'
        return item_name

    def load_auction_page(self, group, post):
        url = f'https://www.facebook.com/groups/{group.id}/permalink/{post.id}/'
        print(f'Attempting to load {url}')
        self.webdriver.get(url)
        if group.name in self.webdriver.title:
            print('    Loaded auction page!')
        else:
            raise RuntimeError(f'load_auction_page(): Failed to load page with title {group.name}')

    def get_comments(self):
        comments_container = self.get_comments_container()
        return comments_container.find_elements_by_class_name('_42ef')

    def get_comments_container(self):
        try:
            return self.webdriver.find_element_by_class_name('_7791')
        except NoSuchElementException:
            try:
                return self.webdriver.find_element_by_class_name('_4eez')
            except NoSuchElementException:
                raise RuntimeError('get_comments_container(): Failed to find container element ._7791 or ._4eez')

    def remove_all_child_comments(self):
        child_comment_removal_script = '''
                    elements = document.getElementsByClassName("_2h2j");
                    for (let e of elements) {e.innerHTML='';};
                '''
        self.webdriver.execute_script(child_comment_removal_script)

    # Posts a fb comment on the current page, returning the system post-submission time
    def post_comment(self, content):
        all_comments_elem = self.webdriver.find_element_by_css_selector('[data-testid="UFI2CommentsList/root_depth_0"]')
        comment_form = all_comments_elem.find_elements_by_tag_name("form")[-1]
        comment_form.click()
        reply_elem = comment_form.find_element_by_class_name("_5rpu")

        reply_elem.send_keys(content)
        submission_time = datetime.utcnow().replace(tzinfo=utc)
        reply_elem.send_keys(Keys.RETURN)

        return submission_time

    def check_for_antispam_measures(self):
        sleep(0.5)
        if self.webdriver.find_elements_by_class_name('_4t2a'):
            raise SystemError('Fatal error: Facebook spam-detection filter activated!')

    def get_last_comment_registered_at(self):
        # refresh page to ensure that correct timestamp is loaded in DOM
        self.webdriver.get(self.webdriver.current_url)
        timestamp_element = self.webdriver.find_elements_by_class_name('livetimestamp')[-1]
        timestamp_str = timestamp_element.get_attribute('data-utime')
        post_registered = datetime.utcfromtimestamp(int(timestamp_str)).replace(tzinfo=utc)

        return post_registered

    def delete_last_comment(self):
        url = self.webdriver.current_url
        try:
            el = self.webdriver.find_elements_by_class_name('_2f3a')
            action = ActionChains(self.webdriver)
            action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys('d').send_keys(Keys.ENTER).send_keys(
                Keys.ENTER).perform()
            sleep(0.5)  # todo use implicit wait

            el = self.webdriver.find_elements_by_class_name('_4jy0')
            action = ActionChains(self.webdriver)
            action.move_to_element_with_offset(el[-1], 2, 2).click().send_keys(Keys.ENTER).perform()
        except IndexError:
            print('Attempted to delete comment: No comment exists')

        self.webdriver.get(url)

    @staticmethod
    def get_comment_author(comment):
        author_elem = comment.find_element_by_class_name('_6qw4')
        author = author_elem.get_attribute('href').split('/')[-1]
        return author

    @staticmethod
    def get_comment_text(comment):
        try:
            text_elem = comment.find_element_by_class_name('_3l3x')
            text = text_elem.text
        except Exception:
            text = ''
        return text

    @staticmethod
    def get_comment_timestamp(comment):
        timestamp_elem = comment.find_element_by_class_name('livetimestamp')
        timestamp = timestamp_elem.get_attribute('data-utime')
        timestamp_dt = FacebookHandler.dt_from(timestamp)
        return timestamp_dt

    @staticmethod
    def dt_from(fb_timestamp):
        return datetime.utcfromtimestamp(int(fb_timestamp)).replace(tzinfo=utc)

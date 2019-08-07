from facebookinteractions import establish_persistent_facebook_login
from secrets import *
from webdriverhelper import get_webdriver

driver = get_webdriver()
establish_persistent_facebook_login(driver, MY_FB_EMAIL_ADDRESS, MY_FB_PASSWORD)

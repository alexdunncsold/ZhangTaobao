from sys import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_webdriver():
    print('Platform identified as {}.  Instantiating driver...'.format(platform))
    options = Options()
    if platform == 'win32':
        options.add_argument('--disable-notifications')
    elif platform == 'linux':
        options = Options()
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        options.add_argument('--remote-debugging-port=9222')
    else:
        raise RuntimeError('Error while setting webdriver options: platform {} not supported.'.format(platform))
    driver = webdriver.Chrome(options=options)
    print('Driver instantiated.')
    return driver

from sys import platform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_webdriver(user_id):
    print('Platform identified as {}.  Instantiating driver...'.format(platform))
    options = Options()
    if platform == 'win32':
        options.add_argument('--disable-notifications')
        options.add_argument(f'--user-data-dir={user_id}/chrome-data')
    elif platform == 'linux':
        options = Options()
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument(f'--user-data-dir=/home/centos/pythonprogs/PuerBattlefield/{user_id}/chrome-data')
    else:
        raise RuntimeError('Error while setting webdriver options: platform {} not supported.'.format(platform))
    driver = webdriver.Chrome(options=options)

    # Set big screen size for screencap of history
    if platform == 'linux':
        driver.set_window_size(1000, 3000)

    print('Driver instantiated.')
    return driver

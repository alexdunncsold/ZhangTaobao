import configparser
from pytz import timezone


class User:
    def __init__(self, nickname):
        user_config = configparser.ConfigParser()
        user_config.read('account_config.ini')
        self.id = user_config[nickname]['Id']
        self.email = user_config[nickname]['Email']
        self.password = user_config[nickname]['Password']
        self.tz = timezone(user_config[nickname]['Timezone'])

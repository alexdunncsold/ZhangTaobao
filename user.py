import configparser


class User:
    def __init__(self, nickname):
        user_config = configparser.ConfigParser()
        user_config.read('account_config.ini')
        self.id = user_config[nickname]['id']
        self.email = user_config[nickname]['email']
        self.password = user_config[nickname]['password']

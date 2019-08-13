import configparser


class Auction:
    name = None

    def __init__(self, mode):
        config = configparser.ConfigParser()

        if mode == 'dev' or mode == 'test':
            config.read('test_config.ini')
        elif mode == 'live':
            config.read('live_config.ini')
        else:
            raise ValueError(f'Invalid mode "{mode}" specified')

        self.id = config['Auction']['AuctionId']

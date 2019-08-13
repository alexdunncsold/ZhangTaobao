import configparser
from datetime import datetime, timedelta
from pytz import utc, timezone


class ConstraintSet:
    def __init__(self, mode):
        config = configparser.ConfigParser()
        group_config = configparser.ConfigParser()
        group_config.read('group_config.ini')

        if mode == 'dev' or mode == 'test':
            config.read('test_config.ini')
            tz = timezone(group_config['dev']['Timezone'])
        elif mode == 'live':
            config.read('live_config.ini')
            tz = timezone(group_config['DEFAULT']['Timezone'])
        else:
            raise ValueError(f'Invalid mode "{mode}" specified')

        if config['Constraints']['Expiry'] == 'generateShort':
            self.expiry = self.get_short_expiry()
        else:
            self.expiry = self.parse_auction_datetime(config['Constraints']['Expiry'], tz)
        self.extensions = int(config['Constraints']['Extensions'])
        self.make_initial_bid = True if config['Constraints']['MakeInitialBid'] == 'True' else False
        self.minimum_bids = int(config['Constraints']['MinimumBids'])
        self.starting_bid = int(config['Constraints']['StartingBid'])
        self.bid_step = int(config['Constraints']['BidStep'])
        self.max_bid = int(config['Constraints']['MaxBid'])

    def parse_auction_datetime(self, dt_string, tz):
        # input must be in YYYY/MM/DD hh:mm or YYYY/MM/DD hh:mm:ss format
        date_parts = dt_string.split(' ')[0].split('/')
        time_parts = dt_string.split(' ')[1].split(':')

        seconds_provided = True if len(time_parts) == 3 else False

        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        hour = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = int(time_parts[2]) if seconds_provided else 0

        if seconds_provided and seconds != 59:
            raise ValueError('Seconds provided with a value other than 59')

        expiry_dt = tz.localize(datetime(year, month, day, hour, minutes, 0) + timedelta(minutes=1))
        return expiry_dt

    # Returns an auction expiry ending at XX:XX:00.000000
    def get_short_expiry(self):
        t = datetime.utcnow().replace(tzinfo=utc)
        t += timedelta(minutes=1) if t.second < 30 else timedelta(minutes=2)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

import configparser
from datetime import datetime, timedelta
from pytz import utc, timezone


class ConstraintSet:
    def __init__(self, auction_config_section):
        config = configparser.ConfigParser()
        group_config = configparser.ConfigParser()
        group_config.read('group_config.ini')

        if auction_config_section['GroupNickname'] == 'dev':
            tz = timezone(group_config['dev']['Timezone'])
        else:
            tz = timezone(group_config['DEFAULT']['Timezone'])  # timezone needs to be pulled from group

        if auction_config_section['Expiry'] == 'generateShort':
            self.expiry = self.get_short_expiry()
        elif auction_config_section['Expiry'] == 'generateMedium':
            self.expiry = self.get_medium_expiry()
        elif auction_config_section['Expiry'] == 'generateLong':
            self.expiry = self.get_long_expiry()
        else:
            self.expiry = self.parse_auction_datetime(auction_config_section['Expiry'], tz)
        self.extensions = int(auction_config_section['Extensions'])
        self.make_initial_bid = True if auction_config_section['MakeInitialBid'] == 'True' else False
        self.minimum_bids = int(auction_config_section['MinimumBids'])
        self.starting_bid = int(auction_config_section['StartingBid'])
        self.min_bid_step = int(auction_config_section['BidStep'])
        self.max_bid = int(auction_config_section['MaxBid'])

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
        t += timedelta(minutes=1) if t.second < 15 else timedelta(minutes=2)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

    # Returns an auction expiry in approx. 2min, ending at XX:XX:00.000000
    def get_medium_expiry(self):
        t = datetime.utcnow().replace(tzinfo=utc)
        t += timedelta(minutes=2) if t.second < 15 else timedelta(minutes=3)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

    # Returns an auction expiry in approx. 3min, ending at XX:XX:00.000000
    def get_long_expiry(self):
        t = datetime.utcnow().replace(tzinfo=utc)
        t += timedelta(minutes=3) if t.second < 15 else timedelta(minutes=4)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

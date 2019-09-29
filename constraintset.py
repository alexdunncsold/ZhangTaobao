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

        constraints_dict = auction_config_section  # todo replace refs to conDict woth acs

        if constraints_dict['Expiry'] == 'generateShort':
            self.expiry = self.get_short_expiry()
        elif constraints_dict['Expiry'] == 'generateMedium':
            self.expiry = self.get_medium_expiry()
        elif constraints_dict['Expiry'] == 'generateLong':
            self.expiry = self.get_long_expiry()
        else:
            self.expiry = self.parse_auction_datetime(constraints_dict['Expiry'], tz)

        try:
            self.extensions = int(constraints_dict['Extensions'])
        except KeyError:
            self.extensions = 0

        try:
            self.starting_bid = int(constraints_dict['StartingBid'])
        except:
            self.starting_bid = 1

        try:
            self.min_bid_step = int(constraints_dict['BidStep'])
        except:
            self.min_bid_step = 100

        try:
            self.max_bid = int(constraints_dict['MaxBid'])
        except KeyError:
            print(f'NO MAXIMUM BID GIVEN - DEFAULTING TO WATCHING ONLY')
            self.max_bid = 0

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

    # Returns an auction expiry in approx. 3min, ending at XX:XX:00.000000
    def get_medium_expiry(self):
        t = datetime.utcnow().replace(tzinfo=utc)
        t += timedelta(minutes=3) if t.second < 15 else timedelta(minutes=4)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

    # Returns an auction expiry in approx. 5min, ending at XX:XX:00.000000
    def get_long_expiry(self):
        t = datetime.utcnow().replace(tzinfo=utc)
        t += timedelta(minutes=5) if t.second < 15 else timedelta(minutes=6)
        return datetime(t.year, t.month, t.day, t.hour, t.minute, 0, 0, tzinfo=utc)

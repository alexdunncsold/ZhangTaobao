from datetime import timedelta


class CountdownTimer:
    countdown_complete = False

    def __init__(self, time_handler, countdown_seconds_notifications = (1, 2, 3, 4, 5, 10, 30)):
        self.time_handler = time_handler
        self.countdown_seconds_notifications_init = countdown_seconds_notifications
        self.countdown_seconds_notifications = list(self.countdown_seconds_notifications_init)

    def proc(self):
        try:
            if self.time_handler.get_time_remaining() >= timedelta(minutes=1):
                raise ValueError

            if not self.time_handler.auction_expired() \
                    and self.time_handler.get_time_remaining() < timedelta(seconds=self.countdown_seconds_notifications[-1]):
                print(f'{str(self.countdown_seconds_notifications.pop()).rjust(10)} seconds remaining!')
            elif self.time_handler.auction_expired() and not self.countdown_complete:
                self.countdown_complete = True
                print(f'Auction Complete! at {self.time_handler.get_current_time().strftime("%Y-%m-%d %H:%M:%S")}')
        except IndexError:
            pass
        except ValueError:
            pass

    def reset(self):
        self.countdown_seconds_notifications = list(self.countdown_seconds_notifications_init)

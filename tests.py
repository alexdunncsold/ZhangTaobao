from datetime import datetime, timedelta
import facebookhandler as fb
import math
from pytz import utc
import statistics

from supervisor import Supervisor


class TestSupervisor(Supervisor):
    def __init__(self, prevent_shutdown=False):
        super().__init__('alex', dev=True, archive=False, prevent_shutdown=prevent_shutdown)

    def test_maximal_delay(self, trial_sets, trials):
        max_mean_delta_results = []

        for trial_set in range(0, trial_sets):
            try:
                delay_results = []

                for trial in range(0, trials):
                    delay_results.append(self.fbclock.timedelta_to_ms(self.fbclock.get_posting_delay_datum()))
                    print(f'{delay_results[-1]}ms')

                delay_mean = statistics.mean(delay_results)
                delay_min = min(delay_results)
                delay_max = max(delay_results)

                max_mean_delta = delay_max - delay_mean
                max_mean_delta_results.append(max_mean_delta)

                print(f'Delay ave={delay_mean}ms, min={delay_min}ms, max={delay_max}')
            except Exception as err:
                self.webdriver.quit()
                raise err

        delta_mean = statistics.mean(max_mean_delta_results)
        delta_max = max(max_mean_delta_results)

        print(f'Delay delta ave={delta_mean}ms, max={delta_max}')

    def passes_safety_test(self):
        self.constraints.expiry = datetime.utcnow().replace(tzinfo=utc) + timedelta(minutes=1)
        self.constraints.expiry -= timedelta(microseconds=self.constraints.expiry.microsecond)
        print(f'New expiry: {self.constraints.expiry}')

        self.perform_main_loop()
        print(f'Result: {"success" if self.auction_won() else "failure"}')

        return self.auction_won()


def test():
    validate_safety_margin(90)


def validate_safety_margin(test_duration_minutes):
    end_time = datetime.now() + timedelta(minutes=test_duration_minutes)

    trials = 0
    failures = 0
    delay_safety_buffer_ms = None
    successive_maximal_delays = []
    deviations_from_last_second = []
    try:
        while datetime.now() < end_time:
            supervisor = TestSupervisor()
            supervisor.perform_main_loop()

            successive_maximal_delays.append(supervisor.fbclock.maximal_delay.total_seconds() * 1000)

            try:
                deviations_from_last_second.append(supervisor.valid_bid_history[-1].timestamp.second - 59)
            except IndexError:
                deviations_from_last_second.append('???')

            if not delay_safety_buffer_ms:
                delay_safety_buffer_ms = supervisor.fbclock.maximal_delay_safety_buffer.total_seconds() * 1000

            trials += 1
            if not supervisor.auction_won():
                failures += 1
    except Exception as err:
        # This may occur if facebook's spam detection prevents posting in sync or auction threads
        print(err.__repr__())

    print(f'\n{delay_safety_buffer_ms}ms delay buffer: {failures / (trials if trials else 1) * 100}% failure')
    print(f'Delays: {"ms, ".join(str(math.floor(delay)) for delay in successive_maximal_delays)}ms')
    print(f'Deviations: {", ".join(str(deviation) for deviation in deviations_from_last_second)}')


test()

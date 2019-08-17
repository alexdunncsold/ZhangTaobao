from datetime import datetime, timedelta
import facebookhandler as fb
import math
from pytz import utc
import statistics

from supervisor import Supervisor


class TestSupervisor(Supervisor):
    def __init__(self):
        super().__init__('dev')

    def init_selenium(self):
        fb.login_with(self.webdriver, self.user)

    def test_maximal_delay(self, trial_sets, trials):
        max_mean_delta_results = []

        for trial_set in range(0, trial_sets):
            try:
                delay_results = []

                for trial in range(0, trials):
                    delay_results.append(self.sync.timedelta_to_ms(self.sync.get_posting_delay_datum(self.webdriver)))
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

        print(f'Delta ave={delta_mean}ms, max={delta_max}')

    # def run_safety_tests(self, trials_per_test):
    #     results = []
    #
    #     for safety_delay in range(200, 600, 100):
    #         failures = self.run_safety_test(safety_delay, trials_per_test)
    #         results.append({'delay':safety_delay, 'failures':failures})
    #
    #     for result in results:
    #         print(f'{result["delay"]}ms delay: {result["failures"]/trials_per_test*100}% failure')
    #
    # def run_safety_test(self, delay, trials):
    #     tests_complete = 0
    #     failures = 0
    #
    #     self.safety_margin = timedelta(milliseconds=delay)
    #
    #     now = datetime.utcnow().replace(tzinfo=utc) + posting_delay

    # return failures


def test():
    supervisor = TestSupervisor()
    supervisor.test_maximal_delay(1, 10)
    supervisor.webdriver.quit()
# login_to_facebook(driver, auction_context)
# posting_delay = get_offset(driver, auction_context)
# load_auction_page(driver, auction_context)
#
# bid_tests = 15
# tests_complete = 0
# failures = 0
#
# now = datetime.utcnow().replace(tzinfo=utc) + posting_delay
# while now < auction_context.auction.end_datetime:
#     # Bear in mind that passing this test isn't a guarantee that it will work in production.
#     # Test multiple times against a simulated auction
#     if now > auction_context.auction.end_datetime - timedelta(milliseconds=100):
#         print(f'Bidding at adjusted system time {now.strftime("%H:%M (%S.%fsec)")}')
#         make_bid(driver, auction_context, 500)
#
#         driver.get(driver.current_url)
#         post_registered = get_post_registered(driver)
#         if auction_context.auction.end_datetime.second - post_registered.second > post_registered.second:
#             spare_seconds = auction_context.auction.end_datetime - post_registered
#         else:
#             spare_seconds = 60 + auction_context.auction.end_datetime.second - post_registered.second
#
#         if post_registered < auction_context.auction.end_datetime:
#             print(f'    Passed with {spare_seconds} seconds to spare (1sec optimal)')
#         else:
#             failures += 1
#             print(f'    Failed to bid before auction expiry T_T')
#
#         tests_complete += 1
#         auction_context.auction.end_datetime = auction_context.auction.end_datetime + timedelta(minutes=1)
#
#         if tests_complete >= bid_tests:
#             print(f'Ran {tests_complete} tests - {failures} failed.')
#             break
#     now = datetime.utcnow().replace(tzinfo=utc) + posting_delay

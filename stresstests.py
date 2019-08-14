from datetime import datetime, timedelta
import facebook as fb
import math
from pytz import utc
import statistics

from supervisor import Supervisor


class SafetySupervisor(Supervisor):
    def __init__(self):
        super().__init__('dev')

    def init_selenium(self):
        fb.login_with(self.driver, self.user)

    def test_maximal_delay(self, trials):
        try:
            results = []
            for trial in range(0, trials):
                self.sync.init_maximal_delay(self.driver)
                results.append(
                    math.ceil(self.sync.maximal_delay.seconds * 1000 + self.sync.maximal_delay.microseconds / 1000))
                self.sync.maximal_delay = None
                print(f'{results[-1]}ms')

            print(f'Delay ave={statistics.mean(results)}ms, min={min(results)}ms, max={max(results)}')
        except Exception as err:
            self.driver.quit()
            raise err

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


def run_tests():
    supervisor = SafetySupervisor()
    supervisor.test_maximal_delay(10)
    supervisor.driver.quit()
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

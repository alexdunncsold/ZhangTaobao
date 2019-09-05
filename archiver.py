import os
from datetime import datetime


class Archiver:

    def __init__(self, webdriver):
        base_dir = os.getcwd()
        self.webdriver = webdriver
        self.id = str(datetime.now().timestamp())
        self.path = os.path.join(base_dir, 'archives', self.id)

        try:
            os.mkdir(self.path)
            print(f'Saving records in {self.path}')
        except Exception:
            print('Could not create directory for output.  Output will not be saved.')

    def save_final_state_html(self):
        try:
            with open(os.path.join(self.path, 'final_state.html'), 'wb+') as out:
                out.write(self.webdriver.page_source.encode('utf-8'))
                out.close()
        except Exception as err:
            print(f'Error writing final-state html: {err.__repr__()}')

    def take_screenshot(self):
        try:
            self.webdriver.save_screenshot(os.path.join(self.path, 'screenshot.png'))
            print('    Screenshot saved!')
        except Exception as err:
            print(f'Error taking screenshot: {err.__repr__()}')

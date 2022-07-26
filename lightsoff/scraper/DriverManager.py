import os
from seleniumwire import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class DriverManager:

    def __init__(self):

        print("Configuring chrome driver...")

        chrome_caps = DesiredCapabilities.CHROME
        chrome_caps['goog:loggingPrefs'] = {'performance': 'ALL'}
        chrome_caps['acceptSslCerts'] = True

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-insecure-localhost')
        chrome_options.add_argument('"--ssl-insecure"')


        if "SCRAPER_PROXY" in os.environ:
            print("Proxy enabled.")
            seleniumwire_options = {
                'proxy': {
                    'https': os.environ.get('SCRAPER_PROXY')
                }
            }
            driver = webdriver.Chrome(desired_capabilities=chrome_caps, options=chrome_options, seleniumwire_options=seleniumwire_options)
        else:
            print("Proxy disabled. Add SCRAPER_PROXY env var to enable it.")
            driver = webdriver.Chrome(desired_capabilities=chrome_caps, options=chrome_options)

        self.driver = driver

    def get_driver(self):
      return self.driver

    def print_request(self):
        for request in self.driver.requests:
            print(
                request.url,
                request.response.status_code,
                request.response.headers['Content-Type']
            )
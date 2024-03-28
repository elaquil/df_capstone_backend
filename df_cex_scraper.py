"""system_module."""
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import argparse
import re
import os
import requests

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("start-maximised")


options = webdriver.ChromeOptions()
options.add_experimental_option('detach', True)
options.add_experimental_option('excludeSwitches', ['enable-logging'])

parser = argparse.ArgumentParser()
parser.add_argument("-r", "--Root", help = "Select root link to start crawling from")
parser.add_argument("-d", "--Docker", help = "Run in container mode")

parser.parse_args()
args = parser.parse_args()
if args.Root:
    print(f'Root link specified as: {args.Root}')
    crawlLink = args.Root
else:
    crawlLink = 'https://uk.webuy.com/search?stext=iphone%207%20plus'
    print(f'No root link specified, defaulting to: {crawlLink}')
if args.Docker:
    print(f'Running in container mode')
    service = Service(executable_path='/usr/bin/chromedriver')

print("App Started")

class Crawler:
    """
    This class is used to gather Iphone price data.
    """

    def __init__(self):
        """
        See help(Crawler) for accurate signature
        """
        if args.Docker:
            self.driver = webdriver.Chrome(options=chrome_options, service=service)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(150)
        self.url = crawlLink
        self.phones_names_list = []
        self.phones_price_list = []
        self.url_list = []
        self.spec_list = []
        self.price_list = []
        self.image_url = ''
        self.api_get = 'https://buw5pcb475.execute-api.us-east-1.amazonaws.com/production/phone?phoneid='
        self.api_post = 'https://buw5pcb475.execute-api.us-east-1.amazonaws.com/production/phone'

    def load_and_accept_cookies(self) -> webdriver.Chrome:
        """
        Accept the cookies prompt.
        """
        self.url = crawlLink
        self.driver.get(self.url)
        accept_cookies_button = self.driver.find_element(By.XPATH,
        value='//*[@id="onetrust-accept-btn-handler"]')
        accept_cookies_button.click()
        time.sleep(1)
    
    def select_iphone(self):
        """
        Find the tick box responsible for showing only phone results. 
        """
        select_iphone = self.driver.find_element(By.XPATH,
        value='//*[@id="main"]/div/div/div[1]/div[2]/div/div[3]/div[1]/div/div[3]/div[3]/div/div/div/ul/li[1]/label/span[1]')
        select_iphone.click()
        time.sleep(2)
    
    def get_all_phone_url(self):
        previous_url = ''
        while (True):
            if self.driver.current_url != previous_url:
                print(previous_url)
                previous_url = self.driver.current_url
                self.append_all_url_to_list()
                next_page = self.driver.find_element(By.CSS_SELECTOR, '[aria-label="Next"]')
                next_page.click()
                time.sleep(2)
            else:
                print('HERE')
                break

        # self.append_all_url_to_list()
        # next_page = self.driver.find_element(By.CSS_SELECTOR, '[aria-label="Next"]')
        # next_page.click()
        # time.sleep(2)
    
    def append_all_url_to_list(self):
        parent = self.driver.find_elements(By.CSS_SELECTOR, value='a.line-clamp')
        for i in parent:
            self.url_list.append(i.get_attribute('href'))
    
    def go_into_page_and_out(self):
        """
        The option that allows access to the image class is only made available after going into
        a device link and coming back out.
        """
        
        for url in self.url_list:
            self.driver.execute_script("window.open('');") 
            self.driver.switch_to.window(self.driver.window_handles[1]) 
            self.driver.get(url)
            self.product_image()
            self.product_prices()
            self.product_spec()
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        time.sleep(5)
        print('DONE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        if not os.path.exists('data.json'):
            self.export_json()

    def product_spec(self):
        self.spec_list = []
        product_detail = self.driver.find_elements(By.CSS_SELECTOR, 'span[class="text-sm"]')
        for i in product_detail:
            self.spec_list.append(i.text)
        self.phone_name_and_condition()
    
    def product_prices(self):
        self.price_list = []
        prices = self.driver.find_elements(By.CSS_SELECTOR, 'div[class="d-flex flex-wrap w-100"]')
        for i in prices:
            price = i.text
            self.price_list.append(price)
        self.price_list = re.findall(r'\d+\.\d+', self.price_list[0])
        self.price_list = [float(num) for num in self.price_list]
    
    def product_image(self):
        self.image_url = ''
        image = self.driver.find_element(By.XPATH, '//*[@id="main"]/div/div/div[1]/div[1]/div[1]/div/div[2]/img')
        self.image_url = image.get_attribute('src')
    
    def phone_name_and_condition(self):
        """
        Find all span tags and classes that correlate with the desired device names.
        """
        print(self.api_get + ''.join(string.replace(' ', '').lower() for string in self.spec_list))
        get_phone = str(self.api_get + ''.join(string.replace(' ', '').lower() for string in self.spec_list))
        if self.read_from_api(get_phone) == False:
            dict_phones = {'phoneid': (), 'manufacturer': (), 'phone_model': (), 'network': (),
                            'grade': (), 'capacity': (), 'phone_colour': (),
                            'main_colour': (), 'os': (), 'physical_sim_slots': (),
                            'time': [], 'price': [], 'trade-in_for_voucher': [],
                            'trade-in_for_cash': [], 'image_url': ()}
            
            dict_phones['phoneid'] = ''.join(string.replace(' ', '').lower() for string in self.spec_list)
            dict_phones['manufacturer'] = self.spec_list[0]
            dict_phones['phone_model'] = self.spec_list[1]
            dict_phones['network'] = self.spec_list[2]
            dict_phones['grade'] = self.spec_list[3]
            dict_phones['capacity'] = self.spec_list[4]
            dict_phones['phone_colour'] = self.spec_list[5]
            dict_phones['main_colour'] = self.spec_list[6]
            dict_phones['os'] = self.spec_list[7]
            dict_phones['physical_sim_slots'] = self.spec_list[8]
            dict_phones['time'].append(str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')))
            dict_phones['price'].append(str(self.price_list[0]))
            dict_phones['trade-in_for_voucher'].append(str(self.price_list[1]))
            dict_phones['trade-in_for_cash'].append(str(self.price_list[2]))
            dict_phones['image_url'] = self.image_url
            replace_quote = str(dict_phones).replace("'", '"')
            self.make_post_request(self.api_post, replace_quote)
        else:
            data = self.read_from_api(get_phone)
            data['price'].append(str(self.price_list[0]))
            data['trade-in_for_voucher'].append(str(self.price_list[1]))
            data['trade-in_for_cash'].append(str(self.price_list[2]))
            data['time'].append(str(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')))
            replace_quote = str(data).replace("'", '"')
            self.make_post_request(self.api_post, replace_quote)
    


    def read_from_api(self, url):
        try:
            # Make a GET request to the API
            response = requests.get(url)

            # Check if the response status code indicates success (2xx)
            if response.status_code // 100 == 2:
                # Check if the response content is null
                if response.content.strip() == b'null':
                    return False
                else:
                    return response.json()
            else:
                print("Error: Failed to fetch data from the API. Status code:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to the API:", e)
    
    def make_post_request(self, url, data):
        try:
            # Make the POST request with the provided data
            response = requests.post(url, data=data)

            # Check the response status code
            if response.status_code == 200:
                print("POST request successful.")
                return response.json()  # Assuming the response is JSON
            else:
                print("POST request failed. Status code:", response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            print("Error: Failed to connect to the API:", e)
            return None
    
if __name__ == '__main__':
    start_crawling = Crawler()
    start_crawling.load_and_accept_cookies()
    start_crawling.select_iphone()
    start_crawling.get_all_phone_url()
    start_crawling.go_into_page_and_out()

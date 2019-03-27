from time import sleep

import re
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from typing import List, Dict, Iterable
from urllib.parse import urlparse

from config import HEADLESS, YANDEX_PASSWORD, YANDEX_LOGIN
from log import selenium_logger as logger

AUTH_URL = "https://passport.yandex.ru/auth"
LOGIN_ID = "passp-field-login"
PASSWORD_ID = "passp-field-passwd"

PHONE_PATTERN = re.compile(r'^\+\d{11}$')
YANDEX_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fz'


def get_element(driver, xpath, delay):
    wait = WebDriverWait(driver, delay)
    return wait.until(ec.presence_of_element_located((By.XPATH, xpath)))


class SeleniumClient:
    BROWSER: webdriver.Chrome = None
    BUSY = False

    BASE_URL = "https://fleet.taxi.yandex.ru/"
    TAXOPARK_URL = "https://fleet.taxi.yandex.ru/map"
    DRIVERS_URL = BASE_URL + "drivers"

    BUSY_BUTTON_XPATH = '//span[text()[contains(., "Busy")]]'

    @classmethod
    def init(cls):
        logger.info("launching browser")
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--window-size=800,600")
        options.add_argument("--disable-gpu")
        options.headless = True if HEADLESS else False
        browser = webdriver.Chrome(options=options)

        browser.get(AUTH_URL)
        login_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, LOGIN_ID)))
        login_input.send_keys(YANDEX_LOGIN)
        login_input.submit()

        password_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, PASSWORD_ID)))
        password_input.send_keys(YANDEX_PASSWORD)
        password_input.submit()
        sleep(1)
        cls.BROWSER = browser

    @classmethod
    def launched(cls):
        try:
            return cls.BROWSER is not None and cls.BROWSER.current_url is not None
        except WebDriverException:
            return False

    @classmethod
    def get_all_drivers_info(cls) -> List[Dict]:
        try:
            return cls._get_all_drivers_info()
        except Exception as e:
            logger.exception(e)
            cls.BROWSER.refresh()
            return []

    @classmethod
    def _get_all_drivers_info(cls) -> List[Dict]:
        if not cls.launched():
            cls.init()

        while cls.BUSY:
            sleep(1)
        cls.BUSY = True

        p = urlparse(cls.BROWSER.current_url)
        if "{}://{}{}".format(p.scheme, p.netloc, p.path) != cls.DRIVERS_URL:
            cls.BROWSER.get(cls.DRIVERS_URL)
            sleep(5)

        selector = "tr.ant-table-row > td:nth-child({}) > a:nth-child(1)"
        names = cls.BROWSER.find_elements_by_css_selector(selector.format(3))
        phones = cls.BROWSER.find_elements_by_css_selector(selector.format(4))
        result = []
        for name_info, phone in zip(names, phones):
            surname, name, patronymic = name_info.text.split()
            result.append({
                "name": name,
                "surname": surname,
                "patronymic": patronymic,
                "phone": phone.text,
            })

        # TODO: доделать переход по пагинации
        cls.BUSY = False
        return result

    @classmethod
    def get_drivers_info_from_map(cls) -> Iterable[Dict]:
        try:
            yield from cls._get_drivers_info_from_map()
        except Exception as e:
            logger.exception(e)
            raise

    @classmethod
    def _get_drivers_info_from_map(cls) -> Iterable[Dict]:
        """
        Возвращает дикты с водителями, которые доступны во вьюхе /maps
        Этот метод удобен для сбора занятых водителей
        """
        if not cls.launched():
            cls.init()

        while cls.BUSY:
            sleep(1)
        cls.BUSY = True

        p = urlparse(cls.BROWSER.current_url)
        if "{}://{}{}".format(p.scheme, p.netloc, p.path) != cls.TAXOPARK_URL:
            cls.BROWSER.get(cls.TAXOPARK_URL)

        cls.BROWSER.refresh()

        free_user_list = cls.BROWSER.find_elements_by_class_name("user-item")
        for user_elem in free_user_list:
            yield cls._process_user(user_elem)

        busy_button = get_element(cls.BROWSER, cls.BUSY_BUTTON_XPATH, 5)
        sleep(1)
        busy_button.click()

        busy_user_list = cls.BROWSER.find_elements_by_class_name("user-item")
        for user_elem in busy_user_list:
            yield cls._process_user(user_elem)

        cls.BUSY = False

    @staticmethod
    def _process_user(user_elem):
        phone = user_elem.find_element_by_xpath('./a').get_attribute('href').lstrip('callto:')
        assert PHONE_PATTERN.fullmatch(phone), f"phone number {phone} doesn't match with pattern"

        name_string = user_elem.find_element_by_xpath('.//*[contains(@class, "fio")]').text
        surname, name, patronymic = name_string.split()

        status = user_elem.find_element_by_xpath('.//*[contains(@class, "status-text")]').text

        time_elem = user_elem.find_element_by_xpath('.//time').get_attribute('datetime')
        time = datetime.strptime(time_elem, YANDEX_DATE_FORMAT)

        return {
            "name": name,
            "surname": surname,
            "patronymic": patronymic,
            "phone": phone,
            "status": {
                "value": status,
                "set_at": time,
            },
        }

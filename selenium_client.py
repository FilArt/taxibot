from time import sleep

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from typing import List

from cache import Cache
from config import HEADLESS, YANDEX_PASSWORD, YANDEX_LOGIN, DRIVERS_INFO_CACHE
from driver import driver_status_factory, DriverInfo
from log import selenium_logger as logger

AUTH_URL = 'https://passport.yandex.ru/auth'
LOGIN_ID = 'passp-field-login'
PASSWORD_ID = 'passp-field-passwd'


class SeleniumClient:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if SeleniumClient.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            SeleniumClient.__instance = cls
            cls.init()

    BROWSER: webdriver = None
    LAUNCHED = False

    BASE_URL = 'https://fleet.taxi.yandex.ru/'
    TAXOPARK_URL = 'https://fleet.taxi.yandex.ru/map'
    DRIVERS_URL = BASE_URL + "drivers"

    BUSY_BUTTON_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[1]/div/div/div/button[2]'
    PHONE_TAGS_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[2]/div[2]/ul/div[{}]/div/a'

    USER_LIST_TAG = 'user-list'

    @classmethod
    def init(cls):
        logger.info('launching')
        options = Options()
        options.headless = True if HEADLESS else False
        browser = webdriver.Firefox(options=options)

        logger.info('authentication of webdriver')
        browser.get(AUTH_URL)
        login_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, LOGIN_ID)))
        login_input.send_keys(YANDEX_LOGIN)
        login_input.submit()

        password_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, PASSWORD_ID)))
        password_input.send_keys(YANDEX_PASSWORD)
        password_input.submit()
        cls.BROWSER = browser

    @classmethod
    def trigger(cls):
        cls.LAUNCHED = not cls.LAUNCHED

    def __init__(self):
        self._firefox = None

    def __del__(self):
        self.BROWSER.quit()

    @Cache.cached(DRIVERS_INFO_CACHE, logger=logger)
    def get_all_drivers_info(self) -> List[DriverInfo]:
        if self._firefox.current_url != self.DRIVERS_URL:
            self._firefox.get(self.DRIVERS_URL)

        selector = 'tr.ant-table-row > td:nth-child({}) > a:nth-child(1)'

        sleep(5)
        result = []
        names = self._firefox.find_elements_by_css_selector(selector.format(3))
        phones = self._firefox.find_elements_by_css_selector(selector.format(4))

        for name_info, phone in zip(names, phones):
            surname, name, patronymic = name_info.text.split()
            result.append(DriverInfo(name=name, surname=surname, patronymic=patronymic, phone=phone.text, status=None))

        # TODO: доделать переход по пагинации
        return result

    @classmethod
    def get_drivers_from_map(cls) -> List[DriverInfo]:
        """
        Возвращает дикты с водителями, которые доступны во вьюхе /maps
        Этот метод удобен для сбора занятых водителей
        """
        logger.info('getting drivers from map')

        if not cls.BROWSER.current_url == cls.TAXOPARK_URL:
            cls.BROWSER.get(cls.TAXOPARK_URL)
            sleep(1)

        cls.BROWSER.find_element_by_xpath(cls.BUSY_BUTTON_XPATH).click()

        user_list_tag = cls.BROWSER.find_element_by_class_name(cls.USER_LIST_TAG)
        user_list = user_list_tag.text.split('\n')

        logger.info('fetching drivers info from map')
        now = datetime.now()
        drivers_info_dicts = []
        for i in range(0, len(user_list), 4):
            chunk = tuple(user_list[i:i+4][1:])
            fullname, status, minutes = chunk
            minutes = int(minutes.split()[0])
            name, surname, patronymic = fullname.split()
            logger.info('adding user %s', surname)
            driver_status = driver_status_factory(status, minutes, now)
            drivers_info_dicts.append(dict(
                name=name,
                surname=surname,
                patronymic=patronymic,
                status=driver_status,
            ))

        logger.info('adding phone numbers')
        for i in range(1, len(drivers_info_dicts) + 1):
            selector = cls.PHONE_TAGS_XPATH.format(i)
            phone_tag = cls.BROWSER.find_element_by_xpath(selector)
            href = phone_tag.get_attribute('href')
            phone = href.split(':')[1]
            drivers_info_dicts[i - 1]['phone'] = phone

        return [
            DriverInfo(name=d['name'], surname=d['surname'], patronymic=d['patronymic'],
                       phone=d['phone'], status=d['status'])
            for d in drivers_info_dicts
        ]

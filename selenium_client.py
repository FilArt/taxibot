from time import sleep

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from typing import List

from config import HEADLESS
from driver import driver_info_factory, driver_status_factory
from log import selenium_logger as logger
from payload import Payload


class SeleniumClient:
    BROWSER = None
    AUTHORISED = False
    LAUNCHED = False
    BASE_URL = 'https://fleet.taxi.yandex.ru/'
    AUTH_URL = 'https://passport.yandex.ru/auth'
    TAXOPARK_URL = 'https://fleet.taxi.yandex.ru/map'
    DRIVERS_URL = BASE_URL + "drivers"

    LOGIN_ID = 'passp-field-login'
    PASSWORD_ID = 'passp-field-passwd'

    BUSY_BUTTON_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[1]/div/div/div/button[2]'
    PHONE_TAGS_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[2]/div[2]/ul/div[{}]/div/a'

    USER_LIST_TAG = 'user-list'

    login = None
    password = None

    @classmethod
    def trigger(cls):
        cls.LAUNCHED = not cls.LAUNCHED

    def __init__(self, login, password):
        SeleniumClient.login = login
        SeleniumClient.password = password

        self._firefox = None
        self._user_list_tag = None
        self._phone_list_selector = None
        self._busy_button_pressed = False

    def __enter__(self):
        """
        Возвращает авторизованный драйвер
        """
        while SeleniumClient.LAUNCHED:
            sleep(1)
        SeleniumClient.trigger()
        logger.info('launching')

        if not SeleniumClient.BROWSER:
            options = Options()
            options.headless = True if HEADLESS else False
            SeleniumClient.BROWSER = webdriver.Firefox(options=options)
            SeleniumClient.BROWSER.get(self.AUTH_URL)
            SeleniumClient._submit_login()
            SeleniumClient._submit_password()
            SeleniumClient.AUTHORISED = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            logger.exception(exc_val)
        # self._user_list_tag = None
        # self._phone_list_selector = None
        # self._busy_button_pressed = False
        # self._firefox.quit()
        SeleniumClient.trigger()

    def get_all_drivers_info(self) -> List[driver_info_factory]:
        if self._firefox.current_url != self.DRIVERS_URL:
            self._firefox.get(self.DRIVERS_URL)

        selector = 'tr.ant-table-row > td:nth-child({}) > a:nth-child(1)'

        sleep(5)
        result = []
        names = self._firefox.find_elements_by_css_selector(selector.format(3))
        phones = self._firefox.find_elements_by_css_selector(selector.format(4))

        for name_info, phone in zip(names, phones):
            surname, name, patronymic = name_info.text.split()
            result.append(driver_info_factory(name=name, surname=surname, patronymic=patronymic, phone=phone.text,
                                              status=None))

        # TODO: доделать переход по пагинации
        return result

    @classmethod
    def get_drivers_from_map(self) -> List[driver_info_factory]:
        """
        Возвращает дикты с водителями, которые доступны во вьюхе /maps
        Этот метод удобен для сбора занятых водителей
        """
        logger.info('getting drivers from map')

        if not self.BROWSER.current_url == self.TAXOPARK_URL:
            self.BROWSER.get(self.TAXOPARK_URL)

        if not self._busy_button_pressed:
            sleep(1)
            self.BROWSER.find_element_by_xpath(self.BUSY_BUTTON_XPATH).click()
            self._busy_button_pressed = True

        if self._user_list_tag:
            user_list_tag = self._user_list_tag
        else:
            user_list_tag = self.BROWSER.find_element_by_class_name(self.USER_LIST_TAG)
            self._user_list_tag = user_list_tag

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
            selector = self.PHONE_TAGS_XPATH.format(i)
            phone_tag = self.BROWSER.find_element_by_xpath(selector)
            href = phone_tag.get_attribute('href')
            phone = href.split(':')[1]
            drivers_info_dicts[i - 1]['phone'] = phone

        return [driver_info_factory(name=d['name'], surname=d['surname'], patronymic=d['patronymic'], phone=d['phone'],
                                    status=d['status']) for d in drivers_info_dicts]

    @classmethod
    def _submit_login(cls):
        logger.info('login')
        login_input = WebDriverWait(cls.BROWSER, 10).until(
            ec.presence_of_element_located((By.ID, cls.LOGIN_ID))
        )
        login_input.send_keys(cls.login)
        sleep(1)
        login_input.submit()
        sleep(1)

    @classmethod
    def _submit_password(cls):
        password_input = WebDriverWait(cls.BROWSER, 10).until(
            ec.presence_of_element_located((By.ID, cls.PASSWORD_ID)))
        password_input.send_keys(cls.password)
        sleep(1)
        password_input.submit()
        sleep(1)

from time import sleep

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from config import DEBUG, TIME_FORMAT, HEADLESS
from log import selenium_logger as logger


class SeleniumClient:
    BASE_URL = 'https://fleet.taxi.yandex.ru'
    AUTH_URL = 'https://passport.yandex.ru/auth?retpath=https%3A%2F%2Ffleet.taxi.yandex.ru'
    TAXOPARK_URL = 'https://fleet.taxi.yandex.ru/map?park=2f51f552dc07460dbf9f18e6176fc752'

    LOGIN_ID = 'passp-field-login'
    PASSWORD_ID = 'passp-field-passwd'

    BUSY_BUTTON_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[1]/div/div/div/button[2]'
    PHONE_TAGS_XPATH = '/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[2]/div[2]/ul/div[{}]/div/a'

    USER_LIST_TAG = 'user-list'

    def __init__(self, login, password):
        self.login = login
        self.password = password

        self._firefox = None
        self._user_list_tag = None
        self._phone_list_selector = None
        self._busy_button_pressed = False
        self = self.__enter__()

    def __enter__(self):
        """
        Возвращает авторизованный драйвер
        """
        logger.info('launching...')

        options = Options()
        options.headless = True if HEADLESS else False
        self._firefox = webdriver.Firefox(options=options)
        self._firefox.get(self.AUTH_URL)
        self._submit_login()
        self._submit_password()
        self._firefox.get(self.BASE_URL)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.exception(exc_val)
        self._user_list_tag = None
        self._phone_list_selector = None
        self._busy_button_pressed = False
        self._firefox.quit()

    def close(self, exc_type, exc_val, exc_tb):
        logger.info('closing')
        self.__exit__(exc_type, exc_val, exc_tb)

    def get_drivers_from_map(self):
        """
        Возвращает дикты с водителями, которые доступны во вьюхе /maps
        Этот метод удобен для сбора занятых водителей
        """
        logger.info('getting drivers from map')

        if not self._firefox.current_url == self.TAXOPARK_URL:
            self._firefox.get(self.TAXOPARK_URL)

        if not self._busy_button_pressed:
            sleep(1)
            self._firefox.find_element_by_xpath(self.BUSY_BUTTON_XPATH).click()
            self._busy_button_pressed = True

        if self._user_list_tag:
            user_list_tag = self._user_list_tag
        else:
            user_list_tag = self._firefox.find_element_by_class_name(self.USER_LIST_TAG)
            self._user_list_tag = user_list_tag

        user_list = user_list_tag.text.split('\n')

        users = []
        for i in range(0, len(user_list), 4):
            chunk = tuple(user_list[i:i+4][1:])
            fullname, status, minutes = chunk
            name, surname, patronymic = fullname.split()
            logger.info('adding user %s', surname)
            users.append({
                'name': name,
                'surname': surname,
                'patronimyc': patronymic,
                'status': status,
                'minutes': minutes.split()[0],
                'time': datetime.now().strftime(TIME_FORMAT),
            })

        for i in range(1, len(users) + 1):
            logger.info('add phone number to user %s', users[i-1]['surname'])
            selector = self.PHONE_TAGS_XPATH.format(i)
            phone_tag = self._firefox.find_element_by_xpath(selector)
            href = phone_tag.get_attribute('href')
            phone_number = href.split(':')[1]
            users[i - 1]['telephone'] = phone_number

        return users

    def _submit_login(self):
        logger.info('login...')
        login_input = WebDriverWait(self._firefox, 10).until(
            ec.presence_of_element_located((By.ID, self.LOGIN_ID))
        )
        login_input.send_keys(self.login)
        sleep(1)
        login_input.submit()
        sleep(1)

    def _submit_password(self):
        password_input = WebDriverWait(self._firefox, 10).until(
            ec.presence_of_element_located((By.ID, self.PASSWORD_ID)))
        password_input.send_keys(self.password)
        sleep(1)
        password_input.submit()
        sleep(1)

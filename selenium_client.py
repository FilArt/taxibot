from time import sleep

from retry import retry
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from typing import List, Dict
from urllib.parse import urlparse

from config import HEADLESS, YANDEX_PASSWORD, YANDEX_LOGIN
from log import selenium_logger as logger

AUTH_URL = "https://passport.yandex.ru/auth"
LOGIN_ID = "passp-field-login"
PASSWORD_ID = "passp-field-passwd"


class SeleniumClient:
    BROWSER: webdriver.Chrome = None
    BUSY = False

    BASE_URL = "https://fleet.taxi.yandex.ru/"
    TAXOPARK_URL = "https://fleet.taxi.yandex.ru/map"
    DRIVERS_URL = BASE_URL + "drivers"

    BUSY_BUTTON_XPATH = "/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[1]/div/div/div/button[2]"
    PHONE_TAGS_XPATH = "/html/body/div[2]/div[3]/div[4]/div/div/div[1]/div/div[2]/div[2]/ul/div[{}]/div/a"

    USER_LIST_TAG = "user-list"

    @classmethod
    def init(cls):
        logger.info("launching")
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.headless = True if HEADLESS else False
        browser = webdriver.Chrome(options=options)

        logger.debug("authentication of webdriver")
        browser.get(AUTH_URL)
        login_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, LOGIN_ID))
        )
        login_input.send_keys(YANDEX_LOGIN)
        login_input.submit()

        password_input = WebDriverWait(browser, 10).until(
            ec.presence_of_element_located((By.ID, PASSWORD_ID))
        )
        password_input.send_keys(YANDEX_PASSWORD)
        password_input.submit()
        sleep(1)
        cls.BROWSER = browser

    def __del__(self):
        self.BROWSER.quit()

    @classmethod
    def get_all_drivers_info(cls) -> List[Dict]:
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
            result.append(
                {
                    "name": name,
                    "surname": surname,
                    "patronymic": patronymic,
                    "phone": phone.text,
                }
            )

        # TODO: доделать переход по пагинации
        cls.BUSY = False
        return result

    @classmethod
    def get_drivers_info_from_map(cls) -> List[Dict]:
        """
        Возвращает дикты с водителями, которые доступны во вьюхе /maps
        Этот метод удобен для сбора занятых водителей
        """
        while cls.BUSY:
            sleep(1)
        cls.BUSY = True
        logger.debug("getting drivers from map")

        p = urlparse(cls.BROWSER.current_url)
        if "{}://{}{}".format(p.scheme, p.netloc, p.path) != cls.TAXOPARK_URL:
            cls.BROWSER.get(cls.TAXOPARK_URL)

        user_list = cls._scrap_user_list()
        if not user_list:
            logger.warning("no one user found")

        logger.debug("fetching drivers info from map")
        drivers_info_dicts = []
        for i in range(0, len(user_list), 4):
            chunk = tuple(user_list[i:i + 4][1:])
            fullname, status, minutes = chunk
            minutes = int(minutes.split()[0])
            surname, name, patronymic = fullname.split()
            drivers_info_dicts.append(
                {
                    "name": name,
                    "surname": surname,
                    "patronymic": patronymic,
                    "status": {"value": status, "duracity": minutes},
                }
            )

        for i in range(1, len(drivers_info_dicts) + 1):
            selector = cls.PHONE_TAGS_XPATH.format(i)
            phone_tag = cls.BROWSER.find_element_by_xpath(selector)
            href = phone_tag.get_attribute("href")
            phone = href.split(":")[1]
            drivers_info_dicts[i - 1]["phone"] = phone

        cls.BUSY = False
        return drivers_info_dicts

    @classmethod
    @retry(tries=3)
    def _scrap_user_list(cls):
        try:
            sleep(1)
            cls.BROWSER.find_element_by_xpath(cls.BUSY_BUTTON_XPATH).click()
        except NoSuchElementException:
            logger.warning("busy button not found. refreshing.")
            cls.BROWSER.refresh()
        return cls.BROWSER.find_element_by_class_name(cls.USER_LIST_TAG).text.split(
            "\n"
        )


SeleniumClient.init()

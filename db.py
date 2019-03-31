from datetime import datetime

import mongoengine as me

from config import MONGO_SETTINGS, PENALTIES
from log import db_logger as logger

me.connect(
    MONGO_SETTINGS["DB_NAME"],
    host=MONGO_SETTINGS["HOST"],
    port=MONGO_SETTINGS["PORT"],
    username=MONGO_SETTINGS["USERNAME"],
    password=MONGO_SETTINGS["PASSWORD"],
)


class DriverStatus(me.EmbeddedDocument):
    value = me.StringField(max_length=30, min_length=2)
    set_at = me.DateTimeField()


class DriverTG(me.EmbeddedDocument):
    id = me.IntField(unique=True, sparse=True)
    name = me.StringField(unique=True, sparse=True)


class Driver(me.Document):
    name = me.StringField(required=True, max_length=20)
    surname = me.StringField(required=True)
    patronymic = me.StringField(required=False, max_length=20)
    phone = me.StringField(required=True, max_length=20, unique=True)
    status = me.EmbeddedDocumentField(DriverStatus)
    tg = me.EmbeddedDocumentField(DriverTG)
    lunch_count = me.IntField(default=0, min_value=0, max_value=5)
    last_lunch_request_time = me.DateTimeField()

    def __str__(self):
        return f'{self.name} {self.surname}'

    def add_tg_info(self, tg_name: str, tg_id: int):
        self.tg = DriverTG(name=tg_name, id=tg_id)
        self.save()

    @property
    def tg_id(self):
        return self.tg.id if self.tg else None

    @property
    def tg_name(self):
        return self.tg.name if self.tg else None

    @property
    def busy(self):
        return self.status.value.lower() in ("занят", "busy")

    @classmethod
    def from_driver_info(cls, driver_info: dict) -> "Driver":
        result = cls.objects.filter(
            **{k: v
               for k, v in driver_info.items() if k != "status"})
        if result:
            result = result[0]
            status = driver_info["status"]
            result.status = DriverStatus(**status) if status else DriverStatus()
            return result
        result = cls(**driver_info)
        return result

    def to_dict(self):
        return {
            "name": self.name,
            "surname": self.surname,
            "phone": self.phone,
            "patronymic": self.patronymic,
            "tg_id": self.tg.id if self.tg else None,
            "tg_name": self.tg.name if self.tg else None,
        }


class Payload(me.Document):
    driver = me.ReferenceField(
        Driver, required=True, reverse_delete_rule=me.CASCADE)
    penalty = me.IntField(min_value=0, required=True)
    timeout = me.IntField(min_value=0)
    timeout_set_at = me.DateTimeField()
    exclude = me.BooleanField(default=False)

    def update_timeout(self):
        timeout = self.timeout
        if timeout:
            timeout_seconds = timeout * 60
            now = datetime.now()
            passed_seconds = (now - self.timeout_set_at).seconds
            if passed_seconds >= timeout_seconds:
                self.timeout = None
            else:
                self.timeout = int((timeout_seconds - passed_seconds) // 60)
        self.save()

    def increment_penalties(self):
        max_penalty = max(PENALTIES.keys())
        if self.penalty == max_penalty:
            self.penalty = 0
            logger.info("Penalty increased for %s %s", self.driver.name,
                        self.driver.surname)
        else:
            self.penalty += 1
        self.save()


class Admin(me.Document):
    tg_id = me.IntField(required=True)


class Config(me.Document):
    dispatcher_chat_id = me.IntField(000000)
    lunch_timeout = me.IntField(default=30)

    check_drivers_interval = me.IntField(
        min_value=1, max_value=60, default=5)  # minutes
    max_busy_time = me.IntField(
        min_value=1, max_value=60, default=5)  # minutes

    translation_map = {
        "check_drivers_interval":
        "Периодичность проверки водителей (в минутах)",
        "dispatcher_chat_id": "ID диспетчера",
        "max_busy_time": "Максимальное время простоя водителя (в минутах)",
        "lunch_timeout":
        "Время обеда водителя (отключает уведомления о простое)",
    }

    def set_lunch_timeout(self, new_value: int):
        config = self.get()
        old_value = config.lunch_timeout
        config.lunch_timeout = new_value
        config.save()
        logger.info(
            'config modified. value "lunch_timeout"'
            "chaged from %i to %i",
            old_value,
            new_value,
        )

    def set_check_drivers_interval(self, new_value: int):
        config = self.get()
        old_value = config.check_drivers_interval
        config.check_drivers_interval = new_value
        config.save()
        logger.info(
            'config modified. value "max_busy_time"'
            "chaged from %i to %i",
            old_value,
            new_value,
        )

    def set_dispatcher_chat_id(self, new_value: int):
        config = self.get()
        old_value = config.dispatcher_chat_id
        config.dispatcher_chat_id = new_value
        config.save()
        logger.info(
            'config modified. value "dispatcher_chat_id" '
            "chaged from %i to %i",
            old_value,
            new_value,
        )

    def set_max_busy_time(self, new_value: int):
        config = self.get()
        old_value = config.max_busy_time
        config.max_busy_time = new_value
        config.save()
        logger.info(
            'config modified. value "max_busy_time"'
            "chaged from %i to %i",
            old_value,
            new_value,
        )

    @classmethod
    def get(cls):
        conf = cls.objects.first()
        if not conf:
            conf = Config()
            conf.save()
        return conf

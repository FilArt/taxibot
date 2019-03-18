import mongoengine as me
from datetime import datetime

me.connect(
    'taxi',
    host='localhost',
    port=27017,
    username='taxi',
    password='taxi',
)


class DriverStatus(me.EmbeddedDocument):
    value = me.StringField(max_length=30, min_length=2)
    duracity = me.IntField(min_value=0, max_value=1000)
    last_updated_at = me.DateTimeField()


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

    def add_tg_info(self, tg_name: str, tg_id: int):
        self.tg = DriverTG(name=tg_name, id=tg_id)
        self.save()

    @property
    def busy(self):
        return self.status.value == 'Busy'

    @classmethod
    def from_driver_info(cls, driver_info: dict) -> 'Driver':
        result = cls.objects.filter(**driver_info)
        if result:
            return result[0]
        result = cls(**driver_info)
        result.save()
        return result

    def __str__(self):
        return f'{self.name} {self.surname}'


class Payload(me.Document):
    driver = me.ReferenceField(Driver, required=True, reverse_delete_rule=me.CASCADE)
    penalty = me.IntField(min_value=0, required=True)
    timeout = me.IntField(min_value=0)
    timeout_set_at = me.DateTimeField()

    def update_timeout(self):
        timeout = self.timeout
        if timeout:
            timeout_seconds = timeout * 60
            now = datetime.now()
            passed_seconds = (now - self.timeout_set_at).seconds
            if passed_seconds >= timeout_seconds:
                self.timeout = None
            else:
                self.timeout = (timeout_seconds - passed_seconds) // 60
        self.save()

    def increment_penalties(self):
        self.penalty += 1


class Admin(me.Document):
    tg_id = me.IntField(required=True)


class Dispatcher(me.Document):
    chat_id = me.IntField(required=True)

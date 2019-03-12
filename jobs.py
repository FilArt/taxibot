from datetime import datetime
from telegram.bot import Bot
from telegram.ext.jobqueue import Job, JobQueue

from config import YANDEX_LOGIN, YANDEX_PASSWORD, CHECK_DRIVERS_TASK_INTERVAL, NEW_DRIVERS_STATUSES_FN, ALL_DRIVERS_FN
from fs_store import Store
from log import jobs_logger as logger
from punishment import Punisher, Punishment
from selenium_client import SeleniumClient
from taxopark import Taxopark
from utils import merge_with_pattern


def update_drivers(bot: Bot, job: Job):
    with SeleniumClient(YANDEX_LOGIN, YANDEX_PASSWORD) as client:
        logger.info('updating drivers list')
        start_middle = datetime.now()
        drivers = client.get_all_drivers()
        if drivers:
            Store.store_failsafe(ALL_DRIVERS_FN, drivers)
        end_middle = datetime.now()
        elapsed_middle = end_middle - start_middle
        logger.info('drivers list update for %i seconds', elapsed_middle.seconds)


def fetching_drivers(bot: Bot, job: Job):
    with SeleniumClient(YANDEX_LOGIN, YANDEX_PASSWORD) as client:
        logger.info('fetching drivers')
        start_main = datetime.now()
        drivers = client.get_drivers_from_map()
        if drivers:
            Store.store_failsafe(NEW_DRIVERS_STATUSES_FN, drivers)
        end_main = datetime.now()
        elapsed_main = end_main - start_main
        logger.info('drivers fetched for %i seconds', elapsed_main.seconds)


def process_supervision(bot: Bot, job: Job):
    logger.info('Checking drivers...')
    payloads = Punisher.fetch_and_update_busy_drivers_payloads()
    if not payloads:
        return

    for payload in payloads:

        timeout = payload.timeout
        if timeout and timeout > 0:
            continue

        penalties = payload.penalties
        punishment = Punishment(penalties)

        context = (punishment, payload)

        if punishment.is_warning:
            job.job_queue.run_once(send_warning, 0, context=context)

        elif punishment.is_call_dispatcher:
            job.job_queue.run_once(call_dispatcher, 0, context=context)


def send_warning(bot: Bot, job: Job):
    """
    Послать водителю предупреждение.
    """
    punishment, payload = job.context
    name, surname = payload.name, payload.surname
    logger.info("Sending warning to %s %s", name, surname)
    warning = punishment.penalty['message']
    user_id = Taxopark.get_driver(name=name, surname=surname).tg_id
    bot.send_message(
        user_id,
        warning,
    )


def call_dispatcher(bot: Bot, job: Job):
    """
    Ну все это бан.
    """
    punishment, payload = job.context
    name, surname = payload.name, payload.surname
    driver = Taxopark.get_driver(name=name, surname=surname)

    logger.info("Sending warning to %s %s", name, surname)

    message_pattern = punishment.penalty['message']
    message = merge_with_pattern(message_pattern, driver.to_dict())

    bot.send_message(
        Taxopark.get_dispatcher_chat_id(),
        message,
    )


def run_jobs(job_queue: JobQueue):
    job_queue.run_repeating(process_supervision, interval=CHECK_DRIVERS_TASK_INTERVAL)

from datetime import datetime
from telegram.bot import Bot
from telegram.ext.jobqueue import Job, JobQueue

from config import CHECK_DRIVERS_TASK_INTERVAL
from log import jobs_logger as logger
from punishment import Punisher, Punishment
from taxopark import Taxopark
from utils import merge_with_pattern


def process_supervision(bot: Bot, job: Job):
    logger.info('Checking drivers...')
    payloads = Punisher.fetch_and_update_busy_drivers_payloads()
    if not payloads:
        return

    for payload in payloads:

        timeout = payload.timeout
        if timeout:
            timeout = payload.update_timeout()
            timeout_set_at = payload.timeout_set_at
            if timeout and timeout_set_at:
                passed_minutes = (datetime.now() - timeout_set_at).minute
                if passed_minutes <= timeout:
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
    phone = payload.phone
    logger.info("Sending warning to %s", phone)
    warning = punishment.penalty['message']
    tg_id = Taxopark.get_driver(name=name, surname=surname).tg_id
    bot.send_message(tg_id, warning)


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

    bot.send_message(Taxopark.get_dispatcher_chat_id(), message)


def run_jobs(job_queue: JobQueue):
    job_queue.run_once(process_supervision, 0)
    # job_queue.run_repeating(process_supervision, interval=CHECK_DRIVERS_TASK_INTERVAL)

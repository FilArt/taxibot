from telegram.bot import Bot
from telegram.ext.jobqueue import Job, JobQueue

from config import CHECK_DRIVERS_TASK_INTERVAL
from log import jobs_logger as logger
from punishment import Punisher
from taxopark import Taxopark


def process_supervision(bot: Bot, job: Job):
    logger.info('checking drivers')

    drivers = Taxopark.get_all_drivers_from_map()
    for driver in drivers:
        if driver.status.busy:
            continue
        punisher = Punisher(bot)
        punisher.punish_driver(driver)


def run_jobs(job_queue: JobQueue):
    # job_queue.run_once(process_supervision, 0)
    job_queue.run_repeating(process_supervision, interval=CHECK_DRIVERS_TASK_INTERVAL)

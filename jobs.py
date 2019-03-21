from time import sleep, monotonic

from telegram.bot import Bot
from telegram.ext.jobqueue import Job, JobQueue

from db import Config
from log import jobs_logger as logger
from punishment import Punisher
from taxopark import Taxopark


# noinspection PyUnusedLocal
def process_supervision(bot: Bot, job: Job):
    logger.info("checking drivers")

    start = monotonic()

    drivers = Taxopark.get_all_drivers_from_map()
    for driver in drivers:
        punisher = Punisher(bot)
        punisher.punish_driver(driver)

    config = Config.get()
    interval = config.check_drivers_interval * 60

    end = monotonic()
    extra_time = interval - (end - start)
    if extra_time > 0:
        logger.info("supervisor will sleep for %i seconds", extra_time)
        sleep(extra_time)


def run_jobs(job_queue: JobQueue):
    job_queue.run_repeating(process_supervision, interval=0)


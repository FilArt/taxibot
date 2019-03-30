import sentry_sdk

from telegram.ext import Updater

from config import TOKEN, REQUEST_KWARGS
from handlers import handling_handlers
from jobs import run_jobs
from selenium_client import SeleniumClient

sentry_sdk.init("https://feaba2f28b9f4a078fa57026f5b5b356@sentry.io/1427389")

updater = Updater(token=TOKEN, request_kwargs=REQUEST_KWARGS, workers=10)
job_queue = updater.job_queue


def main():
    run_jobs(job_queue)
    handling_handlers(updater.dispatcher)
    updater.start_polling()
    # updater.idle()


if __name__ == "__main__":
    try:
        main()
    except:
        SeleniumClient.BROWSER.quit()

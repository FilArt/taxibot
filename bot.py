from telegram.ext import Updater

from config import TOKEN, REQUEST_KWARGS
from handlers import handling_handlers
from jobs import run_jobs

updater = Updater(token=TOKEN, request_kwargs=REQUEST_KWARGS)
job_queue = updater.job_queue


def main():
    run_jobs(job_queue)
    handling_handlers(updater.dispatcher)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

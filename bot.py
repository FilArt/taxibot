from telegram.ext import Updater

from config import TOKEN
from jobs import run_jobs
from handlers import handling_handlers


def main():
    updater = Updater(token=TOKEN)

    run_jobs(updater.job_queue)
    handling_handlers(updater.dispatcher)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

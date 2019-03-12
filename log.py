import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('main')
jobs_logger = logging.getLogger('jobs')
selenium_logger = logging.getLogger('selenium')

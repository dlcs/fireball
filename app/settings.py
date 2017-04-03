"""Settings for Fireball"""
import os

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
WORK_FOLDER = os.environ.get('WORK_FOLDER')
DOWNLOAD_POOL_SIZE = int(os.environ.get('FIREBALL_DOWNLOAD_POOL_SIZE'))

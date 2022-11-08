"""Settings for Fireball"""
import os
import distutils.util

DEBUG = bool(distutils.util.strtobool(os.getenv("DEBUG", "True")))

WORK_FOLDER = os.getenv('FIREBALL_WORK_FOLDER', '/tmp')
DOWNLOAD_POOL_SIZE = int(os.getenv('FIREBALL_DOWNLOAD_POOL_SIZE', '50'))
DEFAULT_DPI = 300
PDF_COMPLIANCE_VERSION = "%PDF-1.3"

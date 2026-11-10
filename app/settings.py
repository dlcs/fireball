"""Settings for Fireball"""
import os

DEBUG = os.getenv("DEBUG", "True").lower() in ("y", "yes", "t", "true", "on", "1")  # distutils removed in py3.12

WORK_FOLDER = os.getenv('FIREBALL_WORK_FOLDER', '/tmp')
DOWNLOAD_POOL_SIZE = int(os.getenv('FIREBALL_DOWNLOAD_POOL_SIZE', '50'))
DEFAULT_DPI = 300
PDF_COMPLIANCE_VERSION = "%PDF-1.3"
# ASCII85 encoding of embedded images is slow and inflates PDFs ~25%; off unless needed
USE_A85 = os.getenv("FIREBALL_USE_A85", "False").lower() in ("y", "yes", "t", "true", "on", "1")

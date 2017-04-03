import io
import os
import sys
import json
import logging
import subprocess
import tempfile
import settings
import requests
import uuid
import concurrent.futures

from flask import Flask, request, jsonify

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from PyPDF2 import PdfFileMerger

from PIL import Image

app = Flask(__name__)

def main():
    app.run(threaded=True, debug=True, port=5000, host='0.0.0.0')

@app.route('/pdf', methods=['POST'])
def generate():
    """example docstring"""
    request_data = request.json

    output = request_data["output"]
    pages = request_data["pages"]
    custom_types = request_data["customTypes"]

    session_folder = make_session_folder()

    (fd, workfile) = tempfile.mkstemp(prefix=session_folder)
    logging.info("generate will use workfile %s", workfile)

    # load the cover pdf for the first page
    cover_page = pages[0]
    (cover_page_fd, cover_page_filename) = tempfile.mkstemp(prefix=session_folder)
    logging.info("generate will use cover page filename %s", cover_page_filename)

    download_success = False
    if cover_page["type"] == "pdf" and cover_page["method"] == "download":
        download_success = download(cover_page["input"], cover_page_filename)
    else:
        logging.error("cover page was invalid")
        return "cover page was invalid"

    if download_success != True:
        logging.error("problem during download")
        return "problem during download"

    # generate pdf from the rest of the pages

    images_to_download = []
    playbook = []

    # skip first page
    pages_iterator = iter(pages)
    next(pages_iterator)
    for page in pages_iterator:
        page["id"] = str(uuid.uuid4())
        playbook.append(page)
        if page["type"] == "jpg" and page["method"] == "s3":
            images_to_download.append(page)
            logging.debug("adding %s to list of images to download", page["input"])
        elif page["type"] in custom_types:
            # found custom type
            logging.debug("found custom type %s", page["type"])
        else:
            logging.error("unknown page type %s", page["type"])
            return "unknown page type %s", page["type"]

    parallel_fetch(images_to_download, session_folder)

    #pdf = Canvas(pageCompression=1)

    #s3Connection = get_s3_connection()

    #write_file_to_s3(workfile, output, "application/pdf")

    response_data = {
        "success": True
    }

    return jsonify(response_data)

@app.route('/general-case/', methods=['POST'])
def generate_general_case():
    """example docstring"""
    request_data = request.get_json()

    output_method = request_data.get("method")
    output = request_data.get("output")

    pages = request_data.get("pages")

    custom_types = request_data.get("customTypes")

    # create a plan for the operations
    # if any pages are a pdf, then we will need to merge results with them

    # e.g. p1 = pdf, p2 = jpg, p3 = jpg
    # plan = merge(p1, pdf(p2,p3))

    # p1 = jpg, p2 = jpg, p3 = pdf
    # plan = merge(pdf(p1,p2), p3)

    # p1 = jpg, p2 = pdf, p3 = jpg, p4 = pdf
    # plan = merge(pdf(p1), p2, pdf(p3), p4)

    # p1 = jpg, p2 = jpg, p3 = jpg
    # plan = pdf(p1,p2,p3)

    plan = []

    if any(page.type == "pdf" for page in pages):
        # got pdfs to merge with our generated pages
        logging.debug("we will need to merge existing pdf with our work")

    workfile = ""

    page_index = 0

    for page in pages:
        page_index = page_index + 1
        logging.debug("page %d: type=%s", page_index, page.type)

    if output_method == "s3":
        write_file_to_s3(workfile, output, "application/pdf")

def write_file_to_s3(workfile, output, mime_type):
    """example docstring"""
    logging.debug("write_file_to_s3")

def make_session_folder():
    """example docstring"""
    session_folder = settings.WORK_FOLDER + "/" + str(uuid.uuid4())
    try:
        os.stat(session_folder)
    except os.error:
        os.mkdir(session_folder)
    return session_folder

def parallel_fetch(download_list, base_folder):
    """example docstring"""

    succeeded = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.DOWNLOAD_POOL_SIZE) as executor:
        futures = {
            executor.submit(fetch, base_folder, page):
                page for page in download_list
        }
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                succeeded += 1

    return download_list.count == succeeded

def fetch(base_folder, page):
    """example docstring"""
    target_filename = base_folder + "/" + page["id"]
    logging.debug("fetching %s to %s", page["input"], target_filename)
    return download(page["input"], target_filename)

def download(url, filename):
    """example docstring"""
    try:
        download_request = requests.get(url)
        with open(filename, 'wb') as file:
            file.write(download_request.content)
        return True
    except Exception:
        logging.exception("problem during download of %s to %s", url, filename)
    return False

def get_s3_connection():
    """example docstring"""
    return S3Connection(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def setup_logging():
    """example docstring"""
    logging.basicConfig(filename="fireball.log",
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', )
    logging.getLogger('boto').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)

if __name__ == "__main__":
    setup_logging()
    main()

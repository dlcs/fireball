import io
import os.path
import sys
import json
import logging
import subprocess
import settings

from flask import Flask, request, jsonify

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from PIL import Image

app = Flask(__name__)

S3CONNECTION = get_s3_connection()

def main():
    app.run(threaded=True, debug=True, port=5000, host='0.0.0.0')

@app.route('/pdf/', methods=['POST'])
def generate():
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
    logging.debug("write_file_to_s3")

def get_s3_connection():
    return S3Connection( \
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID, \
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)

def setup_logging():
    logging.basicConfig(filename="fireball.log",
                        filemode='a',
                        level=logging.DEBUG,
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s', )
    logging.getLogger('boto').setLevel(logging.ERROR)
    logging.getLogger('botocore').setLevel(logging.ERROR)

if __name__ == "__main__":
    setup_logging()

    main()

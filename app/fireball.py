import os
import math
import shutil

import logzero
import logging
from logzero import logger
import tempfile
import settings
import requests
import uuid
import concurrent.futures
import re

from flask import Flask, request, jsonify

import boto3

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.rl_config import defaultPageSize
from reportlab.lib.pagesizes import A4

from PyPDF2 import PdfFileMerger

from PIL import Image

from filechunkio import FileChunkIO
from decimal import Context, ROUND_HALF_EVEN
import decimal

app = Flask(__name__)

if settings.DEBUG:
    logzero.loglevel(logging.DEBUG)
else:
    logzero.loglevel(logging.INFO)

s3_resource = None


@app.route('/pdf', methods=['POST'])
def generate():
    session_folder = None
    try:
        global s3_resource

        request_data = request.json

        output = request_data["output"]
        pages = request_data["pages"]
        custom_types = request_data["customTypes"]
        title = request_data["title"]

        s3_resource = boto3.resource("s3")

        session_folder = make_session_folder()

        workfile = make_temp_file(prefix=session_folder + "/")
        logger.info(f"generate will use workfile {workfile}")

        # load the cover pdf for the first page
        cover_page = pages[0]
        cover_page_filename = make_temp_file(prefix=session_folder + "/")
        logger.info(f"generate will use cover page filename {cover_page_filename}")

        output_filename = make_temp_file(prefix=session_folder + "/")
        logger.info(f"generate will use output filename {output_filename}")

        download_success = False
        if cover_page["type"] == "pdf" and cover_page["method"] == "download":
            download_success = download(cover_page["input"], cover_page_filename)
        else:
            logger.error("cover page was invalid")
            return "cover page was invalid"

        if not download_success:
            logger.error("problem during download")
            return "problem during download"

        # generate pdf from the rest of the pages

        pages_to_download = []

        # skip first page
        pages_iterator = iter(pages)
        next(pages_iterator)
        for page in pages_iterator:
            page["id"] = str(uuid.uuid4())
            if page["type"] == "jpg" and page["method"] == "s3":
                pages_to_download.append(page)
                logger.debug(f"adding {page['input']} to list of images to download")
            elif page["type"] in custom_types:
                # found custom type
                logger.debug(f"found custom type {page['type']}")
            else:
                logger.error(f"unknown page type {page['type']}")
                return f"unknown page type {page['type']}"

        parallel_fetch(pages_to_download, session_folder)

        logger.debug("creating pdf")

        pdf = Canvas(workfile, pageCompression=1, pagesize=A4)

        pages_iterator = iter(pages)
        next(pages_iterator)
        for page in pages_iterator:
            if page in pages_to_download:
                downloaded_file = session_folder + "/" + page["id"]
                logger.debug(f"checking file {downloaded_file}")
                if os.path.exists(downloaded_file):
                    logger.debug("downloaded file exists")
                    if pdf_append_image(pdf, downloaded_file):
                        logger.debug("appended image")
                        # all good
                    else:
                        # problem
                        logger.debug("problem appending image")
                        return jsonify({"success": False, "message": "problem with image"})
                else:
                    # missing
                    pdf_append_custom(pdf, custom_types["missing"])
                    logger.debug("image was missing")
            elif page["type"] == "redacted":
                pdf_append_custom(pdf, custom_types["redacted"])
                logger.debug("image was redacted")
            pdf.showPage()

        logger.debug("saving pdf")
        pdf.save()

        # now merge the cover page with the workfile

        logger.debug("merging cover page and generated pdf")
        merger = PdfFileMerger()

        fix_pdf_compliance_version(cover_page_filename, settings.PDF_COMPLIANCE_VERSION)
        fix_pdf_compliance_version(workfile, settings.PDF_COMPLIANCE_VERSION)

        merge_input1 = open(cover_page_filename, "rb")
        merge_input2 = open(workfile, "rb")

        merger.append(merge_input1)
        merger.append(merge_input2)

        logger.debug(f"writing to {output_filename}")
        merge_output = open(output_filename, "wb")
        merger.write(merge_output)
        merge_output.close()

        success = write_file_to_s3(
            filename=output_filename,
            uri=output,
            title=title,
            mime_type="application/pdf")

        response_data = {
            "size": os.stat(output_filename).st_size,
            "success": success
        }

        status_code = 200 if success else 500

        return jsonify(response_data), status_code
    finally:
        cleanup(session_folder)


@app.route('/ping', methods=['GET'])
def ping():
    return {"status": "healthy"}


def make_temp_file(prefix):
    file = tempfile.NamedTemporaryFile(mode="w+b", delete=False, prefix=prefix)
    file.close()
    return file.name


def fix_pdf_compliance_version(filename, version):
    logger.debug(f"fixing PDF compliance version of {filename} to {version}")
    with open(filename, "r+b") as file:
        file.write(version.encode('ascii'))


def pdf_append_custom(pdf, custom_type):
    logger.debug("appending custom to pdf")

    page_width, page_height = A4

    logger.debug(f"page size = {page_width} x {page_height}")

    text = custom_type["message"]
    logger.debug(f"message = {text}")

    text_width = stringWidth(text, 'Helvetica', 12)
    logger.debug(f"text_width = {text_width}")

    text_start_y = page_height / 2
    logger.debug(f"text_start_y = {text_start_y}")

    text_start_x = (page_width - text_width) / 2
    logger.debug(f"text_start_x = {text_start_x}")

    pdf.setFont('Helvetica', 12)
    pdf.drawString(text_start_x, text_start_y, text)


def pdf_append_image(pdf, filename):
    try:
        logger.debug(f"appending image {filename}")
        image = Image.open(filename)
        image_width, image_height = image.size
        logger.debug(f"image size = {image_width} x {image_height}")
        page_width, page_height = A4
        logger.debug(f"page size = {page_width} x {page_height}")

        width, height = confine(image_width, image_height, page_width, page_height)
        logger.debug(f"confined image size = {width} x {height}")

        pdf.setPageSize(A4)

        # center
        image_x = (decimal.Decimal(page_width) - width) / 2
        image_y = (decimal.Decimal(page_height) - height) / 2
        logger.debug(f"image offsets = {image_x} x {image_y}")

        pdf.drawImage(filename, int(image_x), int(image_y), width=int(width), height=int(height))

    except Exception as append_exception:
        logger.exception(f"problem during append to pdf of {filename}: {append_exception}")
        return False
    return True


def write_file_to_s3(filename, uri, title, mime_type):
    logger.debug(f"write_file_to_s3 file: {filename} -> {uri} {title} ({mime_type})")

    (bucket_name, key) = parse_bucket_uri(uri)

    s3 = boto3.client("s3")

    try:
        logger.debug(f"bucket = {bucket_name}, key = {key}")

        multipart_session = s3.create_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            ContentType=mime_type,
            ContentDisposition='attachment; filename="' + title + '"')
        upload_id = multipart_session["UploadId"]
        chunk_size = 52428800
        source_size = os.stat(filename).st_size
        chunks_count = int(math.ceil(source_size / float(chunk_size)))

        parts = []

        for index in range(chunks_count):
            offset = index * chunk_size
            bytes = min(chunk_size, source_size - offset)
            with FileChunkIO(filename, "r", offset=offset, bytes=bytes) as file_part:
                logger.debug(f"uploading part {index}")
                part_response = s3.upload_part(UploadId=upload_id, Bucket=bucket_name, Key=key, Body=file_part,
                                               PartNumber=index + 1)
                parts.append({
                    "ETag": part_response["ETag"],
                    "PartNumber": index + 1
                })

        complete_response = s3.complete_multipart_upload(UploadId=upload_id, Bucket=bucket_name, Key=key,
                                                         MultipartUpload={
                                                             "Parts": parts
                                                         })

        if "Location" not in complete_response:
            logger.error("multipart upload failed")
            return False

        logger.debug("upload done")

    except Exception as write_exception:
        logger.exception(f"hit a problem while trying to upload {uri} to s3: {write_exception}")
        return False
    return True


def make_session_folder():
    session_folder = settings.WORK_FOLDER + "/" + str(uuid.uuid4())
    try:
        os.stat(session_folder)
    except os.error:
        os.mkdir(session_folder)
    return session_folder


def cleanup(session_folder):
    if session_folder:
        logger.debug(f"Removing folder {session_folder}")
        shutil.rmtree(session_folder, ignore_errors=False, onerror=None)


def parallel_fetch(download_list, base_folder):
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
    target_filename = base_folder + "/" + page["id"]
    logger.debug(f"fetching {page['input']} to {target_filename}")
    if page["input"].startswith('s3://'):
        return download_s3(page["input"], target_filename)
    else:
        return download(page["input"], target_filename)


def download_s3(uri, filename):
    global s3_resource

    logger.debug(f"using s3 strategy to download {uri}")

    (bucket_name, key) = parse_bucket_uri(uri)

    try:
        s3_resource.Object(bucket_name, key).download_file(filename + ".moving")

        logger.debug(f"downloaded {uri} -> {filename}.moving")
        os.rename(filename + ".moving", filename)
        logger.debug(f"renamed to {filename}")
    except Exception as download_exception:
        logger.exception(f"hit a problem while trying to download {uri}: {download_exception}")
        return False
    return True


def download(url, filename):
    try:
        download_request = requests.get(url)
        download_request.raise_for_status()
        with open(filename, 'wb') as file:
            file.write(download_request.content)
        return True
    except Exception as download_exception:
        logger.exception(f"problem during download of {url} to {filename}: {download_exception}")
    return False


def parse_bucket_uri(uri):
    """
    uri: s3://bucket/key
    returns: bucket, key
    """

    match = re.search(r's3://([^\/]+)/(.*)$', uri)
    if match:
        return match.group(1), match.group(2)

    return None, None


def confine(w, h, req_w, req_h):
    # reduce longest edge to size
    if w <= req_w and h <= req_h:
        return w, h

    context = Context(prec=17, rounding=ROUND_HALF_EVEN)
    d_w = context.create_decimal(w)
    d_req_w = context.create_decimal(req_w)
    d_h = context.create_decimal(h)
    d_req_h = context.create_decimal(req_h)
    scale = context.create_decimal(round(min(d_req_w / d_w, d_req_h / d_h), 17))
    return tuple(map(lambda d: (d * scale).to_integral_exact(context=context), [d_w, d_h]))

import os
import urllib.request
from logzero import logger
import fitz
import mimetypes
import datetime


def _is_pdf(tmp_file_name, http_response_obj):
    mimetype = str(mimetypes.guess_type(tmp_file_name)[0])
    logger.info(f"MimeType of {tmp_file_name} is {mimetype}.")
    content_type = http_response_obj.getheader("Content-Type")
    logger.info(f"Content-Type of {tmp_file_name} is {content_type}.")
    return "application/pdf" in content_type or "application/pdf" in mimetype


def download_pdf(url_dic, tmp_file_name, slack_bot_token):
    req = urllib.request.Request(url_dic["url"])
    if url_dic["is_slack_upload"]:
        req.add_header("Authorization", f"Bearer {slack_bot_token}")

    logger.info(f'Downloading pdf from {url_dic["url"]}...')
    try:
        with urllib.request.urlopen(req) as web_file:
            with open(tmp_file_name, "wb") as local_file:
                local_file.write(web_file.read())

            if not _is_pdf(tmp_file_name, web_file):
                logger.warn(f'Content-type of {url_dic["url"]} is not application/pdf.')
                os.remove(tmp_file_name)
                return False
    except Exception as e:
        logger.warning(f'Failed to download pdf from {url_dic["url"]}.')
        logger.warning(f"Exception: {str(e)}")
        return False

    return True


# See: https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/extract-images/extract-from-pages.py
def _recoverpix(doc, item):
    xref = item[0]  # xref of PDF image
    smask = item[1]  # xref of its /SMask

    # special case: /SMask or /Mask exists
    if smask > 0:
        pix0 = fitz.Pixmap(doc.extract_image(xref)["image"])
        if pix0.alpha:  # catch irregular situation
            pix0 = fitz.Pixmap(pix0, 0)  # remove alpha channel
        mask = fitz.Pixmap(doc.extract_image(smask)["image"])

        try:
            pix = fitz.Pixmap(pix0, mask)
        except Exception as e:  # fallback to original base image in case of problems
            logger.warning(f"Exception: {e}")
            pix = fitz.Pixmap(doc.extract_image(xref)["image"])

        if pix0.n > 3:
            ext = "pam"
        else:
            ext = "png"

        return {  # create dictionary expected by caller
            "ext": ext,
            "colorspace": pix.colorspace.n,
            "image": pix.tobytes(ext),
        }

    # special case: /ColorSpace definition exists
    # to be sure, we convert these cases to RGB PNG images
    if "/ColorSpace" in doc.xref_object(xref, compressed=True):
        pix = fitz.Pixmap(doc, xref)
        pix = fitz.Pixmap(fitz.csRGB, pix)
        return {  # create dictionary expected by caller
            "ext": "png",
            "colorspace": 3,
            "image": pix.tobytes("png"),
        }
    return doc.extract_image(xref)


def _extract_images(
    doc,
    min_width=600,
    min_height=600,
    abssize=2048,
    max_ratio=8,
    max_num=5,
):
    page_count = doc.page_count

    xreflist = []
    imglist = []
    images = []
    logger.info("Extracting images...")
    for pno in range(page_count):
        if len(images) >= max_num:
            break
        il = doc.get_page_images(pno)
        imglist.extend([x[0] for x in il])
        for img in il:
            xref = img[0]
            if xref in xreflist:
                continue
            width = img[2]
            height = img[3]
            if width < min_width and height < min_height:
                continue
            image = _recoverpix(doc, img)
            imgdata = image["image"]

            if len(imgdata) <= abssize:
                continue

            if width / height > max_ratio or height / width > max_ratio:
                continue
            suffix = str(datetime.datetime.now()).strip()
            imgname = f'image{pno + 1}_{suffix}.{image["ext"]}'
            images.append(imgname)
            imgfile = os.path.join(imgname)
            fout = open(imgfile, "wb")
            fout.write(imgdata)
            fout.close()
            xreflist.append(xref)

    logger.info(f"Successfully extract {len(xreflist)} images.")
    return images


def read(tmp_file_name):
    logger.info(f"Reading pdf text from {tmp_file_name}...")
    paper_text = ""
    paper_images = []
    with fitz.open(tmp_file_name) as doc:
        paper_text = "".join([page.get_text() for page in doc]).strip()
        paper_images = _extract_images(doc)

    # delete after refenrences
    reference_pos = max(
        paper_text.find("References"),
        paper_text.find("REFERENCES"),
        paper_text.find("参考文献"),
    )
    paper_text = paper_text[:reference_pos].strip()
    return paper_text, paper_images

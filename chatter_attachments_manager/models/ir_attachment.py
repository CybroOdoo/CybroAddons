#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import base64
import io
import zipfile

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import xlrd
except ImportError:
    xlrd = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import qrcode
except ImportError:
    qrcode = None


class IrAttachment(models.Model):
    """Extended Attachment Model (Inherited from 'ir.attachment')

    This class represents an extension of the original 'ir.attachment' model in
    Odoo. The 'ir.attachment' model is a built-in Odoo model that handles file
    attachments to various records, such as documents, emails, or notes.

    In this custom model, we extend the functionality of 'ir.attachment' to add
    new fields and custom methods to cater to specific requirements of our
    application.
    """

    _inherit = "ir.attachment"

    tag_ids = fields.Many2many(
        comodel_name="ir.attachment.tag",
        string="Tags",
        help="Tags assigned to this attachment.",
    )

    @api.model
    def decode_content(self, attach_id, doc_type=None):
        """Decode XLSX, XLS, DOCX or preview file data.

        :param int attach_id: id of attachment.
        :param str doc_type: the type of the given attachment ('xlsx', 'docx', etc.)
        :return: return decoded data dict or error string.
        """
        attachment = self.browse(attach_id)
        if not attachment.exists():
            raise UserError(self.env._("Attachment not found."))
        attachment.check_access("read")

        if not doc_type:
            name = attachment.name or ""
            if "." in name:
                doc_type = name.rsplit(".", 1)[1].lower()

        if attachment.raw:
            raw_data = (
                attachment.raw.content
                if hasattr(attachment.raw, "content")
                else bytes(attachment.raw)
            )
        else:
            raw_data = b""

        if doc_type == "docx":
            if DocxDocument is None:
                return "<p style='padding-top:8px;color:red;'>No preview available</p>"
            try:
                doc = DocxDocument(io.BytesIO(raw_data))
                paragraphs = [p.text for p in doc.paragraphs]
                return {
                    "type": "docx",
                    "content": paragraphs,
                }
            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
                AttributeError,
                IndexError,
                zipfile.BadZipFile,
                ImportError,
            ):
                return "<p style='padding-top:8px;color:red;'>No preview available</p>"

        if doc_type in ["xlsx", "xls"]:
            try:
                html_table = None
                if doc_type == "xlsx" and openpyxl is not None:
                    wb = openpyxl.load_workbook(
                        io.BytesIO(raw_data),
                        data_only=True,
                    )
                    ws = wb.active
                    rows = list(ws.iter_rows(values_only=True))
                    if rows:
                        header = "".join(
                            f"<th>{h if h is not None else ''}</th>"
                            for h in rows[0]
                        )
                        body = "".join(
                            "<tr>"
                            + "".join(
                                f"<td>{c if c is not None else ''}</td>"
                                for c in row
                            )
                            + "</tr>"
                            for row in rows[1:]
                        )
                        html_table = f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"
                elif doc_type == "xls" and xlrd is not None:
                    book = xlrd.open_workbook(file_contents=raw_data)
                    sheet = book.sheet_by_index(0)
                    if sheet.nrows > 0:
                        header = "".join(
                            f"<th>{sheet.cell_value(0, c)}</th>"
                            for c in range(sheet.ncols)
                        )
                        body = "".join(
                            "<tr>"
                            + "".join(
                                f"<td>{sheet.cell_value(r, c)}</td>"
                                for c in range(sheet.ncols)
                            )
                            + "</tr>"
                            for r in range(1, sheet.nrows)
                        )
                        html_table = f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"

                return {
                    "type": doc_type,
                    "content": html_table or "<table></table>",
                }
            except (
                ValueError,
                KeyError,
                TypeError,
                OSError,
                AttributeError,
                IndexError,
                zipfile.BadZipFile,
                ImportError,
            ):
                return "<p style='padding-top:8px;color:red;'>No preview available</p>"

        if doc_type == "pdf" or (attachment.mimetype and "pdf" in attachment.mimetype):
            return {
                "type": "pdf",
                "data": f"/web/content/{attachment.id}",
                "content": attachment.name,
            }

        return "Cannot preview this file."

    @api.model
    def save_edited_image(self, attachment_id, myImage=None, **kwargs):
        """Replace attachment image data with edited image.

        :param int attachment_id: id of attachment.
        :param str myImage: new image data url or base64 string
        :return dict
        """
        attachment = self.browse(attachment_id)
        if not attachment.exists():
            raise UserError(self.env._("Attachment not found."))
        attachment.check_access("write")

        image_data = myImage or kwargs.get("my_image") or kwargs.get("image") or ""
        if image_data:
            image_b64 = image_data
            if "," in image_data:
                image_b64 = image_data.split(",", 1)[1]
            raw_bytes = base64.b64decode(image_b64)
            attachment.write({"raw": raw_bytes})
            return {
                "id": attachment.id,
                "checksum": attachment.checksum,
                "mimetype": attachment.mimetype,
            }
        return {"id": attachment.id, "checksum": attachment.checksum}

    @api.model
    def generate_qr_code(self, attach_id):
        """Generate QR code for an attachment allowing users to download it.

        The QR code encodes a public URL using the attachment's access_token
        so that scanning the code from any device (phone, tablet) downloads
        the file directly without requiring an Odoo login session.
        """
        attachment = self.browse(attach_id)
        if not attachment.exists():
            raise UserError(self.env._("Attachment not found."))
        attachment.check_access("read")

        base_url = self.env["ir.config_parameter"].sudo().get_str("web.base.url", "")
        if not base_url:
            base_url = self.get_base_url()
        if not base_url.endswith("/"):
            base_url += "/"

        # Ensure an access_token exists so the URL is publicly accessible
        # without requiring the scanner to be logged in to Odoo.
        if not attachment.access_token:
            attachment.sudo().generate_access_token()
        token = attachment.access_token or ""

        safe_name = attachment.name or "file"
        if token:
            download_url = (
                f"web/content/{attach_id}"
                f"?access_token={token}"
                f"&filename={safe_name}"
                f"&download=true"
            )
        else:
            download_url = f"web/content/{attach_id}?download=true"

        data = {}
        if qrcode is not None:
            attach_qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=6,
                border=4,
            )
            attach_qr.add_data(base_url + download_url)
            attach_qr.make(fit=True)
            img = attach_qr.make_image(fill_color="black", back_color="white")
            temp = io.BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue()).decode("utf-8")
            data.update(
                {
                    "image": qr_image,
                    "company": self.env.company.name,
                    "filename": safe_name,
                    "url": base_url + download_url,
                },
            )
        return data

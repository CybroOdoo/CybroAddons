# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from io import BytesIO
import pandas as pd
from odoo import api, fields, models
try:
    import qrcode
    import base64
    import io
    from docx import Document as DocxDocument
except ImportError:
    io = None
    qrcode = None
    base64 = None
    DocxDocument = None


class IrAttachment(models.Model):
    """Extended Attachment Model (Inherited from 'ir.attachment')

    This class represents an extension of the original 'ir.attachment' model in
    Odoo. The 'ir.attachment' model is a built-in Odoo model that handles file
    attachments to various records, such as documents, emails, or notes.

    In this custom model, we extend the functionality of 'ir.attachment' to add
    new fields and custom methods to cater to specific requirements of our
    application.
    """
    _inherit = 'ir.attachment'

    tags_ids = fields.Many2many(comodel_name='ir.attachment.tag',
                                string='Tags', help="Tags for attachments")

    @api.model
    def decode_content(self, attach_id, doc_type):
        """Decode XLSX or DOC File Data.
        This method takes a binary file data from an attachment and decodes
        the content of the file for XLSX and DOC file formats.
        :param int attach_id: id of attachment.
        :param str doc_type: the type of the given attachment either 'xlsx' or
        'doc'
        :return: return the decoded data."""
        attachment = self.sudo().browse(attach_id)
        xlsx_data = base64.b64decode(attachment.datas)
        if doc_type == 'xlsx':
            content = pd.read_excel(BytesIO(xlsx_data), engine='openpyxl',
                                    converters={'A': str})
            html_table = content.to_html(index=False)
            return html_table
        if doc_type == 'docx':
            doc = DocxDocument(io.BytesIO(xlsx_data))
            paragraphs = [p.text for p in doc.paragraphs]
            return paragraphs
        text = "Cant Preview"
        return text

    @api.model
    def save_edited_image(self, attach_id, image):
        """The image is replaced by image from Toast image editor
        :param int attach_id: id of attachment.
        :param str image: new image data
        :return file containing image
        """
        file = self.sudo().browse(attach_id)
        file.write({'datas': image.strip('data:image/png;base64')})
        return file

    @api.model
    def generate_qr_code(self, attach_id):
        """Generate qr code for attachment tha allow anyone to download it."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        data = {}
        download_url = f"mail/channel/1/attachment/{attach_id}?download=true"
        if qrcode and base64:
            attach_qr = qrcode.QRCode(
                version=3,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4, border=4)
            attach_qr.add_data(base_url + download_url)
            attach_qr.make(fit=True)
            img = attach_qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            data.update({'image': qr_image,
                         'company': self.env.company.name})
        return data

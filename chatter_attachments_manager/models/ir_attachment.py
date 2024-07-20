# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nihala KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
import binascii
from io import BytesIO
import pandas as pd
from odoo import api, fields, models
import base64
import qrcode
from docx import Document as DocxDocument


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
        :param str doc_type: the type of the given attachment either 'xlsx' or 'doc'
        :return: return the decoded data."""
        attachment = self.sudo().browse(attach_id)
        if not attachment or not attachment.datas:
            return "Attachment not found or has no data"
        try:
            if doc_type == 'xlsx':
                data = binascii.a2b_base64(attachment.datas)
                content = pd.read_excel(BytesIO(data),
                                        engine='openpyxl',
                                        converters={'A': str})
                html_table = content.to_html(index=False)
                return html_table
            elif doc_type == 'docx':
                data = binascii.a2b_base64(attachment.datas)
                if DocxDocument is None:
                    return "Docx processing library not available"
                doc = DocxDocument(BytesIO(data))
                paragraphs = [p.text for p in doc.paragraphs]
                return paragraphs
            else:
                raise ValueError("Unsupported file format")
            html_table = content.to_html(index=False)
            return html_table
        except TypeError:
            return ("<p style='padding-top:8px;color:red;'>"
                    "No preview available</p>")
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
        """Generate qr code for attachment that allow anyone to download it."""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        data = {}
        download_url = f"/mail/channel/1/attachment/{attach_id}?download=true"
        if qrcode:
            attach_qr = qrcode.QRCode(
                version=3,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4, border=4)
            attach_qr.add_data(base_url + download_url)
            attach_qr.make(fit=True)
            img = attach_qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue()).decode('utf-8')
            data.update({'image': qr_image, 'company': self.env.company.name})
        return data

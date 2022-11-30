# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>))
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import fields, models, api, _

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
import binascii
import pytz
from odoo.exceptions import UserError
from odoo.tools.pycompat import to_text
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    qr = fields.Binary("QR Code", compute='generate_qrcode', store=True)

    def timezone(self, userdate):

        tz_name = self.env.context.get('tz') or self.env.user.tz
        contex_tz = pytz.timezone(tz_name)
        date_time = pytz.utc.localize(userdate).astimezone(contex_tz)
        return date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def string_hexa(self, value):
        if value:
            string = str(value)
            string_bytes = string.encode("UTF-8")
            encoded_hex_value = binascii.hexlify(string_bytes)
            hex_value = encoded_hex_value.decode("UTF-8")
            return hex_value

    def hexa(self, tag, length, value):
        if tag and length and value:
            hex_string = self.string_hexa(value)
            length = int(len(hex_string) / 2)
            conversion_table = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
            hexadecimal = ''
            while (length > 0):
                remainder = length % 16
                hexadecimal = conversion_table[remainder] + hexadecimal
                length = length // 16
            if len(hexadecimal) == 1:
                hexadecimal = "0" + hexadecimal
            return tag + hexadecimal + hex_string

    def qr_code_data(self):
        sellername = str(self.company_id.name)
        seller_vat_no = self.company_id.vat or ''
        seller_hex = self.hexa("01", "0c", sellername)
        vat_hex = self.hexa("02", "0f", seller_vat_no) or ""
        time_stamp = self.timezone(self.create_date)
        date_hex = self.hexa("03", "14", time_stamp)
        total_with_vat_hex = self.hexa("04", "0a", str(round(self.amount_total, 2)))
        total_vat_hex = self.hexa("05", "09", str(round(self.amount_tax, 2)))
        qr_hex = seller_hex + vat_hex + date_hex + total_with_vat_hex + total_vat_hex
        encoded_base64_bytes = base64.b64encode(bytes.fromhex(qr_hex)).decode()
        return encoded_base64_bytes

    @api.depends('state')
    def generate_qrcode(self):
        param = self.env['ir.config_parameter'].sudo()
        qr_code = param.get_param('advanced_vat_invoice.generate_qr')
        for rec in self:
            if rec.state == 'posted':
                if qrcode and base64:
                    if qr_code == 'automatically':
                        qr = qrcode.QRCode(
                            version=4,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=4,
                            border=1,
                        )
                        qr.add_data(self._origin.qr_code_data())
                        qr.make(fit=True)
                        img = qr.make_image()
                        temp = BytesIO()
                        img.save(temp, format="PNG")
                        qr_image = base64.b64encode(temp.getvalue())
                        rec.qr = qr_image
                else:
                    raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

    def generate_qr_button(self):
        param = self.env['ir.config_parameter'].sudo()
        qr_code = param.get_param('advanced_vat_invoice.generate_qr')
        for rec in self:
            if qrcode and base64:
                if qr_code == 'manually':
                    qr = qrcode.QRCode(
                        version=4,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=4,
                        border=1,
                    )
                    qr.add_data(self.qr_code_data())
                    qr.make(fit=True)
                    img = qr.make_image()
                    temp = BytesIO()
                    img.save(temp, format="PNG")
                    qr_image = base64.b64encode(temp.getvalue())
                    rec.qr = qr_image
            else:
                raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))

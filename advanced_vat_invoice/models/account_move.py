# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.

################################################################################
import base64
import binascii
from io import BytesIO
import pytz

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

try:
    import qrcode
except ImportError:
    qrcode = None


class AccountMove(models.Model):
    """Class for adding new button and a page in account move"""
    _inherit = 'account.move'

    qr = fields.Binary(
        string="QR Code",
        compute='_compute_qr_code',
        store=True,
        readonly=False,
        copy=False,
        help="QR code",
    )
    qr_button = fields.Boolean(
        compute="_compute_qr",
        help="Indicates whether the QR button is enabled",
    )
    qr_page = fields.Boolean(
        compute="_compute_qr",
        help="Indicates whether the QR page is enabled",
    )

    @api.depends('state')
    def _compute_qr(self):
        """Compute function for checking the value of a field in settings."""
        param = self.env['ir.config_parameter'].sudo()
        qr_code = param.get_bool('advanced_vat_invoice.is_qr')
        method = param.get_str('advanced_vat_invoice.generate_qr')
        for record in self:
            record.qr_button = bool(qr_code and method == 'manually')
            record.qr_page = bool(
                qr_code
                and (
                    (record.state in ['posted', 'cancelled']
                     and method == 'manually')
                    or method == 'automatically'
                )
            )

    def timezone(self, userdate):
        """Function to convert a user's date to their timezone."""
        tz_name = self.env.context.get('tz') or self.env.user.tz or 'UTC'
        try:
            contex_tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            contex_tz = pytz.utc
        userdate = userdate or fields.Datetime.now()
        if userdate.tzinfo:
            date_time = userdate.astimezone(contex_tz)
        else:
            date_time = pytz.utc.localize(userdate).astimezone(contex_tz)
        return date_time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def string_hexa(self, value):
        """Convert a string to a hexadecimal representation."""
        if value:
            string = str(value)
            string_bytes = string.encode("UTF-8")
            encoded_hex_value = binascii.hexlify(string_bytes)
            return encoded_hex_value.decode("UTF-8")
        return ""

    def hexa(self, tag, length, value):
        """Generate a hex value with tag, length, and value."""
        if tag and length and value:
            hex_string = self.string_hexa(value)
            length = int(len(hex_string) / 2)
            conversion_table = [
                '0', '1', '2', '3', '4', '5', '6', '7', '8',
                '9', 'a', 'b', 'c', 'd', 'e', 'f'
            ]
            hexadecimal = ''
            while length > 0:
                remainder = length % 16
                hexadecimal = conversion_table[remainder] + hexadecimal
                length = length // 16
            if len(hexadecimal) == 1:
                hexadecimal = "0" + hexadecimal
            return tag + hexadecimal + hex_string
        return ""

    def qr_code_data(self):
        """Generate QR code data for the current record."""
        seller_name = str(self.company_id.name)
        seller_vat_no = self.company_id.vat or ''
        seller_hex = self.hexa("01", "0c", seller_name)
        vat_hex = self.hexa("02", "0f", seller_vat_no) or ""
        time_stamp = self.timezone(self.create_date)
        date_hex = self.hexa("03", "14", time_stamp)
        sar_currency = self.env.ref('base.SAR')
        amount_total = self.currency_id._convert(
            self.amount_total,
            sar_currency,
            self.env.company,
            self.invoice_date or fields.Date.today(),
        )
        total_with_vat_hex = self.hexa(
            "04", "0a", str(round(amount_total, 2))
        )
        amount_tax = self.currency_id._convert(
            self.amount_tax,
            sar_currency,
            self.env.company,
            self.invoice_date or fields.Date.today(),
        )
        total_vat_hex = self.hexa(
            "05", "09", str(round(amount_tax, 2))
        )
        qr_hex = (
            seller_hex + vat_hex + date_hex + total_with_vat_hex
            + total_vat_hex
        )
        encoded_bytes = base64.b64encode(bytes.fromhex(qr_hex)).decode()
        return encoded_bytes

    def _generate_qr_image(self):
        """Generate QR code base64 image for a single move record."""
        self.ensure_one()
        if not (qrcode and base64):
            raise UserError(
                self.env._(
                    'Necessary requirements to run this operation are '
                    'not satisfied.'
                )
            )
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
        return base64.b64encode(temp.getvalue()).decode("utf-8")

    @api.depends('state')
    def _compute_qr_code(self):
        """Generate and save QR code after the invoice is posted."""
        param = self.env['ir.config_parameter'].sudo()
        qr_code = param.get_str('advanced_vat_invoice.generate_qr')
        for rec in self:
            if rec.state == 'posted' and qr_code == 'automatically':
                rec.qr = rec._generate_qr_image()
            elif rec.qr:
                rec.qr = rec.qr
            else:
                rec.qr = False

    def generate_qr_button(self):
        """Manually generate and save QR code."""
        param = self.env['ir.config_parameter'].sudo()
        qr_code = param.get_str('advanced_vat_invoice.generate_qr')
        for rec in self:
            if qr_code == 'manually':
                rec.qr = rec._generate_qr_image()

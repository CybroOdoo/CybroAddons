# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nubla Sherin k (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import qrcode
import base64
import uuid
from odoo import models, fields
import io


class PosOrder(models.Model):
    _inherit = 'pos.order'

    custom_qr_image = fields.Binary("Custom Receipt QR")
    custom_receipt_token = fields.Char("Receipt Token")

    def generate_custom_qr(self):
        """
                Generate a unique QR code for each POS order.

                The QR contains a secure receipt URL with a unique token.
                The generated QR image is stored in 'custom_qr_image'
                and the token is saved in 'custom_receipt_token'.
        """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        for order in self:
            token = str(uuid.uuid4())
            qr_data = f"{base_url}/my/receipt/{order.id}?t={token}"

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=8,
                border=3,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            order.custom_receipt_token = token
            order.custom_qr_image = base64.b64encode(buf.getvalue()).decode()

    def action_pos_order_paid(self):
        """
                After the order is marked as paid,
                automatically generate the custom receipt QR code.
        """
        res = super().action_pos_order_paid()
        self.generate_custom_qr()
        return res
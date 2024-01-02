# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
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
#
################################################################################
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO
try:
    import qrcode
except ImportError:
    qrcode = None
from odoo import fields, models, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    """ inherit res.users to add a field in users """
    _inherit = "res.users"
    qr_code = fields.Binary('QRcode', compute="_compute_generate_qr",
                            help="Use this to login (only for internal users)")

    def _compute_generate_qr(self):
        """method to generate QR code"""
        for detail in self:
            if qrcode and base64:

                qr_code = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                qr_code.add_data(detail.login)
                qr_code.make(fit=True)
                img = qr_code.make_image()
                memory = BytesIO()
                img.save(memory, format="PNG")
                qr_image = base64.b64encode(memory.getvalue())
                detail.update({'qr_code': qr_image})
            else:
                raise UserError(
                    _('Necessary Requirements To Run This Operation Is '
                      'Not Satisfied'))

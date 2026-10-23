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
import secrets
from io import BytesIO

try:
    import qrcode
except ImportError:
    qrcode = None

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import BinaryBytes


class ResUsers(models.Model):
    """Inherit res.users to add QR token and QR code generation for login."""
    _inherit = 'res.users'

    qr_token = fields.Char(
        string='QR Token',
        copy=False,
        readonly=True,
        index=True,
        groups='base.group_system',
        help="Secret token used for QR code login verification",
    )
    _qr_token_unique = models.Constraint(
        'unique(qr_token)',
        'The QR token must be unique.',
    )

    qr_code = fields.Binary(
        string='QR Code',
        compute='_compute_qr_code',
        store=True,
        groups='base.group_system',
        help="Use this to log in (only for internal users)",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Give every new internal user its own QR token.

        No field default is used on purpose: Odoo evaluates a callable default
        only once when the column is added, which would give all the existing
        users the same token.
        """
        users = super().create(vals_list)
        # sudo: the token field is restricted to administrators, but every
        # internal user must get a token whoever creates the user.
        for user in users.sudo().filtered(lambda rec: not rec.share and not rec.qr_token):
            user.qr_token = self._generate_qr_token()
        return users

    @api.model
    def _generate_qr_token(self):
        """Generate a cryptographically secure random token."""
        return secrets.token_urlsafe(32)

    def action_regenerate_qr_token(self):
        """Action to regenerate and assign a new QR token."""
        if not qrcode:
            raise UserError(
                self.env._("The 'qrcode' Python library is required to generate QR codes."),
            )
        for user in self:
            user.qr_token = self._generate_qr_token()

    @api.depends('qr_token')
    def _compute_qr_code(self):
        """Method to generate QR code from qr_token."""
        for user in self:
            if not user.qr_token or not qrcode:
                user.qr_code = False
                continue
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=4,
            )
            qr.add_data(user.qr_token)
            qr.make(fit=True)
            temp = BytesIO()
            qr.make_image().save(temp, format="PNG")
            user.qr_code = BinaryBytes(temp.getvalue())

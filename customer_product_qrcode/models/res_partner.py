# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResPartners(models.Model):
    """Extends the res partner model to include QR code functionality."""
    _inherit = 'res.partner'

    sequence = fields.Char(string="QR Sequence", readonly=True)
    qr = fields.Binary(string="QR Code", help='Used for Qr code')

    def init(self):
        """Initialize the QR sequence for customer partners with a combination
        of 'DEF', partner's name (without spaces), and partner's ID."""
        for record in self.env['res.partner'].search(
                [('customer_rank', '=', True)]):
            name = record.name.replace(" ", "")
            record.sequence = 'DEF' + name.upper() + str(record.id)

    @api.model
    def create(self, vals):
        """Create a new partner record and assign a unique QR sequence to
         it."""
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'customer_product_qr.config.customer_prefix')
        if not prefix:
            raise UserError(_('Set A Customer Prefix In General Settings'))
        prefix = str(prefix)
        seq = prefix + self.env['ir.sequence'].next_by_code(
            'res.partner') or '/'
        vals['sequence'] = seq
        return super().create(vals)

    @api.model
    def write(self, vals):
        """ this fn is to write vals"""
        return super().write(vals)

    @api.depends('sequence')
    def generate_qr(self):
        """Generate a QR code based on the partner's sequence and store it in
        the 'qr' field of the partner record."""
        if qrcode and base64:
            if not self.sequence:
                prefix = self.env['ir.config_parameter'].sudo().get_param(
                    'customer_product_qr.config.customer_prefix')
                if not prefix:
                    raise UserError(
                        _('Set A Customer Prefix In General Settings'))
                prefix = str(prefix)
                self.sequence = prefix + self.env['ir.sequence'].next_by_code(
                    'res.partner') or '/'
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.sequence)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.write({'qr': qr_image})
            return self.env.ref(
                'customer_product_qrcode.print_qr').report_action(self, data={
                 'data': self.id, 'type': 'cust'})
        else:
            raise UserError(
                _('Necessary Requirements To Run This Operation Is Not '
                  'Satisfied'))

    def get_partner_by_qr(self, **args):
        """THis fn is to get partner by qr """
        return self.env['res.partner'].search([('sequence', '=', self.id), ],
                                              limit=1).id

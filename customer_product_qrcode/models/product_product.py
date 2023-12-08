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
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    """Extends the productproduct model to include QR code functionality."""
    _inherit = 'product.product'

    sequence = fields.Char(string="QR Sequence", readonly=True,
                           help='to add sequence')
    qr = fields.Binary(string="QR Code", help='Qr file')

    @api.model
    def create(self, vals):
        """Create a new product and assign a unique QR sequence and QR code
        to it."""
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'customer_product_qr.config.product_prefix')
        if not prefix:
            raise UserError(_('Set A Product Prefix In General Settings'))
        prefix = str(prefix)
        seq = prefix + self.env['ir.sequence'].next_by_code(
            'product.product') or '/'
        vals['sequence'] = seq
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(vals['sequence'])
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        vals.update({'qr': qr_image})
        return super().create(vals)

    @api.depends('sequence')
    def generate_qr(self):
        """Generate a QR code based on the product's sequence and store it in
        the 'qr' field of the product."""
        if qrcode and base64:
            if not self.sequence:
                prefix = self.env['ir.config_parameter'].sudo().get_param(
                    'customer_product_qr.config.product_prefix')
                if not prefix:
                    raise UserError(
                        _('Set A Customer Prefix In General Settings'))
                prefix = str(prefix)
                self.sequence = prefix + self.env['ir.sequence'].next_by_code(
                    'product.product') or '/'
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
                'customer_product_qrcode.print_qr2').report_action(self, data={
                 'data': self.id, 'type': 'prod'})
        else:
            raise UserError(
                _('Necessary Requirements To Run This Operation Is Not'
                  ' Satisfied'))

    def get_product_by_qr(self, **args):
        """Retrieve a product based on the provided QR sequence."""
        return self.env['product.product'].search(
            [('sequence', '=', self.id), ], limit=1).id

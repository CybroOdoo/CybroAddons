# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

try:
    import qrcode
except ImportError:
    qrcode = None
from io import BytesIO
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import BinaryBytes


class ProductProduct(models.Model):
    """Extends the product model to include QR code functionality."""
    _inherit = 'product.product'

    qr_sequence = fields.Char(string="QR Sequence", readonly=True,
                              help='to add sequence')
    qr = fields.Binary(string="QR Code", help='Qr file')

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new product and assign a unique QR sequence and QR code
        to it if a prefix is configured."""
        prefix = self.env['ir.config_parameter'].sudo().get_str(
            'customer_product_qr.config.product_prefix')
        if prefix:
            prefix = str(prefix)
            for vals in vals_list:
                if not vals.get('qr_sequence'):
                    vals['qr_sequence'] = prefix + (
                        self.env['ir.sequence'].next_by_code('product.product')
                        or self.env._('New')
                    )
                    if qrcode:
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4,
                        )
                        qr.add_data(vals['qr_sequence'])
                        qr.make(fit=True)
                        img = qr.make_image()
                        temp = BytesIO()
                        img.save(temp, format="PNG")
                        vals['qr'] = BinaryBytes(temp.getvalue())
        return super().create(vals_list)

    def action_generate_sequence(self):
        """Generate sequence for product QR code."""
        prefix = self.env['ir.config_parameter'].sudo().get_str(
            'customer_product_qr.config.product_prefix')
        if not prefix:
            raise UserError(
                self.env._('Set a product prefix in General Settings.'))
        prefix = str(prefix)
        for record in self:
            if not record.qr_sequence:
                record.qr_sequence = prefix + (
                    self.env['ir.sequence'].next_by_code('product.product')
                    or '/'
                )

    def generate_sequence(self):
        """Server action alias for action_generate_sequence."""
        return self.action_generate_sequence()

    def action_generate_qr(self):
        """Generate a QR code based on the product's sequence and store it in
        the 'qr' field of the product."""
        if not qrcode:
            raise UserError(
                self.env._(
                    'Necessary requirements to run this operation are not'
                    ' satisfied.'
                )
            )
        self.action_generate_sequence()
        for record in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(record.qr_sequence)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            record.write({'qr': BinaryBytes(temp.getvalue())})
        return self.env.ref(
            'customer_product_qrcode.print_qr1').report_action(
                self, data={'data': self.ids, 'type': 'prod'})

    def get_product_by_qr(self, **args):
        """Retrieve a product based on the provided QR sequence."""
        sequence = args.get('qr_sequence') or args.get('sequence') or (
            self[:1].qr_sequence if self else False
        )
        return self.env['product.product'].search(
            [('qr_sequence', '=', sequence)], limit=1).id

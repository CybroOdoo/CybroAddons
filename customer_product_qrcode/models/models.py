# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
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

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError


class Partners(models.Model):
    _inherit = 'res.partner'

    sequence = fields.Char(string="QR Sequence", readonly=True)
    qr = fields.Binary(string="QR Code")

    def init(self):
        for record in self.env['res.partner'].search(
                [('customer_rank', '=', True)]):
            name = record.name.replace(" ", "")
            record.sequence = 'DEF' + name.upper() + str(record.id)

    @api.model
    def create(self, vals):
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'customer_product_qr.config.customer_prefix')
        if not prefix:
            raise UserError(_('Set A Customer Prefix In General Settings'))
        prefix = str(prefix)
        seq = prefix + self.env['ir.sequence'].next_by_code(
            'res.partner') or '/'
        vals['sequence'] = seq
        return super(Partners, self).create(vals)

    @api.depends('sequence')
    def generate_qr(self):
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
                _('Necessary Requirements To Run This Operation Is Not Satisfied'))

    def get_partner_by_qr(self, **args):
        return self.env['res.partner'].search([('sequence', '=', self.id), ],
                                              limit=1).id


class Products(models.Model):
    _inherit = 'product.product'

    sequence = fields.Char(string="QR Sequence", readonly=True)
    qr = fields.Binary(string="QR Code")

    @api.model
    def create(self, vals):
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
        return super(Products, self).create(vals)

    @api.depends('sequence')
    def generate_qr(self):
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
                _('Necessary Requirements To Run This Operation Is Not Satisfied'))

    def get_product_by_qr(self, **args):
        return self.env['product.product'].search(
            [('sequence', '=', self.id), ], limit=1).id


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def generate_qr(self):
        product = self.env['product.product'].search(
            [('product_tmpl_id', '=', self.id)])
        for rec in product:
            rec.generate_qr()
        return self.env.ref('customer_product_qrcode.print_qr2').report_action(
            self, data={'data': self.id, 'type': 'all'})


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_prefix = fields.Char(string="Customer QR Prefix")
    product_prefix = fields.Char(string="Product QR Prefix")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        customer_prefix = self.env["ir.config_parameter"].get_param(
            "customer_product_qr.config.customer_prefix")
        product_prefix = self.env["ir.config_parameter"].get_param(
            "customer_product_qr.config.product_prefix")
        res.update({
            'customer_prefix': customer_prefix if type(
                customer_prefix) else False,
            'product_prefix': product_prefix if type(product_prefix) else False
        }
        )
        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_product_qr.config.customer_prefix', self.customer_prefix)
        self.env['ir.config_parameter'].sudo().set_param(
            'customer_product_qr.config.product_prefix', self.product_prefix)

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
from odoo import fields, models


class ProductTemplate(models.Model):
    """
    ProductTemplate class for add methods and field for generate qr code,
    Methods:
        generate_qr(self):
            QRcode generating method
    """
    _inherit = 'product.template'

    def generate_qr(self):
        product = self.env['product.product'].search(
            [('product_tmpl_id', '=', self.id)])
        for rec in product:
            rec.generate_qr()
        return self.env.ref('customer_product_qrcode.print_qr2').report_action(
            self, data={'data': self.id, 'type': 'all'})

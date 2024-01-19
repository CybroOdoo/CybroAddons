# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ADVAITH B G (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ProductProduct(models.Model):
    """Inherits Products for multiple barcodes"""
    _inherit = 'product.product'

    multi_barcode_ids = fields.One2many('product.multiple.barcodes',
                                        'product_id', string='Barcodes',
                                        help='Set multiple barcode')

    def _check_multi_barcode(self, domain):
        """Check product have multi barcode or not"""
        product_id = None
        if len(domain) > 1:
            if 'barcode' in domain[0]:
                barcode = domain[0][2]
                bi_line = self.env['product.multiple.barcodes'].search(
                    [('product_multi_barcode', '=', barcode)])
                if bi_line:
                    product_id = bi_line.product_id.id
        return product_id

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None,
                    order=None):
        """For searching the product with multi barcode"""
        product_id = self._check_multi_barcode(domain)
        if product_id:
            domain = [('id', '=', product_id)]
        res = super().search_read(domain=domain, fields=fields, offset=offset,
                                  limit=limit, order=order)
        return res

    @api.model
    def create(self, vals):
        """Creating multi barcodes"""
        res = super(ProductProduct, self).create(vals)
        res.multi_barcode_ids.update({
            'product_template_id': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        """Updating multi barcodes"""
        res = super(ProductProduct, self).write(vals)
        self.multi_barcode_ids.update({
            'product_template_id': self.product_tmpl_id.id
        })
        return res

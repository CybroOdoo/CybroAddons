# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Risha C.T (<https://www.cybrosys.com>)
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
###################################################################################

from odoo import models, fields, api
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = 'product.product'

    product_multi_barcodes = fields.One2many('multi.barcode.products', 'product_multi', string='Barcodes')

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res.product_multi_barcodes.update({
            'template_multi': res.product_tmpl_id.id
        })
        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        self.product_multi_barcodes.update({
            'template_multi': self.product_tmpl_id.id
        })
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        print("666666666666666")
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('default_code', operator, name),
                      '|', ('barcode', operator, name), ('product_multi_barcodes', operator, name)]
        product_id = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(product_id).name_get()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_multi_barcodes = fields.One2many('multi.barcode.products', 'template_multi', string='Barcodes')

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes.update({
            'product_multi': res.product_variant_id.id
        })
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes:
            self.template_multi_barcodes.update({
                'product_multi': self.product_variant_id.id
            })
        return res


class ProductMultiBarcode(models.Model):
    _name = 'multi.barcode.products'

    multi_barcode = fields.Char(string="Barcode", help="Provide alternate barcodes for this product")
    product_multi = fields.Many2one('product.product')
    template_multi = fields.Many2one('product.template')

    def get_barcode_val(self, product):
        # returns barcode of record in self and product id
        return self.multi_barcode, product

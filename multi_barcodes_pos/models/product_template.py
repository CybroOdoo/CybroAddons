# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
       Inherit product.template model for adding fields
    """
    _inherit = 'product.template'

    template_multi_barcodes_ids = fields.One2many(
        'multi.barcode.products','template_multi_id',
        string='Barcodes', help="Multiple Barcodes for the product")

    @api.model
    def create(self, vals):
        """
           Create a new product template record with the provided values
           and update the associated multi-barcode product.
        """
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes_ids.update({
            'product_multi_id': res.product_variant_id.id
        })
        return res

    def write(self, vals):
        """
           Update the product template record with the provided values and
           update the associated multi-barcode product.
        """
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes_ids:
            self.template_multi_barcodes_ids.update({
                'product_multi_id': self.product_variant_id.id
            })
        return res

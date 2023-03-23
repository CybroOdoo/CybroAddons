# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """Inherits Product Template"""
    _inherit = 'product.template'

    template_multi_barcodes = fields.One2many('product.multiple.barcodes',
                                              'template_barcode',
                                              string='Barcodes')

    def write(self, vals):
        """Supering write method"""
        res = super(ProductTemplate, self).write(vals)
        if self.template_multi_barcodes:
            self.template_multi_barcodes.update({
                'product_barcode': self.product_variant_id.id
            })
        return res

    @api.model
    def create(self, vals):
        """Supering create method"""
        res = super(ProductTemplate, self).create(vals)
        res.template_multi_barcodes.update({
            'product_barcode': res.product_variant_id.id
        })
        return res

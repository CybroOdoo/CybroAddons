# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Rosmy John (<https://www.cybrosys.com>)
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
    """It introduces an additional field 'is_sample_product' to mark products
    as sample products. When a product is marked as a sample, its list price
    is set to 0.0."""
    _inherit = "product.template"

    is_sample_product = fields.Boolean(string="Sample Product",
                                       help="To know as a sample product")

    @api.onchange('is_sample_product')
    def _onchange_is_sample_product(self):
        """Change the product price when it is sample product"""
        self.list_price = 0.0 if self.is_sample_product else self.list_price
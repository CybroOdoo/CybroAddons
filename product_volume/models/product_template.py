# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
from odoo import api, models, fields


class ProductDimensionsVolume(models.Model):
    """Inheriting product_template to add new fields"""
    _inherit = 'product.template'

    length = fields.Char(string="Length", help="Enter length of the product")
    breadth = fields.Char(string="Breadth", help="Enter breadth of the product")
    height = fields.Char(string="Height", help="Enter height of the product")

    @api.onchange('length', 'breadth', 'height')
    def _onchange_product_measures(self):
        """Onchange function to calculate volume of the product"""
        self.volume = (float(self.length if self.length else 0) *
                       float(self.breadth if self.breadth else 0) * float(
            self.height if self.height else 0))

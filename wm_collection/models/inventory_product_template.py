# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models


class ProductTemplate(models.Model):
    """Extends Product Template with waste collection costing methods and unit conversions."""
    _inherit = 'product.template'

    @api.depends_context('company')
    @api.depends('categ_id.property_cost_method', 'is_waste_material')
    def _compute_cost_method(self):
        """
        Override the product cost method computation to default waste material
        products to 'average' costing, aligning with waste stream valuation
        accounting standards.
        """
        super(ProductTemplate, self)._compute_cost_method()
        for product in self:
            if product.is_waste_material:
                product.cost_method = 'standard'

# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM(odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ProductCategory(models.Model):
    """ Class to inherit product_category to add costing method """
    _inherit = "product.category"

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('last', 'Last Purchase Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string='Costing Method',
        company_dependent=True, copy=True,
        help="""Standard Price: The products are valued at their standard cost 
            defined on the product. Average Cost (AVCO): The products are 
            valued at weighted average cost. First In First Out (FIFO): The 
            products are valued supposing those that enter the company first 
            will also leave it first. Last Purchase Price: The products are 
            valued same as 'Standard Price' Method, But standard price defined 
            on the product will updated automatically with last purchase 
            price.""")

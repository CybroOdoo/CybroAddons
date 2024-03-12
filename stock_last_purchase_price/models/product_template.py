# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """ Class to inherit product.template to add costing method """
    _inherit = 'product.template'

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('last', 'Last Purchase Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string='Costing Method',
        company_dependent=True, copy=True,
        help="""Standard Price: The products are valued 
        at their standard cost defined on the product.
        Average Cost (AVCO): The products are valued at weighted average cost.
        First In First Out (FIFO): The products are valued supposing 
        those that enter the company first will also leave it first.
        Last Purchase Price: The products are valued same as 'Standard 
        Price' Method, But standard price defined on the product will 
        be updated automatically with last purchase price.""")

    def _set_cost_method(self):
        """ When going from FIFO to AVCO or to standard, we update the standard
        price with the average value in stock """
        if (self.property_cost_method == 'fifo' and
                self.cost_method in ['average', 'standard', 'last']):
            # Cannot use the `stock_value` computed field as it's already
            # invalidated when entering this method.
            valuation = sum([variant._sum_remaining_values()[0] for variant in
                             self.product_variant_ids])
            qty_available = self.with_context(company_owned=True).qty_available
            if qty_available:
                self.standard_price = valuation / qty_available
        return self.write({'property_cost_method': self.cost_method})

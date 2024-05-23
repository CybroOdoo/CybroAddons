# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ProductCustomerLeadTime(models.TransientModel):
    """
        Model for changing sale_delay (Customer Lead Time)
    """
    _name = 'product.customer.lead.time'
    _description = 'Product Customer Lead Time'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    sale_delay = fields.Float(string='Customer Lead Time',
                              help='Delivery lead time in days')

    def action_change_customer_lead_time(self):
        """
        Function for changing sale_delay (Customer Lead Time) of Selected Products
        """
        if self.product_ids and self.sale_delay != 0:
            for products in self.product_ids:
                products.write({'sale_delay': self.sale_delay})

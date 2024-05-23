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


class ProductCustomerTax(models.TransientModel):
    """
        Model for changing tax_ids (Customer Tax)
    """
    _name = 'product.customer.tax'
    _description = 'Product Customer Tax'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    tax_ids = fields.Many2many('account.tax',
                               domain="[('type_tax_use', '=', 'sale')]",
                               string="Customer Tax",
                               help='Customer Tax')

    def action_change_customer_tax(self):
        """
        Function for changing tax_ids (Customer Tax) of selected products
        """
        if self.product_ids and self.tax_ids:
            for products in self.product_ids:
                for items in self.tax_ids:
                    products.taxes_id = [fields.Command.link(items.id)]

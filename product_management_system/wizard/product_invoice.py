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


class ProductInvoice(models.TransientModel):
    """
        Model for changing invoice policy
    """
    _name = 'product.invoice'
    _description = 'Product Invoice'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    invoice_policy = fields.Selection([
        ('order', 'Ordered Quantities'),
        ('delivery', 'Delivered Quantities')],
        string='Invoicing Policy', help='Invoice policy of the product',
        default='order', required=True)

    def action_change_invoice_policy_products(self):
        """
        Function for changing invoice policy of selected products
        """
        if self.product_ids:
            for products in self.product_ids:
                products.write({'invoice_policy': self.invoice_policy})

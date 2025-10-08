# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherited sale order to super functions to add additional
    functionalities"""
    _inherit = 'sale.order'

    is_warranty_check = fields.Boolean(string='Warranty Check',
                                       help='Check this box if the item has'
                                            ' warranty.')

    def action_confirm(self):
        """Call the super method to perform the default confirmation
        behavior"""
        super(SaleOrder, self).action_confirm()
        # Loop through the order lines and check warranty for each product
        for order in self:
            for line in order.order_line:
                product = line.product_id
                if product.is_warranty_available:
                    self.is_warranty_check = True
                else:
                    self.is_warranty_check = False
        if (self.order_line.
                filtered(lambda x: x.product_id.is_warranty_available)):
            self.is_warranty_check = True
        else:
            self.is_warranty_check = False

    def action_open_smart_tab(self):
        """ To open warranty smart tab"""
        domain = [
            ('id', 'in',
             self.order_line.mapped('product_id.product_tmpl_id.id')),
            ('is_warranty_available', '=', True),
        ]
        products_with_warranty = self.env['product.template'].search(domain)
        for product in products_with_warranty:
            # Calculate the warranty expiry date based on the sale order date
            warranty_expiry_date = self.date_order + relativedelta(
                months=product.warranty_duration)
            product.write({'warranty_expiry': warranty_expiry_date})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Warranty Details',
            'view_mode': 'tree,form',
            'res_model': 'product.template',
            'views': [(self.env.ref('product_warranty_management_odoo.'
                                    'product_template_view_tree').id, 'tree'),
                      (self.env.ref('product_warranty_management_odoo.'
                                    'product_template_view_form').id, 'form')],
            'domain': domain
        }

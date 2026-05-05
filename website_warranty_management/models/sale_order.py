# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
        """ To open warranty smart tab and create registration records if missing"""
        domain = [
            ('sale_order_id', '=', self.id),
        ]
        
        # Ensure registrations exist for all products with warranty
        for line in self.order_line:
            product = line.product_id
            if product.is_warranty_available:
                # Check if registration already exists
                existing = self.env['warranty.registration'].search([
                    ('sale_order_id', '=', self.id),
                    ('product_id', '=', product.id)
                ])
                if not existing:
                    # Calculate expiry date
                    start_date = fields.Date.context_today(self)
                    duration = product.warranty_duration
                    period_type = product.warranty_period_type
                    
                    if period_type == 'days':
                        expiry_date = start_date + relativedelta(days=duration)
                    elif period_type == 'years':
                        expiry_date = start_date + relativedelta(years=duration)
                    else: # default to months
                        expiry_date = start_date + relativedelta(months=duration)
                        
                    self.env['warranty.registration'].create({
                        'customer_id': self.partner_id.id,
                        'sale_order_id': self.id,
                        'product_id': product.id,
                        'start_date': start_date,
                        'expiry_date': expiry_date,
                        'warranty_type': product.warranty_type,
                        'state': 'active'
                    })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Warranty Registrations',
            'view_mode': 'list,form',
            'res_model': 'warranty.registration',
            'domain': domain,
            'context': {'default_sale_order_id': self.id, 'default_customer_id': self.partner_id.id}
        }

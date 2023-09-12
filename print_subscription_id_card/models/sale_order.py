# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    """Inherit sale order model for add a button to print
    subscription id card"""
    _inherit = 'sale.order'

    def action_subscription_id_card(self):
        """For printing subscription id card"""
        products = [order.product_id.name for order in self.order_line]
        data = {
            'name': self.partner_id.name,
            'start_date': self.date_order.date(),
            'partner_id': self.partner_id.id,
            'end_date': self.end_date,
            'products': products,
        }
        action = self.env.ref('print_subscription_id_card'
        '.action_report_subscription_card').report_action(
            None, data=data)
        action.update({'close_on_report_download': True})
        return action

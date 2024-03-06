# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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


class SaleOrder(models.Model):
    """Class for inherit sale order"""
    _inherit = 'sale.order'

    return_order_count = fields.Integer(compute="_compute_returns",
                                        string='Return Orders',
                                        help='Count of return order')

    def _compute_returns(self):
        """Method to compute return count"""
        sale_return_groups = self.env['sale.return'].sudo().read_group(
            domain=[('sale_order', '=', self.ids)],
            fields=['sale_order'], groupby=['sale_order'])
        orders = self.browse()
        for group in sale_return_groups:
            sale_order = self.browse(group['sale_order'][0])
            while sale_order:
                if sale_order in self:
                    sale_order.return_order_count += group['sale_order_count']
                    orders |= sale_order
                    sale_order = False
        (self - orders).return_order_count = 0

    def action_open_returns(self):
        """This function returns an action that displays the sale return orders from sale order"""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_return_management.action_sale_return')
        domain = [('sale_order', '=', self.id)]
        action['domain'] = domain
        action['context'] = {'search_default_order': 1}
        return action

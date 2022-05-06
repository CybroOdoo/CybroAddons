# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
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
###################################################################################


from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    return_order_count = fields.Integer(compute="_compute_retuns", string='Return Orders')

    def _compute_retuns(self):
        """method to compute return count"""
        sale_return_groups = self.env['sale.return'].sudo().read_group(
            domain=[('sale_order', '=', self.ids)],
            fields=['sale_order'], groupby=['sale_order'])
        orders = self.sudo().browse()
        for group in sale_return_groups:
            sale_order = self.sudo().browse(group['sale_order'][0])
            while sale_order:
                if sale_order in self:
                    sale_order.return_order_count += group['sale_order_count']
                    orders |= sale_order
                    sale_order = False
        (self - orders).return_order_count = 0

    def action_open_returns(self):
        """This function returns an action that displays the sale return orders from sale order"""
        action = self.env['ir.actions.act_window']._for_xml_id('website_multi_product_return_management.sale_return_action')
        domain = [('sale_order', '=', self.id)]
        action['domain'] = domain
        action['context'] = {'search_default_order': 1}
        return action

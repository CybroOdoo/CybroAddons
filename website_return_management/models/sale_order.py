# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
        counts = dict(self.env['sale.return'].sudo()._read_group(
            [('sale_order_id', 'in', self.ids)],
            groupby=['sale_order_id'], aggregates=['__count']))
        for order in self:
            order.return_order_count = counts.get(order, 0)

    def action_open_returns(self):
        """This function returns an action that displays the sale return orders from sale order"""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_return_management.action_sale_return')
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {'default_sale_order_id': self.id}
        return action

    def _get_return_source_pickings(self):
        """Outgoing deliveries of the order that a return can be made from"""
        return self.picking_ids.filtered(
            lambda picking: picking.picking_type_code == 'outgoing')
